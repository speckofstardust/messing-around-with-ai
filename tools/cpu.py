import psutil


def check_cpu(**kwargs) -> dict:
    freq = psutil.cpu_freq()
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "logical_cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": round(freq.current, 1) if freq else None,
        "frequency_max_mhz": round(freq.max, 1) if freq else None,
    }
