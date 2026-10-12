"""PPC Waste Detector: Open-source ad spend optimization and budget leak detection platform."""

__version__ = "0.1.0"
__author__ = "Muhammad Hamid"

from ppc_waste_detector.models import (
    LeakCategory,
    PPCAccountAudit,
    Severity,
    WasteFinding,
    WasteSummary,
)

__all__ = [
    "LeakCategory",
    "Severity",
    "WasteFinding",
    "WasteSummary",
    "PPCAccountAudit",
]
