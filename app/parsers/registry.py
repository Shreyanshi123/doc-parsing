"""Registry - the "Registry" box. Parsers self-register with @register."""
from __future__ import annotations

from typing import Type

from app.parsers.base import BaseParser

_REGISTRY: dict[str, Type[BaseParser]] = {}


def register(cls: Type[BaseParser]) -> Type[BaseParser]:
    _REGISTRY[cls.name] = cls
    return cls


def get_parser_class(name: str) -> Type[BaseParser]:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown parser '{name}'. Known: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def list_parsers() -> list[dict]:
    out = []
    for name, cls in sorted(_REGISTRY.items()):
        ok, reason = cls.is_available()
        out.append(
            {
                "name": name,
                "description": cls.description,
                "supported_types": sorted(cls.supported_types),
                "cost": cls.cost,
                "available": ok,
                "unavailable_reason": reason,
            }
        )
    return out


def parsers_for(file_type: str, only_available: bool = True) -> list[Type[BaseParser]]:
    res = []
    for cls in _REGISTRY.values():
        if file_type in cls.supported_types and (not only_available or cls.is_available()[0]):
            res.append(cls)
    return res
