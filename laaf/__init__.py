"""
LAAF — Logic-layer Automated Attack Framework
==============================================
Enterprise red-teaming framework for LPCI vulnerabilities in agentic LLM systems.

Reference: Atta et al., "LAAF: Logic-layer Automated Attack Framework", Qorvex Research, 2026
Paper:     https://arxiv.org/abs/2507.10457
"""

__version__ = "0.1.0"
__author__ = "Hammad Atta et al., Qorvex Research"
__license__ = "Apache-2.0"

from laaf.taxonomy.base import TechniqueRegistry

__all__ = ["__version__", "TechniqueRegistry"]
