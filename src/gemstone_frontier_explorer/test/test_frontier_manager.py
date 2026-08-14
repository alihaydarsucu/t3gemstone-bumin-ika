"""frontier_manager mantik testleri."""

import pytest

from gemstone_frontier_explorer.frontier_detection import (
    FrontierCluster,
)
from gemstone_frontier_explorer.frontier_manager import (
    FrontierManager,
    FrontierManagerParams,
    FrontierState,
)

FREE = 0
OCC = 100
UNKNOWN = -1


def cluster(cx, cy, size=10, res=0.1):
    cells = [(cx, cy + i) for i in range(size)]
    world = [(cx, cy + i) for i in range(size)]
    return FrontierCluster(
        centroid=(cx, cy),
        cells=world,
        size_cells=size,
        size_m2=size * res * res,
        aabb_min=(cx, cy),
        aabb_max=(cx + size * res, cy + size * res),
    )


class TestUpdateMatching:
    def test_insert_new(self):
        mgr = FrontierManager(FrontierManagerParams())
        mgr.update([cluster(1.0, 1.0)], (0.0, 0.0), 1.0)
        assert mgr.size() == 1
        rec = mgr.records()[0]
        assert rec.state == FrontierState.ACTIVE
        assert rec.id == 0

    def test_merge_matches_existing(self):
        mgr = FrontierManager(FrontierManagerParams())
        mgr.update([cluster(1.0, 1.0)], (0.0, 0.0), 1.0)
        # merkez hafif kaysa da ayni kayda eslenmeli (EMA)
        mgr.update([cluster(1.4, 1.4)], (0.0, 0.0), 2.0)
        assert mgr.size() == 1
        rec = mgr.records()[0]
        assert abs(rec.centroid_x - 1.2) < 1e-6  # EMA(0.5) ortalamasi

    def test_disappeared_gets_invalidated(self):
        mgr = FrontierManager(FrontierManagerParams())
        mgr.update([cluster(1.0, 1.0)], (0.0, 0.0), 1.0)
        mgr.update([], (0.0, 0.0), 2.0)
        assert mgr.records()[0].state == FrontierState.INVALIDATED

    def test_respawn_reactivates(self):
        mgr = FrontierManager(FrontierManagerParams())
        mgr.update([cluster(1.0, 1.0)], (0.0, 0.0), 1.0)
        mgr.update([], (0.0, 0.0), 2.0)
        assert mgr.records()[0].state == FrontierState.INVALIDATED
        mgr.update([cluster(1.0, 1.0)], (0.0, 0.0), 3.0)
        assert mgr.records()[0].state == FrontierState.ACTIVE


class TestDwellVisit:
    def test_dwell_visits_frontier(self):
        params = FrontierManagerParams(
            visit_radius_m=0.5, visit_dwell_sec=1.0)
        mgr = FrontierManager(params)
        mgr.update([cluster(0.1, 0.1)], (0.0, 0.0), 0.0)
        assert mgr.records()[0].state == FrontierState.ACTIVE
        mgr.update([cluster(0.1, 0.1)], (0.05, 0.05), 0.5)
        assert mgr.records()[0].state == FrontierState.ACTIVE
        mgr.update([cluster(0.1, 0.1)], (0.05, 0.05), 1.1)
        assert mgr.records()[0].state == FrontierState.VISITED

    def test_far_robot_never_visits(self):
        params = FrontierManagerParams(
            visit_radius_m=0.5, visit_dwell_sec=1.0)
        mgr = FrontierManager(params)
        mgr.update([cluster(5.0, 5.0)], (0.0, 0.0), 0.0)
        mgr.update([cluster(5.0, 5.0)], (0.0, 0.0), 60.0)
        assert mgr.records()[0].state == FrontierState.ACTIVE


class TestSelection:
    def test_select_skips_non_active(self):
        params = FrontierManagerParams()
        mgr = FrontierManager(params)
        mgr.update([cluster(1.0, 1.0)], (0.0, 0.0), 1.0)
        mgr.mark_visited(0)
        assert mgr.active() == []

    def test_nearest_preferred(self):
        params = FrontierManagerParams(w_dist=2.0, w_size=0.0)
        mgr = FrontierManager(params)
        mgr.update([cluster(10.0, 10.0), cluster(2.0, 2.0)],
                   (0.0, 0.0), 1.0)
        from gemstone_frontier_explorer.goal_selection import select_goal
        goal = select_goal(mgr.active(), (0.0, 0.0), params)
        assert goal is not None
        # mesafe agirligi 2.0, boyut 0 -> en yakin secilir
        assert goal.id == 1

    def test_pursuit_timeout_invalidates(self):
        import math
        params = FrontierManagerParams(pursuit_timeout_min_sec=2.0)
        mgr = FrontierManager(params)
        mgr.update([cluster(2.0, 2.0)], (0.0, 0.0), 1.0)
        rec = mgr.records()[0]
        mgr.mark_selected(rec.id, (0.0, 0.0), 1.0)
        # deadline = 1 + max(2, dist/0.5*10); dist=sqrt(8)
        expected = 1.0 + (math.sqrt(8.0) / 0.5 * 10.0)
        assert rec.pursuit_deadline_t == pytest.approx(expected)
        mgr.update([cluster(2.0, 2.0)], (0.0, 0.0), 60.0)
        assert mgr.records()[0].state == FrontierState.INVALIDATED
