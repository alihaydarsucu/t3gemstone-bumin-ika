"""Harita kapsam hesabi.

"Bilinen hucre" = free veya occupied (bilinmeyen degil). Kapsam orani,
belirtilen kesif sinirlari icindeki bilinen hucrelerin toplam hucrelere
oranidir. Kesif sonlandirmasi icin esik bu degerle karsilastirilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .occupancy_grid_2d import GridExtent, OccupancyGrid2D


@dataclass
class CoverageResult:
    ratio: float = 0.0
    known_cells: int = 0
    total_cells: int = 0
    known_area_m2: float = 0.0
    total_area_m2: float = 0.0


def compute_coverage(grid: OccupancyGrid2D,
                     extent: Optional[GridExtent] = None) -> CoverageResult:
    """Sinirlar icindeki bilinen hucre oranini hesaplar.

    extent.enabled ise yalnizca sinir kutusu icindeki hucreler sayilir;
    degilse tum harita sayilir.
    """
    known = 0
    total = 0
    res2 = grid.resolution * grid.resolution

    for cy in range(grid.height):
        for cx in range(grid.width):
            if extent is not None and extent.enabled:
                wx, wy = grid.cell_to_world(cx, cy)
                if not extent.contains(wx, wy):
                    continue
            total += 1
            if grid.known(cx, cy):
                known += 1

    if total == 0:
        return CoverageResult()

    return CoverageResult(
        ratio=known / total,
        known_cells=known,
        total_cells=total,
        known_area_m2=known * res2,
        total_area_m2=total * res2,
    )
