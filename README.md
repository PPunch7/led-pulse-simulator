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


