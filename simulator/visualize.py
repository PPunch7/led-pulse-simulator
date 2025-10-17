from __future__ import annotations

from typing import Iterable, Tuple

import matplotlib.pyplot as plt


def plot_timeline(ms_span: float,
                  xvs_edges_s: Iterable[float],
                  xhs_edges_s: Iterable[float],
                  led_windows: Iterable[Tuple[float, float]],
                  title: str,
                  last_xhs_per_frame_ms: Iterable[float] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(10, 3))
    # Convert to ms for the plot
    to_ms = lambda s: 1e3 * s

    for t in xvs_edges_s:
        if to_ms(t) <= ms_span:
            ax.axvline(to_ms(t), color='C0', linestyle='--', alpha=0.7, label='XVS' if t == 0 else None)

    # Plot a subset of XHS edges for clarity
    for idx, t in enumerate(xhs_edges_s):
        tm = to_ms(t)
        if tm > ms_span:
            break
        if idx % 50 == 0:
            ax.axvline(tm, color='C1', linestyle=':', alpha=0.4, label='XHS' if idx == 0 else None)

    # Highlight last XHS per frame, if provided
    if last_xhs_per_frame_ms is not None:
        for i, tm in enumerate(last_xhs_per_frame_ms):
            if tm <= ms_span:
                ax.axvline(tm, color='red', linestyle='-', alpha=0.8, linewidth=2.0,
                           label='Last XHS in frame' if i == 0 else None)

    for i, (on, off) in enumerate(led_windows):
        on_ms, off_ms = to_ms(on), to_ms(off)
        if on_ms > ms_span:
            break
        ax.axvspan(on_ms, min(off_ms, ms_span), color='gold', alpha=0.4, label='LED' if i == 0 else None)

    ax.set_xlim(0, ms_span)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel('time (ms)')
    ax.set_title(title)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')
    fig.tight_layout()
    plt.show()


