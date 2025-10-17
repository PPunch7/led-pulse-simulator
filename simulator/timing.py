from __future__ import annotations

from dataclasses import dataclass

from .config import SensorConfig


@dataclass
class DerivedTiming:
    time_per_clock_s: float
    time_per_line_s: float  # H
    frame_period_s: float   # TF
    rolling_time_s: float   # RT (top line start to bottom line start)
    exposure_time_s: float  # E (integration period)
    ft_s: float             # LED flash time


def compute_timing(cfg: SensorConfig) -> DerivedTiming:
    time_per_clock = 1.0 / cfg.inck_hz
    time_per_line = cfg.hmax_clocks * time_per_clock
    frame_period = cfg.vmax_lines * time_per_line
    rolling_time = (cfg.active_lines - 1) * time_per_line
    exposure_time = cfg.exposure_lines * time_per_line
    ft_s = cfg.led_ft_us * 1e-6
    return DerivedTiming(
        time_per_clock_s=time_per_clock,
        time_per_line_s=time_per_line,
        frame_period_s=frame_period,
        rolling_time_s=rolling_time,
        exposure_time_s=exposure_time,
        ft_s=ft_s,
    )


