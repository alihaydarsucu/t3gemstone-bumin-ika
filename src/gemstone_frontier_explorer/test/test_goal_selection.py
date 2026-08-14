"""coverage ve goal_selection mantik testleri."""

from gemstone_frontier_explorer.coverage import compute_coverage
from gemstone_frontier_explorer.frontier_detection import (
    FrontierCluster,
)
from gemstone_frontier_explorer.frontier_manager import (
    FrontierManager,
    FrontierManagerParams,
)
from gemstone_frontier_explorer.goal_selection import (
    goal_pose_for_point,
    select_goal,
    select_goal_with_commit,
)
from gemstone_frontier_explorer.occupancy_grid_2d import (
    GridExtent,
    OccupancyGrid2D,
)

FREE = 0
OCC = 100
UNKNOWN = -1


def make_grid(width=10, height=10, res=0.1, data=None):
    if data is None:
        data = [UNKNOWN] * (width * height)
    return OccupancyGrid2D(width, height, res, 0.0, 0.0, data)


class TestCoverage:
    def test_unknown_only_is_zero(self):
        grid = make_grid()
        result = compute_coverage(grid)
        assert result.ratio == 0.0
        assert result.known_cells == 0

    def test_all_known_is_one(self):
        grid = make_grid()
        grid.data = [FREE] * 100
        result = compute_coverage(grid)
        assert result.ratio == 1.0
        assert result.known_cells == 100

    def test_half_known(self):
        grid = make_grid()
        for i in range(50):
            grid.data[i] = FREE
        result = compute_coverage(grid)
        assert abs(result.ratio - 0.5) < 1e-9

    def test_bounded_coverage(self):
        grid = make_grid(data=[UNKNOWN] * 100)
        for i in range(100):
            grid.data[i] = FREE
        extent = GridExtent(
            enabled=True, min_x=0.0, max_x=0.5, min_y=0.0, max_y=1.0)
        result = compute_coverage(grid, extent)
        # 0..0.5 x, 0..1.0 y -> 5 hucre genislik * 10 yukseklik = 50
        assert result.total_cells == 50
        assert result.ratio == 1.0


def _cluster(cx, cy, size=5):
    return FrontierCluster(
        centroid=(cx, cy),
        cells=[(cx, cy + i) for i in range(size)],
        size_cells=size,
        size_m2=size * 0.01,
        aabb_min=(cx, cy),
        aabb_max=(cx, cy + 0.5),
    )


class TestGoalSelection:
    def test_select_returns_best(self):
        mgr = FrontierManager(FrontierManagerParams())
        mgr.update([_cluster(1.0, 1.0), _cluster(3.0, 3.0)],
                   (0.0, 0.0), 0.0)
        goal = select_goal(mgr.active(), (0.0, 0.0), mgr.params)
        assert goal is not None

    def test_commit_keeps_current_goal(self):
        params = FrontierManagerParams()
        mgr = FrontierManager(params)
        mgr.update([_cluster(1.0, 1.0), _cluster(3.0, 3.0)],
                   (0.0, 0.0), 0.0)
        current = mgr.records()[0]  # id 0, (1,1)
        goal = select_goal_with_commit(
            mgr.active(), (0.0, 0.0), params, current, margin=1.0)
        assert goal.id == current.id

    def test_commit_switches_when_margin_exceeded(self):
        params = FrontierManagerParams(w_dist=2.0, w_size=0.0)
        mgr = FrontierManager(params)
        mgr.update([_cluster(1.0, 1.0), _cluster(3.0, 3.0)],
                   (0.0, 0.0), 0.0)
        current = mgr.find(1)  # uzaktaki (3,3), dusuk fayda
        goal = select_goal_with_commit(
            mgr.active(), (0.0, 0.0), params, current, margin=0.0)
        assert goal.id == 0

    def test_goal_pose_snaps_to_free(self):
        grid = make_grid()
        grid.data[grid.index_of(5, 5)] = FREE
        # merkez FREE; dogrudan
        pose = goal_pose_for_point(grid, (0.55, 0.55), 0.5)
        assert pose is not None
        assert abs(pose[0] - 0.55) < 1e-9
        # merkez UNKNOWN -> yakin FREE hucresine yakalanir
        grid.data[grid.index_of(4, 5)] = FREE
        grid.data[grid.index_of(5, 5)] = UNKNOWN
        pose = goal_pose_for_point(grid, (0.55, 0.55), 0.5)
        assert pose is not None
        cx, cy = grid.world_to_cell(pose[0], pose[1])
        assert grid.is_free(cx, cy)

    def test_goal_pose_none_when_no_free(self):
        grid = make_grid()
        assert goal_pose_for_point(grid, (0.55, 0.55), 0.3) is None
