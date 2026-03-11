"""Technique taxonomy endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from laaf.api.models import TechniqueSchema
from laaf.taxonomy.base import Category, get_registry

router = APIRouter(prefix="/techniques", tags=["Techniques"])


@router.get("", response_model=list[TechniqueSchema])
async def list_techniques(
    category: Optional[str] = Query(None, description="Filter by category")
):
    registry = get_registry()
    if category:
        try:
            cat = Category(category.lower())
        except ValueError:
            raise HTTPException(400, f"Unknown category: {category}")
        techniques = registry.by_category(cat)
    else:
        techniques = registry.all()

    return [
        TechniqueSchema(
            id=t.id, name=t.name, category=t.category.value,
            lpci_stage=t.lpci_stage, description=t.description, tags=t.tags,
        )
        for t in techniques
    ]


@router.get("/{technique_id}", response_model=TechniqueSchema)
async def get_technique(technique_id: str):
    registry = get_registry()
    t = registry.get(technique_id.upper())
    if not t:
        raise HTTPException(404, f"Technique {technique_id!r} not found")
    return TechniqueSchema(
        id=t.id, name=t.name, category=t.category.value,
        lpci_stage=t.lpci_stage, description=t.description, tags=t.tags,
    )
