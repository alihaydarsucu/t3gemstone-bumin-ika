"""frontier_detection mantik testleri."""

import pytest

from gemstone_frontier_explorer.frontier_detection import (
    FrontierDetector,
    FrontierDetectorParams,
)
from gemstone_frontier_explorer.occupancy_grid_2d import OccupancyGrid2D

FREE = 0
OCC = 100
UNKNOWN = -1


def make_grid(width=20, height=20, res=0.1, origin=(0.0, 0.0),
              data=None):
    if data is None:
        data = [UNKNOWN] * (width * height)
    return OccupancyGrid2D(width, height, res, origin[0], origin[1], data)


def fill(grid, cells, value=FREE):
    for cx, cy in cells:
        grid.data[grid.index_of(cx, cy)] = value


def room_with_door():
    """20x20 grid: dogu yuzeyi UNKNOWN'a acilan kapili bos bir oda.

    Disarisi UNKNOWN; oda duvari OCC; icerideki BOS bolge kapidan dis
    UNKNOWN'a bakar. Frontier hucreleri kapinin hemen icinde olusur.
    """
    grid = make_grid()
    # oda duvari (dikdortgen halka)
    fill(grid, [(5, cy) for cy in range(5, 15)], OCC)
    fill(grid, [(14, cy) for cy in range(5, 15)], OCC)
    fill(grid, [(cx, 5) for cx in range(5, 15)], OCC)
    fill(grid, [(cx, 14) for cx in range(5, 15)], OCC)
    # oda ici bos
    fill(grid, [(cx, cy) for cx in range(6, 14) for cy in range(6, 14)])
    # kapi: dogu duvarinda y=8..11 (x=14 FREE, 4 hucre genisliginde)
    fill(grid, [(14, cy) for cy in range(8, 12)])
    return grid


class TestRobotSeed:
    def test_robot_on_free_cell(self):
        grid = room_with_door()
        det = FrontierDetector(FrontierDetectorParams())
        seed = det._robot_seed_cell(grid, (0.65, 0.95))
        assert seed == (6, 9)  # world (0.65,0.95) -> hucre (6,9)

    def test_robot_snap_to_nearest_free(self):
        grid = make_grid()
        grid.data[grid.index_of(10, 10)] = FREE
        det = FrontierDetector(FrontierDetectorParams())
        seed = det._robot_seed_cell(grid, (1.05, 1.05))
        assert seed == (10, 10)

    def test_no_free_cell_anywhere(self):
        grid = make_grid()
        det = FrontierDetector(FrontierDetectorParams(
            robot_snap_radius_m=5.0))
        assert det._robot_seed_cell(grid, (0.5, 0.5)) is None


class TestFrontierDetection:
    def test_detects_door_frontier(self):
        grid = room_with_door()
        det = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=3, border_margin_cells=0,
            obstacle_clearance_cells=0))
        clusters = det.detect(grid, (0.45, 0.95))
        assert len(clusters) >= 1
        # en buyuk kume kapi bolgesinde olmali
        biggest = clusters[0]
        assert biggest.centroid_x > 1.0  # doguya dogru

    def test_sorted_by_size_desc(self):
        grid = room_with_door()
        det = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=2, border_margin_cells=0,
            obstacle_clearance_cells=0))
        clusters = det.detect(grid, (0.45, 0.95))
        sizes = [c.size_cells for c in clusters]
        assert sizes == sorted(sizes, reverse=True)

    def test_fully_known_map_no_frontier(self):
        grid = make_grid()
        fill(grid, [(cx, cy) for cx in range(20) for cy in range(20)], FREE)
        det = FrontierDetector(FrontierDetectorParams())
        assert det.detect(grid, (0.5, 0.5)) == []

    def test_occupied_blocks_bfs(self):
        # robot'un etrafi duvarla cevrili: BFS disari cikamaz
        grid = make_grid()
        fill(grid, [(cx, cy) for cx in range(3, 17) for cy in range(3, 17)],
             FREE)
        # 4,4 - 16,16 alanini cevreleyen duvar haric bos dis
        fill(grid, [(3, cy) for cy in range(3, 17)], OCC)
        fill(grid, [(16, cy) for cy in range(3, 17)], OCC)
        fill(grid, [(cx, 3) for cx in range(3, 17)], OCC)
        fill(grid, [(cx, 16) for cx in range(3, 17)], OCC)
        det = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=2, border_margin_cells=0))
        # robot icerde; BFS duvara takilir, dis frontier'lara ulasamaz
        clusters = det.detect(grid, (0.5, 0.5))
        assert clusters == []

    def test_unknown_bridge_connects_pocket(self):
        # BOS bolge, tek hucre kalinliginda UNKNOWN kolonla ikiye bolunmus.
        # Kopru olmadan BFS sol cebe hapsolur; kopru ile sag bolgeye ulasir.
        grid = make_grid()
        # BOS cep: sol (0..5 x, 0..19 y)
        fill(grid, [(cx, cy) for cx in range(6) for cy in range(20)])
        # UNKNOWN bariyer: x=6 kolonu (tek hucre)
        fill(grid, [(6, cy) for cy in range(20)], UNKNOWN)
        # dis BOS bolge: sag (7..19 x, 0..19 y)
        fill(grid, [(cx, cy) for cx in range(7, 20) for cy in range(20)])

        det0 = FrontierDetector(FrontierDetectorParams(
            unknown_bridge_cells=0, cluster_min_cells=2,
            border_margin_cells=0))
        clusters0 = det0.detect(grid, (0.5, 0.5))
        det1 = FrontierDetector(FrontierDetectorParams(
            unknown_bridge_cells=1, cluster_min_cells=2,
            border_margin_cells=0))
        clusters1 = det1.detect(grid, (0.5, 0.5))

        assert clusters0 != []
        # kopru varken BFS bariyeri asip sag bolgeye ulasir: daha doguda
        # bir frontier gorunur.
        assert clusters1 != []
        max0 = max(c.centroid_x for c in clusters0)
        max1 = max(c.centroid_x for c in clusters1)
        assert max1 > max0

    def test_bounds_filter(self):
        grid = room_with_door()
        det = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=2, border_margin_cells=0,
            bounds_enabled=True, bounds_min_x=0.0, bounds_max_x=0.8,
            bounds_min_y=0.0, bounds_max_y=0.8))
        clusters = det.detect(grid, (0.45, 0.95))
        for c in clusters:
            assert 0.0 <= c.centroid_x <= 0.8
            assert 0.0 <= c.centroid_y <= 0.8


class TestIsStillFrontier:
    def test_valid_frontier_returns_true(self):
        grid = room_with_door()
        det = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=3, border_margin_cells=0,
            obstacle_clearance_cells=0))
        clusters = det.detect(grid, (0.45, 0.95))
        assert clusters
        big = clusters[0]
        assert det.is_still_frontier(grid, big.centroid, 3, 2) is True

    def test_explored_frontier_returns_false(self):
        grid = room_with_door()
        det = FrontierDetector(FrontierDetectorParams(
            cluster_min_cells=3, border_margin_cells=0,
            obstacle_clearance_cells=0))
        clusters = det.detect(grid, (0.45, 0.95))
        big = clusters[0]
        # kapinin onunu doldur (kesfedildi)
        cx, cy = grid.world_to_cell(big.centroid_x, big.centroid_y)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if grid.in_bounds(cx + dx, cy + dy):
                    grid.data[grid.index_of(cx + dx, cy + dy)] = FREE
        assert det.is_still_frontier(grid, big.centroid, 3, 2) is False
