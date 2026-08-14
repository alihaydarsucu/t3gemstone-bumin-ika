"""Occupancy grid 2D veri kabugu.

Saf mantik modulu: ROS'a bagimli DEGILDIR. `OccupancyGrid2D`, bir
nav_msgs/OccupancyGrid mesajinin icerigini (width, height, resolution,
origin, data) alir ve hucre/savas-duzlem donusumleri ile sorgular saglar.
ROS node'u bu sinifi mesaj verileriyle besler; testler ham sayilarla besler.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence

# OccupancyGrid veri degerleri
CELL_UNKNOWN = -1
CELL_FREE = 0


@dataclass
class GridExtent:
    """Kesif sinirlari (dunya cercevesinde, metre)."""

    enabled: bool = False
    min_x: float = 0.0
    max_x: float = 0.0
    min_y: float = 0.0
    max_y: float = 0.0

    def contains(self, x: float, y: float) -> bool:
        if not self.enabled:
            return True
        return (self.min_x <= x <= self.max_x and
                self.min_y <= y <= self.max_y)


class OccupancyGrid2D:
    """Hucre bazli erisim icin OccupancyGrid verisini saran sinif.

    `data` 1B liste/array (row-major, boyut width*height) bekler;
    -1 bilinmeyen, 0 bos, >0 engel olarak yorumlanir. Numpy zorunlu
    degildir (saf python ile de calisir) ama numpy varsa kullanilir.
    """

    def __init__(self, width: int, height: int, resolution: float,
                 origin_x: float, origin_y: float,
                 data: Sequence[int]):
        self.width = int(width)
        self.height = int(height)
        self.resolution = float(resolution)
        self.origin_x = float(origin_x)
        self.origin_y = float(origin_y)

        self.data = [int(v) for v in data]
        if len(self.data) != self.width * self.height:
            raise ValueError(
                'data uzunlugu width*height ile eslesmiyor: '
                f'{len(self.data)} != {self.width * self.height}')

    # ------------------------------------------------------------------
    # Koordinat donusumleri
    # ------------------------------------------------------------------
    def world_to_cell(self, x: float, y: float):
        """Dunya koor. -> hucre indisleri (x_ind, y_ind) (clamp edilmez)."""
        cx = int(math.floor((x - self.origin_x) / self.resolution))
        cy = int(math.floor((y - self.origin_y) / self.resolution))
        return cx, cy

    def cell_to_world(self, cx: int, cy: int) -> tuple:
        """Hucre merkezinin dunya koordinatlari."""
        x = self.origin_x + (cx + 0.5) * self.resolution
        y = self.origin_y + (cy + 0.5) * self.resolution
        return x, y

    def cell_to_world_x(self, cx: int) -> float:
        return self.origin_x + (cx + 0.5) * self.resolution

    def cell_to_world_y(self, cy: int) -> float:
        return self.origin_y + (cy + 0.5) * self.resolution

    # ------------------------------------------------------------------
    # Erisim / sorgular
    # ------------------------------------------------------------------
    def index_of(self, cx: int, cy: int) -> int:
        return cy * self.width + cx

    def in_bounds(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.width and 0 <= cy < self.height

    def value_at(self, cx: int, cy: int):
        """Hucre degeri: -1 bilinmeyen, 0 bos, >0 engel agirligi."""
        if not self.in_bounds(cx, cy):
            return None
        return self.data[self.index_of(cx, cy)]

    def is_free(self, cx: int, cy: int) -> bool:
        v = self.value_at(cx, cy)
        return v is not None and v == CELL_FREE

    def is_unknown(self, cx: int, cy: int) -> bool:
        v = self.value_at(cx, cy)
        return v is not None and v == CELL_UNKNOWN

    def is_occupied(self, cx: int, cy: int) -> bool:
        v = self.value_at(cx, cy)
        return v is not None and v > CELL_FREE

    def known(self, cx: int, cy: int) -> bool:
        v = self.value_at(cx, cy)
        return v is not None and v != CELL_UNKNOWN

    def is_frontier_cell(self, cx: int, cy: int,
                         border_margin: int = 0,
                         obstacle_clearance: int = 0,
                         extent: GridExtent | None = None) -> bool:
        """Frontier hucresi: bilinen-BOS hucre, en az bir BILINMEYEN komsusu
        var, engelden `obstacle_clearance` hucre uzakta ve istege bagli kesif
        sinirlari icinde."""
        if not self.in_bounds(cx, cy):
            return False
        if not self.is_free(cx, cy):
            return False
        if border_margin > 0:
            if cx < border_margin or cx >= self.width - border_margin:
                return False
            if cy < border_margin or cy >= self.height - border_margin:
                return False
        if extent is not None and extent.enabled:
            wx, wy = self.cell_to_world(cx, cy)
            if not extent.contains(wx, wy):
                return False
        # en az bir bilinmeyen komsu (8-komsuluk)
        has_unknown = False
        for dcx in (-1, 0, 1):
            for dcy in (-1, 0, 1):
                if dcx == 0 and dcy == 0:
                    continue
                nx, ny = cx + dcx, cy + dcy
                if self.in_bounds(nx, ny) and self.is_unknown(nx, ny):
                    has_unknown = True
                    break
            if has_unknown:
                break
        if not has_unknown:
            return False
        if obstacle_clearance > 0:
            # Chebyshev mesafesi <= clearance icindeki herhangi bir engel
            # hucresi varsa bu hucre elenir (duvara yapisan frontierlar).
            for dcx in range(-obstacle_clearance, obstacle_clearance + 1):
                for dcy in range(-obstacle_clearance, obstacle_clearance + 1):
                    if dcx == 0 and dcy == 0:
                        continue
                    nx, ny = cx + dcx, cy + dcy
                    if self.in_bounds(nx, ny) and self.is_occupied(nx, ny):
                        return False
        return True

    # ------------------------------------------------------------------
    # Genel yardimcilar
    # ------------------------------------------------------------------
    def neighbors_4(self, cx: int, cy: int):
        for dcx, dcy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dcx, cy + dcy
            if self.in_bounds(nx, ny):
                yield nx, ny

    def neighbors_8(self, cx: int, cy: int):
        for dcx in (-1, 0, 1):
            for dcy in (-1, 0, 1):
                if dcx == 0 and dcy == 0:
                    continue
                nx, ny = cx + dcx, cy + dcy
                if self.in_bounds(nx, ny):
                    yield nx, ny

    def cells_in_square(self, center_cx: int, center_cy: int, radius: int):
        """Chebyshev mesafesi `radius`'dan kucuk/esit hucreleri dondurur."""
        for dcx in range(-radius, radius + 1):
            for dcy in range(-radius, radius + 1):
                nx, ny = center_cx + dcx, center_cy + dcy
                if self.in_bounds(nx, ny):
                    yield nx, ny

    def nearest_free_cell(self, cx: int, cy: int, max_radius: int):
        """Verilen hucreye (spiral arama) en yakin BOS hucreyi bulur.
        Bulunamazsa None dondurur."""
        for r in range(max_radius + 1):
            for nx, ny in self.cells_in_square(cx, cy, r):
                if self.is_free(nx, ny):
                    return nx, ny
        return None

    @staticmethod
    def world_to_cell_list(world_points, grid):
        """Hucre koordinatlarinin dunya koor. listesini verir (karar)."""
        raise NotImplementedError  # pragma: no cover
