from typing import Tuple


def publish_args(branch_name) -> Tuple[str, str]:
    return (
        "https://github.com/blooop/taichi_sweep.git",
        f"https://github.com/blooop/taichi_sweep/blob/{branch_name}",
    )
