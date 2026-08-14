"""Kalici global frontier veritabani (MIGHTY ilhamli).

slam_toolbox /map'i tum bolgeyi yayinlar; yine de frontier kumeleri her
tarama dongusunde hafif kayar (EMA), kaybolur ve yeniden belirir. Bu
yonetici dunya-cercevesinde tum gorulen frontier'lari bir veritabaninda
tutar, ACTIVE/VISITED/INVALIDATED olarak siniflar ve kesif hedefi secimi
icin API sunar.

Matching: yeni bir kume, var olan bir kayda merge_radius_m icindeyse eslestirilir
ve merkez EMA ile guncellenir; degilse yeni kayit acilir.
Dwell-visit: robot bir frontier'in visit_radius_m yakiniysa ve visit_dwell_sec
kadar orada kaliyorsa kayit VISITED isaretlenir (tekrarlanan ayni-hedef
sallanmasini onler).
Invalidation: hala gorunmezse (haritada kayboldu / kuculdu) INVALIDATED
isaretlenir ve tekrar secilmez.

Saf mantik modulu; ROS bagimliligi yoktur.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


class FrontierState(Enum):
    ACTIVE = auto()        # hala gecerli, secilebilir
    VISITED = auto()       # robot zaten kesfetti
    INVALIDATED = auto()   # erisilemez / kayboldu


@dataclass
class FrontierRecord:
    id: int = 0
    centroid: tuple = (0.0, 0.0)          # dunya cercevesi
    size_cells: int = 0
    size_m2: float = 0.0
    first_seen_t: float = 0.0
    last_seen_t: float = 0.0
    state: FrontierState = FrontierState.ACTIVE
    visit_count: int = 0
    dwell_time_sec: float = 0.0
    aabb_min: tuple = (0.0, 0.0)
    aabb_max: tuple = (0.0, 0.0)
    # pursuit takibi: secilen hedefin gecerlilik siniri (yoksa -1)
    pursuit_deadline_t: float = -1.0

    @property
    def centroid_x(self) -> float:
        return self.centroid[0]

    @property
    def centroid_y(self) -> float:
        return self.centroid[1]

    def dist_to(self, xy: tuple) -> float:
        return math.hypot(self.centroid_x - xy[0],
                          self.centroid_y - xy[1])


@dataclass
class FrontierManagerParams:
    # Esleme / yasam dongusu
    merge_radius_m: float = 1.0
    centroid_ema_alpha: float = 0.5
    visit_radius_m: float = 0.6
    visit_dwell_sec: float = 1.5
    max_frontiers: int = 500

    # Puanlama (eklemeli): her agirlik >= 0; 0 = devre disi
    w_size: float = 1.0
    w_dist: float = 2.0
    size_ref_m2: float = 5.0
    dist_ref_m: float = 25.0
    goal_select_threshold: float = -1.0e9

    # Pursuit zamandasimi: secilen hedefe taninan sinir suresi
    pursuit_timeout_min_sec: float = 10.0


class FrontierManager:
    """Frontier kayitlarini tutar ve secim API'si saglar."""

    def __init__(self, params: FrontierManagerParams):
        self.params = params
        self._records: List[FrontierRecord] = []
        self._next_id = 0
        self._last_update_t = 0.0

    # ------------------------------------------------------------------
    # Guncelleme
    # ------------------------------------------------------------------
    def update(self, fresh: List, robot_xy: tuple, t_now: float) -> None:
        """Yeni detection partisini DB'ye isler.

        Eslestir -> EMA guncelle; yenileri ekle; eslesmeyen ACTIVE kayitlari
        INVALIDATED yap; robot yakiniysa dwell-visit kontrolu.
        """
        dt = max(0.0, t_now - self._last_update_t)
        params = self.params

        # 1) fresh kumeleri eslestir / ekle
        matched: set = set()
        for cluster in fresh:
            rec = self._match(cluster)
            if rec is None:
                rec = self._insert(cluster, t_now)
            else:
                alpha = params.centroid_ema_alpha
                c = cluster.centroid
                rec.centroid = (
                    alpha * c[0] + (1.0 - alpha) * rec.centroid_x,
                    alpha * c[1] + (1.0 - alpha) * rec.centroid_y,
                )
                rec.size_cells = cluster.size_cells
                rec.size_m2 = cluster.size_m2
                rec.aabb_min = cluster.aabb_min
                rec.aabb_max = cluster.aabb_max
                rec.last_seen_t = t_now
                if rec.state == FrontierState.INVALIDATED:
                    # yeniden canlanan frontier'i tekrar aktiflestir
                    rec.state = FrontierState.ACTIVE
            matched.add(rec.id)

        # 2) eslesmeyen ACTIVE kayitlar kayboldu -> INVALIDATED
        for rec in self._records:
            if rec.id not in matched and rec.state == FrontierState.ACTIVE:
                rec.state = FrontierState.INVALIDATED
                rec.last_seen_t = t_now

        # 3) dwell-visit kontrolu
        for rec in self._records:
            if rec.state != FrontierState.ACTIVE:
                continue
            if rec.dist_to(robot_xy) <= params.visit_radius_m:
                rec.dwell_time_sec += dt
                if rec.dwell_time_sec >= params.visit_dwell_sec:
                    self.mark_visited(rec.id)
            else:
                rec.dwell_time_sec = max(0.0, rec.dwell_time_sec - dt)

        # 4) pursuit sinir kontrolu
        for rec in self._records:
            if rec.state != FrontierState.ACTIVE:
                continue
            if rec.pursuit_deadline_t > 0 and t_now > rec.pursuit_deadline_t:
                self.mark_invalidated(rec.id, t_now)

        self._evict_if_over_cap()
        self._last_update_t = t_now

    def _match(self, cluster) -> Optional[FrontierRecord]:
        best = None
        best_d = self.params.merge_radius_m
        for rec in self._records:
            if rec.state not in (FrontierState.ACTIVE,
                                 FrontierState.INVALIDATED):
                continue
            d = math.hypot(rec.centroid_x - cluster.centroid[0],
                           rec.centroid_y - cluster.centroid[1])
            if d <= best_d:
                best_d = d
                best = rec
        return best

    def _insert(self, cluster, t_now: float) -> FrontierRecord:
        rec = FrontierRecord(
            id=self._next_id,
            centroid=cluster.centroid,
            size_cells=cluster.size_cells,
            size_m2=cluster.size_m2,
            first_seen_t=t_now,
            last_seen_t=t_now,
            state=FrontierState.ACTIVE,
            aabb_min=cluster.aabb_min,
            aabb_max=cluster.aabb_max,
        )
        self._next_id += 1
        self._records.append(rec)
        return rec

    def _evict_if_over_cap(self) -> None:
        cap = self.params.max_frontiers
        if len(self._records) <= cap:
            return
        # en eski gorulenleri cikar (ACTIVE kayitlari oncelikli koru)
        stale = sorted(self._records,
                       key=lambda r: (r.state == FrontierState.ACTIVE,
                                      r.last_seen_t))
        for rec in stale[:len(self._records) - cap]:
            self._records.remove(rec)

    # ------------------------------------------------------------------
    # Durum degisimleri
    # ------------------------------------------------------------------
    def mark_visited(self, rec_id: int) -> None:
        rec = self.find(rec_id)
        if rec is None or rec.state == FrontierState.VISITED:
            return
        rec.state = FrontierState.VISITED
        rec.visit_count += 1
        rec.pursuit_deadline_t = -1.0

    def mark_invalidated(self, rec_id: int, t_now: float) -> None:
        rec = self.find(rec_id)
        if rec is None or rec.state == FrontierState.INVALIDATED:
            return
        rec.state = FrontierState.INVALIDATED
        rec.last_seen_t = t_now
        rec.pursuit_deadline_t = -1.0

    def mark_selected(self, rec_id: int, robot_xy: tuple, t_now: float) -> None:
        rec = self.find(rec_id)
        if rec is None:
            return
        dist = rec.dist_to(robot_xy)
        rec.pursuit_deadline_t = t_now + max(
            self.params.pursuit_timeout_min_sec, dist / 0.5 * 10.0)

    # ------------------------------------------------------------------
    # Sorgular
    # ------------------------------------------------------------------
    def find(self, rec_id: int) -> Optional[FrontierRecord]:
        for rec in self._records:
            if rec.id == rec_id:
                return rec
        return None

    def records(self) -> List[FrontierRecord]:
        return self._records

    def size(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records = []
        self._next_id = 0
        self._last_update_t = 0.0

    def active(self) -> List[FrontierRecord]:
        return [r for r in self._records if r.state == FrontierState.ACTIVE]
