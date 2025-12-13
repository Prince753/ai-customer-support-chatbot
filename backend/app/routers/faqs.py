"""
FAQ management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from ..models.faq import FAQ, FAQCreate, FAQUpdate, FAQCategory
from ..database import get_database

router = APIRouter(prefix="/faqs", tags=["FAQs"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[FAQ])
async def get_faqs(
    category: Optional[FAQCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in questions")
):
    """
    Get all active FAQs, optionally filtered by category.
    """
    try:
        db = get_database()
        faqs = await db.get_faqs(category=category.value if category else None)
        
        # Filter by search if provided
        if search:
            search_lower = search.lower()
            faqs = [
                f for f in faqs 
                if search_lower in f.get("question", "").lower()
                or search_lower in f.get("answer", "").lower()
                or any(search_lower in kw.lower() for kw in f.get("keywords", []))
            ]
        
        return faqs
        
    except Exception as e:
        logger.error(f"Error fetching FAQs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching FAQs")


@router.get("/categories")
async def get_categories():
    """Get all FAQ categories with counts."""
    try:
        db = get_database()
        faqs = await db.get_faqs()
        
        category_counts = {}
        for faq in faqs:
            cat = faq.get("category", "general")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            "categories": [
                {"name": cat.value, "display_name": cat.value.replace("_", " ").title(), "count": category_counts.get(cat.value, 0)}
                for cat in FAQCategory
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail="Error fetching categories")


@router.get("/{faq_id}", response_model=FAQ)
async def get_faq(faq_id: str):
    """Get a specific FAQ by ID."""
    try:
        db = get_database()
        faqs = await db.get_faqs()
        
        for faq in faqs:
            if faq.get("id") == faq_id:
                return faq
        
        raise HTTPException(status_code=404, detail="FAQ not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching FAQ: {e}")
        raise HTTPException(status_code=500, detail="Error fetching FAQ")


@router.post("/", response_model=FAQ)
async def create_faq(faq: FAQCreate):
    """Create a new FAQ entry."""
    try:
        db = get_database()
        result = await db.create_faq(
            question=faq.question,
            answer=faq.answer,
            category=faq.category.value,
            keywords=faq.keywords,
            priority=faq.priority
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create FAQ")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating FAQ: {e}")
        raise HTTPException(status_code=500, detail="Error creating FAQ")


@router.put("/{faq_id}", response_model=FAQ)
async def update_faq(faq_id: str, faq: FAQUpdate):
    """Update an existing FAQ."""
    try:
        db = get_database()
        
        updates = faq.model_dump(exclude_unset=True)
        if "category" in updates and updates["category"]:
            updates["category"] = updates["category"].value
        
        success = await db.update_faq(faq_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Fetch and return updated FAQ
        faqs = await db.get_faqs()
        for f in faqs:
            if f.get("id") == faq_id:
                return f
        
        raise HTTPException(status_code=404, detail="FAQ not found after update")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating FAQ: {e}")
        raise HTTPException(status_code=500, detail="Error updating FAQ")


@router.delete("/{faq_id}")
async def delete_faq(faq_id: str):
    """Delete (soft) an FAQ."""
    try:
        db = get_database()
        success = await db.delete_faq(faq_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        return {"success": True, "message": "FAQ deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting FAQ: {e}")
        raise HTTPException(status_code=500, detail="Error deleting FAQ")
