from .cpu import check_cpu
from .memory import check_memory
from .disk import check_disk

TOOLS = [
    {
        "name": "check_cpu",
        "description": (
            "Returns current CPU utilization percentage, logical and physical core count, "
            "and clock frequency in MHz. Call this to assess CPU load."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_memory",
        "description": (
            "Returns RAM and swap usage: total, used, available in GB and percent used. "
            "Call this to assess memory pressure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_disk",
        "description": (
            "Returns disk usage for the root filesystem (/): total, used, free in GB "
            "and percent used. Call this to assess disk capacity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

TOOL_DISPATCH = {
    "check_cpu": check_cpu,
    "check_memory": check_memory,
    "check_disk": check_disk,
}
