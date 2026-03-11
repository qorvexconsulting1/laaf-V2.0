"""Base classes and registry for the LAAF technique taxonomy."""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, ClassVar, Optional


class Category(str, Enum):
    ENCODING = "encoding"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    LAYERED = "layered"
    TRIGGER = "trigger"
    EXFILTRATION = "exfiltration"


class Outcome(str, Enum):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"


@dataclass
class Technique:
    """Represents one of the 49 LPCI attack techniques."""

    id: str                        # e.g. "E1", "S3", "M7", "L2", "T11"
    name: str                      # human-readable name
    category: Category
    lpci_stage: str                # primary lifecycle stage(s)
    description: str
    apply: Callable[[str], str]    # primary template fn
    tags: list[str] = field(default_factory=list)
    variants: list[Callable[[str], str]] = field(default_factory=list)
    # Additional template variants — randomly selected at generation time
    # Each variant is a different structural framing of the same technique.
    # With 5 variants per technique: effective template space × 5

    def __call__(self, instruction: str) -> str:
        """Apply a randomly selected template variant to the instruction."""
        import random
        pool = [self.apply] + self.variants
        fn = random.choice(pool)
        return fn(instruction)

    def __repr__(self) -> str:
        return f"<Technique {self.id}: {self.name} [{self.category.value}]>"


class TechniqueRegistry:
    """Singleton registry for all 49 LAAF techniques + third-party plugins."""

    _instance: ClassVar[Optional[TechniqueRegistry]] = None
    _techniques: dict[str, Technique]

    def __new__(cls) -> TechniqueRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._techniques = {}
        return cls._instance

    def register(self, technique: Technique) -> None:
        self._techniques[technique.id] = technique

    def get(self, technique_id: str) -> Optional[Technique]:
        return self._techniques.get(technique_id)

    def all(self) -> list[Technique]:
        return list(self._techniques.values())

    def by_category(self, category: Category) -> list[Technique]:
        return [t for t in self._techniques.values() if t.category == category]

    def ids(self) -> list[str]:
        return list(self._techniques.keys())

    def load_plugins(self) -> None:
        """Load third-party techniques registered via entry points."""
        try:
            eps = importlib.metadata.entry_points(group="laaf.techniques")
            for ep in eps:
                technique_class = ep.load()
                if callable(technique_class):
                    instance = technique_class()
                    if isinstance(instance, Technique):
                        self.register(instance)
        except Exception:
            pass  # plugins are optional

    def __len__(self) -> int:
        return len(self._techniques)

    def __contains__(self, technique_id: str) -> bool:
        return technique_id in self._techniques


def get_registry() -> TechniqueRegistry:
    """Return the global technique registry (initialises all built-ins on first call)."""
    return TechniqueRegistry()
