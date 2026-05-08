import psutil


def check_disk(**kwargs) -> dict:
    du = psutil.disk_usage("/")
    gb = 1024 ** 3
    return {
        "mount": "/",
        "total_gb": round(du.total / gb, 2),
        "used_gb": round(du.used / gb, 2),
        "free_gb": round(du.free / gb, 2),
        "percent_used": du.percent,
    }
