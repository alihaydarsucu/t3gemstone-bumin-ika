"""Wavefront Frontier Detection (Keidar & Kaminka 2014; MIGHTY ilhamli).

Bir "frontier hucresi", en az bir BILINMEYEN komsusu olan bilinen-BOS
hucresidir. Detektor, robot konumundan baslayan iki gecisli BFS calistirir:

  Gecis A - robot'tan erisilebilir bilinen-bos bolgeyi dolasan dis BFS.
             Frontier hucreleri yol uzerinde isaretlenir.
  Gecis B - frontier hucrelerini 8-bagliliklarla kumelere ayiran ic BFS.

Iki gecisli yapi yalnizca robot'a erisilebilir bilinen-bos bolgeyi ziyaret
ettigi icin maliyet dongu basina O(erisilebilir hucre) kadardir ve robot'tan
kopuk bolgeleri dogal olarak yok sayar.

`unknown_bridge_cells`: BFS'in iki bilinen-bos bolgeyi baglantili sayarken
art arda gecis yapabilecegi BILINMEYEN hucresi sayisi (0 = yalnizca bos,
metin WFD davranisi). Lidar gorevcilerin yakin alan kozuklugu nedeniyle
robot'un kendi bos cebi UNKNOWN ile cevrelenebilir; bir kac hucrelik kopru
bu dikişi kapatir. ENGEL hucreleri her zaman bloklar, bu yuzden duvarlardan
sizma olmaz ve koprulenen UNKNOWN hucreler hicbir zaman frontier tohumu
olarak isaretlenmez.

Bu modul saf mantiktir; ROS'a bagimliligi yoktur.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

from .occupancy_grid_2d import GridExtent, OccupancyGrid2D

# Cok buyuk deger (secilmemesi gereken durumlar icin)
_INF = float('inf')


@dataclass
class FrontierDetectorParams:
    cluster_min_cells: int = 6          # en az kume boyutu (hucre)
    border_margin_cells: int = 2        # tohumlardan N-hucrelik kenar halkasi
    obstacle_clearance_cells: int = 1   # engelden N hucre uzaklik (0=kapat)
    robot_snap_radius_m: float = 1.0    # robot BOS degilse spiral arama
    unknown_bridge_cells: int = 0       # art arda gecilebilir UNKNOWN sayisi
    bounds_enabled: bool = False
    bounds_min_x: float = 0.0
    bounds_max_x: float = 0.0
    bounds_min_y: float = 0.0
    bounds_max_y: float = 0.0

    def to_extent(self) -> GridExtent:
        return GridExtent(
            enabled=self.bounds_enabled,
            min_x=self.bounds_min_x,
            max_x=self.bounds_max_x,
            min_y=self.bounds_min_y,
            max_y=self.bounds_max_y,
        )


@dataclass
class FrontierCluster:
    centroid: tuple = (0.0, 0.0)        # dunya cercevesi (x, y)
    cells: List[tuple] = field(default_factory=list)  # dunya koor. hucresi
    size_cells: int = 0
    size_m2: float = 0.0
    aabb_min: tuple = (0.0, 0.0)
    aabb_max: tuple = (0.0, 0.0)
    # Kesif yoneticisinin (FrontierManager) hucre bazli revalidasyonu icin
    # tohum hucrelerin hucre koordinatlari (x_ind, y_ind) listesi.
    cell_indices: List[tuple] = field(default_factory=list)

    @property
    def centroid_x(self) -> float:
        return self.centroid[0]

    @property
    def centroid_y(self) -> float:
        return self.centroid[1]


class FrontierDetector:
    """Bir OccupancyGrid2D uzerinde frontier kumelerini bulan detektor."""

    def __init__(self, params: FrontierDetectorParams):
        self.params = params

    # ------------------------------------------------------------------
    # Ana API
    # ------------------------------------------------------------------
    def detect(self, grid: OccupancyGrid2D, robot_xy: tuple) -> List[FrontierCluster]:
        """WFD calistirir, robot konumundan tohumlanir.

        @return: buyukluk sirasina gore kuculen frontier kumeleri.
                 Robot konumu BOS hucresine yakalanamazsa veya frontier yoksa
                 bos liste.
        """
        seed = self._robot_seed_cell(grid, robot_xy)
        if seed is None:
            return []

        tagged = self._outer_bfs(grid, seed)
        clusters = self._cluster_8(grid, tagged)
        clusters.sort(key=lambda c: c.size_cells, reverse=True)
        return clusters

    def is_still_frontier(self, grid: OccupancyGrid2D, world_xy: tuple,
                          min_cells: int, search_radius_cells: int) -> bool:
        """Bir frontier kaydinin hala gecerli olup olmadigini dogrular.

        `world_xy` verilen konumun `search_radius_cells` hucresinin icinde,
        en az `min_cells` buyuklugunde ve BAGLI bir frontier-hucresi bileseni
        var mi diye bakar. Erkenden cikar, maliyet O(min_cells). Merkez kaybin
        EMA kaymasini sozumecek sekilde robot'un hala var oldugu bolgedeki
        frontier'i yanlis emekli etmez.
        """
        cx, cy = grid.world_to_cell(world_xy[0], world_xy[1])
        extent = self.params.to_extent()
        for sx, sy in grid.cells_in_square(cx, cy, search_radius_cells):
            if not grid.is_frontier_cell(
                    sx, sy,
                    border_margin=self.params.border_margin_cells,
                    obstacle_clearance=self.params.obstacle_clearance_cells,
                    extent=extent):
                continue
            # Bu frontier hucresinden 8-baglilikli bileseni topla
            if self._component_size(grid, sx, sy, extent) >= min_cells:
                return True
        return False

    # ------------------------------------------------------------------
    # Ic mekanizmalar
    # ------------------------------------------------------------------
    def _robot_seed_cell(self, grid: OccupancyGrid2D, robot_xy: tuple):
        """Robot konumunu BOS hucresine yakalar (spiral arama)."""
        cx, cy = grid.world_to_cell(robot_xy[0], robot_xy[1])
        if grid.is_free(cx, cy):
            return cx, cy
        max_radius = int(math.ceil(
            self.params.robot_snap_radius_m / grid.resolution))
        return grid.nearest_free_cell(cx, cy, max_radius)

    def _outer_bfs(self, grid: OccupancyGrid2D, seed: tuple) -> List[tuple]:
        """Gecis A: erisilebilir bilinen-bos bolgeyi BFS ile dolas.

        Frontier hucrelerini isaretleyen tag uretir. UNKNOWN kopruleme:
        `unknown_bridge_cells` > 0 ise, BOS bir hucreden baslayarak art arda
        en fazla o kadar UNKNOWN hucresinden gecilebilir; engel her zaman
        bloklar.
        """
        params = self.params
        extent = params.to_extent()
        # dist_from_free: BOS hucre 0, kopru UNKNOWN hucresinde kac tane
        # UNKNOWN art arda asilmis (>= bridge ise daha ileri gidilemez).
        dist_from_free: dict = {seed: 0}
        visited: set = {seed}
        queue = deque([seed])
        tagged = []

        while queue:
            cx, cy = queue.popleft()
            is_frontier = grid.is_frontier_cell(
                cx, cy,
                border_margin=params.border_margin_cells,
                obstacle_clearance=params.obstacle_clearance_cells,
                extent=extent)
            if is_frontier:
                tagged.append((cx, cy))

            for nx, ny in grid.neighbors_4(cx, cy):
                if (nx, ny) in visited:
                    continue
                if grid.is_free(nx, ny):
                    visited.add((nx, ny))
                    dist_from_free[(nx, ny)] = 0
                    queue.append((nx, ny))
                elif grid.is_unknown(nx, ny):
                    parent_dist = dist_from_free[(cx, cy)]
                    if parent_dist < params.unknown_bridge_cells:
                        visited.add((nx, ny))
                        dist_from_free[(nx, ny)] = parent_dist + 1
                        queue.append((nx, ny))
                # engel: atlanir

        return tagged

    def _cluster_8(self, grid: OccupancyGrid2D,
                   tagged: List[tuple]) -> List[FrontierCluster]:
        """Gecis B: frontier hucrelerini 8-bagliliklarla kumele."""
        if not tagged:
            return []
        unassigned = set(tagged)
        clusters: List[FrontierCluster] = []
        res = grid.resolution

        for seed_cell in tagged:
            if seed_cell not in unassigned:
                continue
            comp = []
            queue = deque([seed_cell])
            unassigned.discard(seed_cell)
            while queue:
                cx, cy = queue.popleft()
                comp.append((cx, cy))
                for nx, ny in grid.neighbors_8(cx, cy):
                    if (nx, ny) in unassigned:
                        unassigned.discard((nx, ny))
                        queue.append((nx, ny))

            if len(comp) < self.params.cluster_min_cells:
                continue
            clusters.append(self._make_cluster(grid, comp, res))

        return clusters

    def _component_size(self, grid: OccupancyGrid2D, sx: int, sy: int,
                        extent: GridExtent) -> int:
        """(sx, sy)'den 8-baglilikli frontier bileseninin buyuklugunu topla."""
        params = self.params
        count = 0
        queue = deque([(sx, sy)])
        seen = {(sx, sy)}
        while queue:
            cx, cy = queue.popleft()
            count += 1
            for nx, ny in grid.neighbors_8(cx, cy):
                if (nx, ny) in seen:
                    continue
                if not grid.is_frontier_cell(
                        nx, ny,
                        border_margin=params.border_margin_cells,
                        obstacle_clearance=params.obstacle_clearance_cells,
                        extent=extent):
                    continue
                seen.add((nx, ny))
                queue.append((nx, ny))
        return count

    @staticmethod
    def _make_cluster(grid: OccupancyGrid2D, comp: List[tuple],
                      res: float) -> FrontierCluster:
        world = [grid.cell_to_world(cx, cy) for cx, cy in comp]
        sum_x = sum(p[0] for p in world)
        sum_y = sum(p[1] for p in world)
        n = len(comp)
        centroid = (sum_x / n, sum_y / n)
        xs = [p[0] for p in world]
        ys = [p[1] for p in world]
        return FrontierCluster(
            centroid=centroid,
            cells=world,
            size_cells=n,
            size_m2=n * res * res,
            aabb_min=(min(xs), min(ys)),
            aabb_max=(max(xs), max(ys)),
            cell_indices=list(comp),
        )
