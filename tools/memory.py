import psutil


def check_memory(**kwargs) -> dict:
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    gb = 1024 ** 3
    return {
        "ram_total_gb": round(vm.total / gb, 2),
        "ram_used_gb": round(vm.used / gb, 2),
        "ram_available_gb": round(vm.available / gb, 2),
        "ram_percent": vm.percent,
        "swap_total_gb": round(sw.total / gb, 2),
        "swap_used_gb": round(sw.used / gb, 2),
        "swap_percent": sw.percent,
    }
