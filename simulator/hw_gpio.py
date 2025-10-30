from __future__ import annotations

import time
from typing import List, Tuple, Optional


def _ns_to_s(ns: int) -> float:
    return ns / 1_000_000_000.0


def _sleep_until(target_monotonic_s: float) -> None:
    # Simple sleep-until helper using time.monotonic()
    while True:
        now = time.monotonic()
        remaining = target_monotonic_s - now
        if remaining <= 0:
            return
        # Sleep in small chunks to reduce oversleep
        time.sleep(min(remaining, 0.001))


def run_hardware_session(
    *,
    frames: int,
    gpiochip: str,
    xvs_offset: int,
    xhs_offset: int,
    led_offset: Optional[int],
    rolling_time_s: float,
    ft_s: float,
    xhs_samples: int,
    dry_led: bool,
) -> None:
    """Capture XVS/XHS from GPIO and fire LED at RT for each frame.

    Notes:
    - Requires libgpiod Python bindings installed on the device.
    - LED timing accuracy depends on OS scheduling; this is a best-effort userspace approach.
    """
    try:
        import gpiod  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "gpiod module not available. Install libgpiod Python bindings on the device."
        ) from exc

    chip = gpiod.Chip(gpiochip)
    xvs_line = chip.get_line(xvs_offset)
    xhs_line = chip.get_line(xhs_offset)

    xvs_line.request(consumer="led-sim", type=gpiod.LINE_REQ_EV_RISING)
    xhs_line.request(consumer="led-sim", type=gpiod.LINE_REQ_EV_RISING)

    led_line = None
    if led_offset is not None:
        led_line = chip.get_line(led_offset)
        led_line.request(consumer="led-sim", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

    def read_event_ts(line, timeout_s: float = 5.0) -> float:
        if not line.event_wait(timeout_s):
            raise TimeoutError("Timeout waiting for GPIO event")
        ev = line.event_read()
        return ev.sec + ev.nsec / 1e9

    # Sync on first XVS
    first_xvs_s = read_event_ts(xvs_line, timeout_s=10.0)

    # Measure H from a handful of XHS intervals to report
    h_samples: List[float] = []
    last_ts = None
    for _ in range(max(0, xhs_samples)):
        ts = read_event_ts(xhs_line, timeout_s=0.5)
        if last_ts is not None:
            h_samples.append(ts - last_ts)
        last_ts = ts

    h_est_s = sum(h_samples) / len(h_samples) if h_samples else None

    # Process frames
    xvs_times: List[float] = [first_xvs_s]
    try:
        for frame_idx in range(frames):
            if frame_idx > 0:
                xvs_times.append(read_event_ts(xvs_line, timeout_s=2.0))

            xvs_t = xvs_times[-1]
            # Schedule LED at RT relative to now
            if led_line is not None and not dry_led:
                # Convert to monotonic-based schedule from receipt time
                start_at = time.monotonic() + rolling_time_s
                _sleep_until(start_at)
                led_line.set_value(1)
                _sleep_until(start_at + ft_s)
                led_line.set_value(0)
    finally:
        try:
            if led_line is not None:
                led_line.set_value(0)
        except Exception:
            pass
        xvs_line.release()
        xhs_line.release()
        if led_line is not None:
            led_line.release()
        chip.close()

    # Print simple report
    print({
        "frames": frames,
        "xvs_count": len(xvs_times),
        "H_est_us": (h_est_s * 1e6) if h_est_s else None,
    })


