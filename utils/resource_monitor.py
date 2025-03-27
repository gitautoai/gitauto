import os
from typing import Optional
import psutil


def get_resource_usage(path: Optional[str] = None) -> dict[str, float]:
    """
    Get current memory usage and storage size.

    Args:
        path: Optional path to measure storage size. If None, only memory is measured.

    Returns:
        Dictionary containing:
        - memory_mb: Current process memory usage in MB
        - storage_mb: Storage size of path in MB (if path provided)
    """
    metrics = {}

    # Memory usage
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    metrics["memory_mb"] = round(memory_mb, 2)

    # Storage size
    if path and os.path.exists(path):
        if os.path.isdir(path):
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(path)
                for filename in filenames
            )
        else:
            total_size = os.path.getsize(path)
        storage_mb = total_size / 1024 / 1024
        metrics["storage_mb"] = round(storage_mb, 2)

    return metrics
