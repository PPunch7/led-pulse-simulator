LED Rolling-Shutter Flash Simulator (IMX415 + ROCK 5C)

Overview
This small Python simulator models Sony IMX415 master mode timing (XVS/XHS), rolling exposure, and LED flash strategies (single short flash and line-synced PWM) to visualize how to avoid banding and skew. Defaults approximate 4K@60 (INCK 74.25 MHz, HMAX 365 clocks, VMAX 3400 lines).

Features
- XVS (frame start) and XHS (line start) signal generators
- Derived timing: H (time/line), TF (frame period), RT (rolling time top-to-bottom), exposure E (in lines/time)
- Configurable LED flash window FT (microseconds)
- Strategies: single flash at RT; optional per-line high-frequency PWM averaging within a line
- Visualization via matplotlib timelines

Quick start (Windows PowerShell)
1) Create/activate venv
   python -m venv .venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .venv\\Scripts\\Activate.ps1

2) Install
   pip install -r requirements.txt

3) Run default 4K@60 simulation
   python -m simulator.run

4) Show CLI options
   python -m simulator.run --help

Optional
1) Define frame number
   --frames [number of frames]

2) Define timing display
   --plot-ms-span [number of ms]

3) Display more info on terminal
   --print-details

Config
- All tunables live in simulator/config.py. Change INCK, HMAX, VMAX, active_lines, exposure_lines, FT_us, and plotting span.

Notes
- This is a timing model for understanding; it does not interface with hardware GPIO.
- Units are carefully tracked (seconds, microseconds, lines, clocks).

---------------------------------------------------------------------------------------------------------------------------------

## Using with real hardware (Linux + libgpiod)

Prerequisites
- Linux on your board (e.g., Radxa ROCK 5C)
- Python 3 and a virtualenv (optional)
- libgpiod userspace tools and Python bindings:

```bash
sudo apt-get update
sudo apt-get install -y gpiod libgpiod-dev python3-libgpiod
```

Identify GPIO chips and line offsets
1) List chips:
```bash
gpiodetect
```
2) Inspect lines (repeat per chip):
```bash
gpioinfo gpiochip0
gpioinfo gpiochip1
```
Look for the line number (offset) you wired to XVS, XHS, and LED. The number shown as "line N:" is the offset.

Verify signals (optional but recommended)
- XVS rising edges (about your frame rate, e.g., ~60 Hz):
```bash
gpiomon --rising --num-events 5 gpiochipX <xvs_offset>
```
- XHS is very high frequency (~200 kHz at 4K/60); userspace may miss edges. It's fine—hardware mode mainly uses XVS for flash scheduling (RT). We only sample a few XHS edges to estimate H optionally.

Verify LED line (be careful with your driver circuit)
```bash
gpioset gpiochipY <led_offset>=1   # ON
gpioset gpiochipY <led_offset>=0   # OFF
```

Run the simulator in hardware mode
- From the project root after installing Python deps:
```bash
python -m simulator.run --hw \
  --frames 5 \
  --gpiochip gpiochipX \
  --xvs-line <xvs_offset> \
  --xhs-line <xhs_offset> \
  --led-line <led_offset>
```

Handle sensor warm-up (unstable XVS/XHS right after power-up)
- If early frames/edges are unstable, delay and/or skip initial XVS edges before capturing:
```bash
# Add a fixed delay (e.g., 2 seconds) before starting
python -m simulator.run --hw --hw-delay-s 2 \
  --gpiochip gpiochipX --xvs-line <xvs> --xhs-line <xhs> --led-line <led>

# Skip first N XVS pulses (e.g., 5 frames) to let timing stabilize
python -m simulator.run --hw --hw-warmup-xvs 5 \
  --gpiochip gpiochipX --xvs-line <xvs> --xhs-line <xhs> --led-line <led>

# Combine both if needed
python -m simulator.run --hw --hw-delay-s 1.5 --hw-warmup-xvs 3 \
  --gpiochip gpiochipX --xvs-line <xvs> --xhs-line <xhs> --led-line <led>
```

Flags
- `--hw`: enable hardware capture mode (uses libgpiod)
- `--gpiochip`: chip name from gpiodetect (e.g., gpiochip0)
- `--xvs-line`, `--xhs-line`: line offsets (integers) from gpioinfo
- `--led-line`: LED output line offset (optional; omit or use `--dry-led` to avoid toggling)
- `--xhs-samples`: number of XHS intervals to measure H (default 10). If XHS is too fast, use `--xhs-samples 0`.
- `--dry-led`: schedule but do not toggle the LED line
- `--hw-delay-s`: warm-up delay (seconds) before capturing in HW mode
- `--hw-warmup-xvs`: number of initial XVS edges to skip before capturing in HW mode

Notes on timing accuracy
- Userspace scheduling introduces jitter at microsecond scales. For production-grade precision, prefer a hardware timer/PWM, a kernel driver, or an external MCU triggered by XVS.
- Ensure the kernel/device tree does not claim your chosen GPIO lines (check the "consumer" field in `gpioinfo`).



