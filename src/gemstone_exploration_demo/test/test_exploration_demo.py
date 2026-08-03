import math
import random

import pytest

from gemstone_exploration_demo.exploration_demo import (
    choose_sector,
    filter_free_sectors,
    heading_only_goal,
    scan_to_sectors,
    sector_to_goal,
)


def test_scan_to_sectors_groups_samples():
    ranges = [0.5, 1.0, 2.0, 3.0, 0.2, 4.0]
    sectors = scan_to_sectors(
        ranges=ranges,
        angle_min=math.radians(-30),
        angle_increment=math.radians(10),
        range_min=0.1,
        range_max=10.0,
        sector_width_rad=math.radians(20),
    )
    assert len(sectors) == 3
    assert sectors[0].min_distance_m == pytest.approx(0.5)
    assert sectors[1].min_distance_m == pytest.approx(2.0)
    assert sectors[2].min_distance_m == pytest.approx(0.2)


def test_filter_free_sectors_removes_close_entries():
    sectors = scan_to_sectors(
        ranges=[0.5, 2.0, 3.0, 1.5],
        angle_min=0.0,
        angle_increment=math.radians(10),
        range_min=0.1,
        range_max=10.0,
        sector_width_rad=math.radians(20),
    )
    free = filter_free_sectors(sectors, min_clearance_m=1.6)
    assert len(free) == 1
    assert free[0].min_distance_m == pytest.approx(2.0)


def test_choose_sector_prefers_random_but_deterministic_seed():
    sectors = scan_to_sectors(
        ranges=[1.0, 2.0, 3.0, 4.0],
        angle_min=0.0,
        angle_increment=math.radians(10),
        range_min=0.1,
        range_max=10.0,
        sector_width_rad=math.radians(10),
    )
    choice = choose_sector(sectors, random.Random(42))
    assert choice is not None
    assert choice.min_distance_m == pytest.approx(4.0)


def test_sector_to_goal_projects_forward():
    sector = scan_to_sectors(
        ranges=[4.0, 4.0],
        angle_min=0.0,
        angle_increment=math.radians(10),
        range_min=0.1,
        range_max=10.0,
        sector_width_rad=math.radians(10),
    )[0]
    goal = sector_to_goal(
        pose_x=1.0,
        pose_y=2.0,
        pose_yaw=0.0,
        sector=sector,
        target_distance_scale=0.5,
        min_goal_distance_m=0.8,
        max_goal_distance_m=2.5,
    )
    assert goal.x > 1.0
    assert goal.y == pytest.approx(2.0)
    assert goal.distance_m == pytest.approx(0.8)


def test_heading_only_goal_uses_heading_without_pose_target():
    sector = scan_to_sectors(
        ranges=[2.0, 2.0],
        angle_min=0.0,
        angle_increment=math.radians(10),
        range_min=0.1,
        range_max=10.0,
        sector_width_rad=math.radians(10),
    )[0]
    goal = heading_only_goal(
        pose_yaw=0.0,
        sector=sector,
        target_distance_scale=0.5,
        min_goal_distance_m=0.8,
        max_goal_distance_m=2.5,
    )
    assert goal.x is None
    assert goal.y is None
    assert goal.distance_m == pytest.approx(0.8)
