"""Kesif hedefi secimi ve hedef nokta hesabi.

Iki katmanli politika:
  1. Utility siralamasi (FrontierManager) — boyut, mesafe, tekrar-ziyaret
     odullu eklemeli fayda fonksiyonu.
  2. Commit margin — halihazirda kesilen bir hedef varsa, yeni aday ancak
     ondan "commit_margin" kadar daha iyiyse hedef degistirilir. Bu,
     merkez EMA kaymasi veya tarama gurultusu yuzunden surekli hedef
     sallanmasini (thrash) onler.

Hedef noktasi: cluster merkezi BOS degilse (bilinmeyen/engel) en yakin BOS
hucresine yakalanir; yaw harita cercevesinde 0'dir (Nav2 goal checker'in
yaw toleransi burayi esnek birakir).

Saf mantik modulu; ROS bagimliligi yoktur.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .frontier_detection import FrontierCluster
from .frontier_manager import FrontierManager, FrontierManagerParams, FrontierRecord, FrontierState
from .occupancy_grid_2d import OccupancyGrid2D


def compute_utility(rec: FrontierRecord, robot_xy: tuple,
                    params: FrontierManagerParams) -> float:
    """Eklemeli fayda: boyut odulu + bilgi odulu - mesafe cezasi.

    Normalizasyon boyutlarindan buyuk degerler doygunluga ulasir; agirliklar
    parametrelerde belirlenir. Daha yuksek = daha iyi.
    """
    size_norm = min(1.0, rec.size_m2 / params.size_ref_m2)
    dist = rec.dist_to(robot_xy)
    dist_norm = min(1.0, dist / params.dist_ref_m)
    utility = (params.w_size * size_norm
               - params.w_dist * dist_norm)
    # istege bagli tekrar ziyaret cezasi (VISITED'e dusen kayitlar zaten
    # secilmez; bu agirlik ileride "tekrar ziyaret" politikasi icin ayrilir)
    return utility


def select_goal(frontiers: List[FrontierRecord], robot_xy: tuple,
                params: FrontierManagerParams) -> Optional[FrontierRecord]:
    """ACTIVE kayitlar arasindan en yuksek faydali hedefi secer.

    Esik altinda kalani yoksa None. Pursuit siniri dolmus kayitlar secilmez.
    """
    best = None
    best_u = params.goal_select_threshold
    for rec in frontiers:
        if rec.state != FrontierState.ACTIVE:
            continue
        if rec.pursuit_deadline_t > 0:
            continue  # zaten pesinde / sinir bitmis; yonetici handle eder
        u = compute_utility(rec, robot_xy, params)
        if u > best_u:
            best_u = u
            best = rec
    return best


def select_goal_with_commit(frontiers: List[FrontierRecord], robot_xy: tuple,
                            params: FrontierManagerParams,
                            current: Optional[FrontierRecord],
                            margin: float) -> Optional[FrontierRecord]:
    """Commit margin'li hedef secimi.

    `current` hala secilebilir (ACTIVE, sinir dolmamis) ise ve yeni aday
    faydasi current'tan `margin`'den az fazlaysa current korunur.
    """
    if current is not None and current.state == FrontierState.ACTIVE:
        if current.pursuit_deadline_t > 0:
            # sinir doldu: yeni hedef sec
            current = None
    candidate = select_goal(frontiers, robot_xy, params)
    if candidate is None:
        return current if (current is not None and
                           current.state == FrontierState.ACTIVE) else None
    if current is not None and current.state == FrontierState.ACTIVE:
        cur_u = compute_utility(current, robot_xy, params)
        cand_u = compute_utility(candidate, robot_xy, params)
        if cand_u - cur_u < margin:
            return current
    return candidate


def goal_pose_for_point(grid: OccupancyGrid2D, world_xy: tuple,
                        snap_radius_m: float = 0.5,
                        yaw: float = 0.0) -> Optional[tuple]:
    """Verilen dunya noktasi icin BOS bir hedef noktasi uretir.

    Noktanin hucresi BOS degilse `snap_radius_m` yaricapli spiral aramayla
    en yakin BOS hucresine yakalanir. (x, y, yaw) doner; bulunamazsa None.
    """
    cx, cy = grid.world_to_cell(world_xy[0], world_xy[1])
    if grid.is_free(cx, cy):
        wx, wy = grid.cell_to_world(cx, cy)
        return (wx, wy, yaw)
    max_radius = int(math.ceil(snap_radius_m / grid.resolution))
    found = grid.nearest_free_cell(cx, cy, max_radius)
    if found is None:
        return None
    wx, wy = grid.cell_to_world(found[0], found[1])
    return (wx, wy, yaw)


def goal_pose_for_cluster(grid: OccupancyGrid2D,
                          cluster: FrontierCluster,
                          snap_radius_m: float = 0.5,
                          yaw: float = 0.0) -> Optional[tuple]:
    """Frontier kumesi icin BOS bir hedef noktasi uretir.

    Once merkez, BOS degilse kumenin BOS hucrelerinden birini dener.
    (x, y, yaw) doner; bulunamazsa None.
    """
    goal = goal_pose_for_point(grid, cluster.centroid, snap_radius_m, yaw)
    if goal is not None:
        return goal
    for wx, wy in cluster.cells:
        goal = goal_pose_for_point(grid, (wx, wy), snap_radius_m, yaw)
        if goal is not None:
            return goal
    return None
