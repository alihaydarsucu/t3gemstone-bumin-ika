"""LiDAR tabanli demo gezinti davranisi icin saf yardimci fonksiyonlar."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class LaserSector:
    center_angle_rad: float
    min_distance_m: float
    start_index: int
    end_index: int


@dataclass(frozen=True)
class ExplorationGoal:
    x: float | None
    y: float | None
    heading_rad: float
    distance_m: float
    selected_sector: LaserSector
    mode: str


def wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def angular_error(target_angle: float, current_angle: float) -> float:
    return wrap_angle(target_angle - current_angle)


def quaternion_to_yaw(quaternion) -> float:
    x = quaternion.x
    y = quaternion.y
    z = quaternion.z
    w = quaternion.w
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def scan_to_sectors(
    ranges,
    angle_min: float,
    angle_increment: float,
    range_min: float,
    range_max: float,
    sector_width_rad: float,
) -> list[LaserSector]:
    if sector_width_rad <= 0.0:
        raise ValueError('sector_width_rad pozitif olmali')
    if angle_increment <= 0.0:
        raise ValueError('angle_increment pozitif olmali')

    samples_per_sector = max(1, int(round(sector_width_rad / angle_increment)))
    sectors: list[LaserSector] = []

    for start in range(0, len(ranges), samples_per_sector):
        end = min(len(ranges), start + samples_per_sector)
        valid = [
            value for value in ranges[start:end]
            if math.isfinite(value) and range_min <= value <= range_max
        ]
        if not valid:
            continue

        center_index = start + ((end - start - 1) / 2.0)
        center_angle = angle_min + center_index * angle_increment
        sectors.append(LaserSector(
            center_angle_rad=wrap_angle(center_angle),
            min_distance_m=min(valid),
            start_index=start,
            end_index=end,
        ))

    return sectors


def filter_free_sectors(
    sectors: list[LaserSector],
    min_clearance_m: float,
) -> list[LaserSector]:
    return [sector for sector in sectors if sector.min_distance_m >= min_clearance_m]


def choose_sector(
    sectors: list[LaserSector],
    rng: random.Random,
    forward_bias: float = 0.35,
) -> LaserSector | None:
    if not sectors:
        return None

    weights = []
    for sector in sectors:
        forward_factor = 1.0 + max(0.0, math.cos(sector.center_angle_rad)) * forward_bias
        weights.append(max(0.1, sector.min_distance_m) * forward_factor)
    return rng.choices(sectors, weights=weights, k=1)[0]


def sector_to_goal(
    pose_x: float,
    pose_y: float,
    pose_yaw: float,
    sector: LaserSector,
    target_distance_scale: float,
    min_goal_distance_m: float,
    max_goal_distance_m: float,
) -> ExplorationGoal:
    if target_distance_scale <= 0.0:
        raise ValueError('target_distance_scale pozitif olmali')
    if min_goal_distance_m <= 0.0:
        raise ValueError('min_goal_distance_m pozitif olmali')
    if max_goal_distance_m < min_goal_distance_m:
        raise ValueError('max_goal_distance_m min_goal_distance_m kadar buyuk olmali')

    goal_distance = sector.min_distance_m * target_distance_scale
    goal_distance = max(min_goal_distance_m, min(max_goal_distance_m, goal_distance))
    heading = wrap_angle(pose_yaw + sector.center_angle_rad)
    goal_x = pose_x + goal_distance * math.cos(heading)
    goal_y = pose_y + goal_distance * math.sin(heading)
    return ExplorationGoal(
        x=goal_x,
        y=goal_y,
        heading_rad=heading,
        distance_m=goal_distance,
        selected_sector=sector,
        mode='odom',
    )


def heading_only_goal(
    pose_yaw: float,
    sector: LaserSector,
    target_distance_scale: float,
    min_goal_distance_m: float,
    max_goal_distance_m: float,
) -> ExplorationGoal:
    goal_distance = sector.min_distance_m * target_distance_scale
    goal_distance = max(min_goal_distance_m, min(max_goal_distance_m, goal_distance))
    heading = wrap_angle(pose_yaw + sector.center_angle_rad)
    return ExplorationGoal(
        x=None,
        y=None,
        heading_rad=heading,
        distance_m=goal_distance,
        selected_sector=sector,
        mode='heading_only',
    )


def distance_to_goal(pose_x: float, pose_y: float, goal_x: float, goal_y: float) -> float:
    return math.hypot(goal_x - pose_x, goal_y - pose_y)


def bearing_to_goal(pose_x: float, pose_y: float, goal_x: float, goal_y: float) -> float:
    return math.atan2(goal_y - pose_y, goal_x - pose_x)
