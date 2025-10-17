from dataclasses import dataclass


@dataclass
class SensorConfig:
    # Sensor base clocks and geometry
    inck_hz: float = 74_250_000.0  # IMX415 example input clock (Hz)
    hmax_clocks: int = 365         # clocks per line
    vmax_lines: int = 3400         # total lines per frame period
    active_lines: int = 2160       # visible lines

    # Exposure (rolling shutter integration) in lines
    exposure_lines: int = 2190     # example from description (>= active-1 + FT_lines + buffer)

    # LED flash time (single-flash) in microseconds
    led_ft_us: float = 100.0

    # Simulation span
    frames: int = 10

    # Plotting
    plot_ms_span: float = 18.0     # time window to visualize (ms)
    show_pwm_example: bool = True  # also demonstrate per-line PWM averaging
    pwm_frequency_khz: float = 200.0  # PWM within a line (example, high frequency)


DEFAULT_CONFIG = SensorConfig()


