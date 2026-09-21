from __future__ import annotations

import os


def runtime_info() -> dict[str, str | bool]:
    """Report the fastest available compute backend without making GPU mandatory."""
    try:
        import torch
    except ImportError:
        return {"backend": "cpu", "cuda_available": False, "device": "cpu"}

    if torch.cuda.is_available():
        return {
            "backend": "cuda",
            "cuda_available": True,
            "device": torch.cuda.get_device_name(0),
        }
    return {"backend": "cpu", "cuda_available": False, "device": os.cpu_count() and f"cpu ({os.cpu_count()} threads)" or "cpu"}
