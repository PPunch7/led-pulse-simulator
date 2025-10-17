from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .timing import DerivedTiming


@dataclass
class LedPulse:
    # List of (t_on, t_off) in seconds
    windows_s: List[Tuple[float, float]]


def single_flash_at_rt(dt: DerivedTiming, frames: int) -> LedPulse:
    # Fire LED at RT for FT seconds in each frame so all lines overlap
    windows: List[Tuple[float, float]] = []
    for k in range(frames):
        base = k * dt.frame_period_s
        t_on = base + dt.rolling_time_s
        t_off = t_on + dt.ft_s
        windows.append((t_on, t_off))
    return LedPulse(windows_s=windows)


def per_line_pwm(dt: DerivedTiming, pwm_freq_hz: float, duty: float, frames: int) -> LedPulse:
    # High-frequency PWM across the full simulation span [0, frames*TF)
    period = 1.0 / pwm_freq_hz
    windows: List[Tuple[float, float]] = []
    t = 0.0
    end_t = frames * dt.frame_period_s
    while t < end_t:
        on = t
        off = min(t + duty * period, end_t)
        if off > on:
            windows.append((on, off))
        t += period
    return LedPulse(windows_s=windows)


def overlaps(a_on: float, a_off: float, b_on: float, b_off: float) -> float:
    # Returns overlap duration in seconds
    start = max(a_on, b_on)
    end = min(a_off, b_off)
    return max(0.0, end - start)


