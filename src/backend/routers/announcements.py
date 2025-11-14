from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.collection import Collection
from datetime import datetime
from typing import List, Optional
from ..database import announcements_collection
from ..routers.auth import get_current_user

router = APIRouter(prefix="/announcements", tags=["announcements"])

def announcement_serializer(ann):
    return {
        "id": str(ann.get("_id", "")),
        "title": ann.get("title", ""),
        "message": ann.get("message", ""),
        "expiration": ann.get("expiration", ""),
        "start": ann.get("start", None)
    }

@router.get("/", response_model=List[dict])
def list_announcements():
    now = datetime.utcnow().isoformat() + "Z"
    anns = announcements_collection.find({
        "$and": [
            {"expiration": {"$gte": now}},
            {"$or": [
                {"start": {"$exists": False}},
                {"start": {"$lte": now}}
            ]}
        ]
    })
    return [announcement_serializer(a) for a in anns]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_announcement(data: dict, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not data.get("title") or not data.get("message") or not data.get("expiration"):
        raise HTTPException(status_code=400, detail="Title, message, and expiration required")
    ann = {
        "title": data["title"],
        "message": data["message"],
        "expiration": data["expiration"],
    }
    if data.get("start"):
        ann["start"] = data["start"]
    result = announcements_collection.insert_one(ann)
    return {"id": str(result.inserted_id)}

@router.put("/{ann_id}")
def update_announcement(ann_id: str, data: dict, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    update = {k: v for k, v in data.items() if k in ["title", "message", "expiration", "start"]}
    if not update:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    result = announcements_collection.update_one({"_id": ann_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"success": True}

@router.delete("/{ann_id}")
def delete_announcement(ann_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = announcements_collection.delete_one({"_id": ann_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"success": True}
