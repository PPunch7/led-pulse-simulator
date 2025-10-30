from __future__ import annotations

from typing import Optional

import numpy as np
from rich import print as rprint
import argparse

from .config import DEFAULT_CONFIG, SensorConfig
from .timing import compute_timing
from .signals import generate_xvs, generate_xhs, exposure_window_for_line
from .led import single_flash_at_rt, per_line_pwm, overlaps
from .visualize import plot_timeline
from .hw_gpio import run_hardware_session


def main():
    parser = argparse.ArgumentParser(description="IMX415 Rolling-Shutter + LED flash simulator")
    parser.add_argument("--inck-hz", type=float, default=None, help="Sensor INCK (Hz)")
    parser.add_argument("--hmax-clocks", type=int, default=None, help="HMAX clocks/line")
    parser.add_argument("--vmax-lines", type=int, default=None, help="VMAX lines/frame")
    parser.add_argument("--active-lines", type=int, default=None, help="Active lines")
    parser.add_argument("--exposure-lines", type=int, default=None, help="Exposure in lines")
    parser.add_argument("--led-ft-us", type=float, default=None, help="LED flash time (us)")
    parser.add_argument("--plot-ms-span", type=float, default=None, help="Plot window (ms)")
    parser.add_argument("--frames", type=int, default=None, help="Number of frames to simulate")
    parser.add_argument("--show-pwm", action="store_true", help="Also show per-line PWM overlay")
    parser.add_argument("--pwm-freq-khz", type=float, default=None, help="PWM frequency (kHz)")
    parser.add_argument("--print-details", "--print-detail", action="store_true", help="Print XVS, XHS(every 500), and LED times to terminal")
    # Hardware mode
    parser.add_argument("--hw", action="store_true", help="Use GPIO hardware capture instead of synthetic timing")
    parser.add_argument("--gpiochip", type=str, default="gpiochip0", help="gpiod chip name")
    parser.add_argument("--xvs-line", type=int, default=None, help="XVS GPIO line offset")
    parser.add_argument("--xhs-line", type=int, default=None, help="XHS GPIO line offset")
    parser.add_argument("--led-line", type=int, default=None, help="LED GPIO line offset (optional)")
    parser.add_argument("--xhs-samples", type=int, default=10, help="Number of XHS intervals to estimate H")
    parser.add_argument("--dry-led", action="store_true", help="Do not toggle LED line in hardware mode")

    args = parser.parse_args()

    cfg = SensorConfig(
        inck_hz=args.inck_hz if args.inck_hz is not None else DEFAULT_CONFIG.inck_hz,
        hmax_clocks=args.hmax_clocks if args.hmax_clocks is not None else DEFAULT_CONFIG.hmax_clocks,
        vmax_lines=args.vmax_lines if args.vmax_lines is not None else DEFAULT_CONFIG.vmax_lines,
        active_lines=args.active_lines if args.active_lines is not None else DEFAULT_CONFIG.active_lines,
        exposure_lines=args.exposure_lines if args.exposure_lines is not None else DEFAULT_CONFIG.exposure_lines,
        led_ft_us=args.led_ft_us if args.led_ft_us is not None else DEFAULT_CONFIG.led_ft_us,
        plot_ms_span=args.plot_ms_span if args.plot_ms_span is not None else DEFAULT_CONFIG.plot_ms_span,
        show_pwm_example=args.show_pwm or DEFAULT_CONFIG.show_pwm_example,
        pwm_frequency_khz=args.pwm_freq_khz if args.pwm_freq_khz is not None else DEFAULT_CONFIG.pwm_frequency_khz,
        frames=args.frames if args.frames is not None else DEFAULT_CONFIG.frames,
    )

    # Hardware capture mode
    if args.hw:
        if args.xvs_line is None or args.xhs_line is None:
            raise SystemExit("--hw requires --xvs-line and --xhs-line")
        # Use derived FT and RT for scheduling
        from .timing import compute_timing
        dt = compute_timing(cfg)
        run_hardware_session(
            frames=cfg.frames,
            gpiochip=args.gpiochip,
            xvs_offset=args.xvs_line,
            xhs_offset=args.xhs_line,
            led_offset=args.led_line,
            rolling_time_s=dt.rolling_time_s,
            ft_s=dt.ft_s,
            xhs_samples=args.xhs_samples,
            dry_led=args.dry_led,
        )
        return

    dt = compute_timing(cfg)
    xvs = generate_xvs(dt, frames=cfg.frames)
    xhs = generate_xhs(dt, lines_per_frame=cfg.vmax_lines, frames=cfg.frames)

    # LED strategy A: single flash at RT
    led_single = single_flash_at_rt(dt, frames=cfg.frames)

    # Optionally LED strategy B: per-line PWM
    led_pwm = None
    if cfg.show_pwm_example:
        led_pwm = per_line_pwm(dt, pwm_freq_hz=cfg.pwm_frequency_khz * 1e3, duty=0.5, frames=cfg.frames)

    # Compute overlap of single-flash with each line's exposure; verify uniformity
    overlaps_us = []
    for line in range(cfg.active_lines):
        t0, t1 = exposure_window_for_line(line, dt)
        ov = overlaps(t0, t1, led_single.windows_s[0][0], led_single.windows_s[0][1])
        overlaps_us.append(ov * 1e6)

    rprint("[bold]Derived Timing[/bold]")
    rprint({
        "H_us": dt.time_per_line_s * 1e6,
        "TF_ms": dt.frame_period_s * 1e3,
        "RT_ms": dt.rolling_time_s * 1e3,
        "Exposure_ms": dt.exposure_time_s * 1e3,
        "FT_us": dt.ft_s * 1e6,
    })
    # Show the simultaneous-exposure intersection window and margin
    overlap_window_us = (dt.exposure_time_s - dt.rolling_time_s) * 1e6
    margin_us = overlap_window_us - dt.ft_s * 1e6
    rprint({
        "Simultaneous_window_us": float(overlap_window_us),
        "FT_margin_us": float(margin_us),
    })

    rprint("\n[bold]Single-flash overlap per line (us)[/bold]")
    rprint(
        {
            "min": float(np.min(overlaps_us)),
            "max": float(np.max(overlaps_us)),
            "mean": float(np.mean(overlaps_us)),
            "std": float(np.std(overlaps_us)),
        }
    )

    if args.print_details:
        to_ms = lambda s: round(1e3 * s, 6)
        to_us = lambda s: round(1e6 * s, 3)
        rprint("\n[bold]XVS edges (ms)[/bold]")
        for idx, t in enumerate(xvs.edges_s):
            rprint({"idx": idx, "t_ms": to_ms(t)})

        rprint("\n[bold]XHS edges every 500th within ACTIVE lines (ms) with exposure end[/bold]")
        for idx, t in enumerate(xhs.edges_s):
            if idx % 500 != 0:
                continue
            frame_idx = idx // cfg.vmax_lines
            line_idx = idx % cfg.vmax_lines
            if line_idx < cfg.active_lines:
                exp_end_s = t + dt.exposure_time_s
                rprint({
                    "idx": idx,
                    "frame": frame_idx,
                    "line": line_idx,
                    "t_ms": to_ms(t),
                    "exp_end_ms": to_ms(exp_end_s),
                })

        rprint("\n[bold]LED single-flash windows[/bold]")
        for fi, (on, off) in enumerate(led_single.windows_s):
            rprint({"frame": fi, "on_ms": to_ms(on), "off_ms": to_ms(off), "dur_us": to_us(off - on)})

    # Compute last ACTIVE XHS per frame for highlighting
    last_xhs_ms = []
    for k in range(cfg.frames):
        last_idx = k * cfg.vmax_lines + (cfg.active_lines - 1)
        if last_idx < len(xhs.edges_s):
            last_xhs_ms.append(round(1e3 * xhs.edges_s[last_idx], 6))

    title = "Single Flash @ RT (gold), XVS (blue dashed), XHS (orange dotted), last ACTIVE XHS (red)"
    plot_timeline(cfg.plot_ms_span, xvs.edges_s, xhs.edges_s, led_single.windows_s, title, last_xhs_per_frame_ms=last_xhs_ms)

    if led_pwm is not None:
        title_pwm = f"Per-line PWM {cfg.pwm_frequency_khz} kHz, 50% duty"
        plot_timeline(cfg.plot_ms_span, xvs.edges_s, xhs.edges_s, led_pwm.windows_s, title_pwm, last_xhs_per_frame_ms=last_xhs_ms)


if __name__ == "__main__":
    main()


