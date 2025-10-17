from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .timing import DerivedTiming


@dataclass
class PulseTrain:
    # Rising edge times in seconds from t=0 reference
    edges_s: List[float]


def generate_xvs(dt: DerivedTiming, frames: int) -> PulseTrain:
    # One XVS rising edge per frame, starting at t=0
    edges = [n * dt.frame_period_s for n in range(frames)]
    return PulseTrain(edges_s=edges)


def generate_xhs(dt: DerivedTiming, lines_per_frame: int, frames: int) -> PulseTrain:
    # One XHS per line for each frame. Frame k is time-offset by k*TF
    edges: List[float] = []
    for k in range(frames):
        frame_offset = k * dt.frame_period_s
        edges.extend([frame_offset + n * dt.time_per_line_s for n in range(lines_per_frame)])
    return PulseTrain(edges_s=edges)


def exposure_window_for_line(line_index: int, dt: DerivedTiming) -> Tuple[float, float]:
    # Rolling shutter: each line starts integrating at its XHS time
    t_start = line_index * dt.time_per_line_s
    t_end = t_start + dt.exposure_time_s
    return t_start, t_end


