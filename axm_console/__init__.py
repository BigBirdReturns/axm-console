"""AXM Operator Console — one seat over the sovereign evidence ecosystem.

Drives a surface's spoke to a genesis-sealed shard, verifies it DETACHED, hands
you a plain-English custody receipt, and queues it for your review. Owns no
custody: sealing stays in the spokes, verification is the kernel's, and the
review queue records human decisions without making any.
"""
from .console import Console
from .receipt import Receipt, VerifyStatus, build_receipt, kernel_available
from .queue import Disposition, ReviewQueue
from .surfaces import Status, Surface, all_surfaces, get

__all__ = [
    "Console", "Receipt", "VerifyStatus", "build_receipt", "kernel_available",
    "Disposition", "ReviewQueue", "Status", "Surface", "all_surfaces", "get",
]
