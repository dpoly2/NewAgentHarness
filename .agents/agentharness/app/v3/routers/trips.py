from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _create_record, _delete_record, _get_record, _list_records, _now_iso, _update_record
from core.models import TripCreate, TripUpdate

router = APIRouter()

@router.get("/trips")
async def list_trips(current_user: dict = Depends(get_current_user)):
    del current_user
    return _list_records("travel_trips", order_by="updated_at DESC")


@router.post("/trips")
async def create_trip(body: TripCreate, current_user: dict = Depends(get_current_user)):
    del current_user
    return _create_record(
        "travel_trips",
        {
            "id": uuid.uuid4().hex,
            "name": body.name,
            "destination": body.destination,
            "depart_date": body.depart_date,
            "return_date": body.return_date,
            "status": body.status,
            "budget": body.budget,
            "spent": 0.0,
            "notes": body.notes,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
    )


@router.get("/trips/{id}")
async def get_trip(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    trip = _get_record("travel_trips", id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    return trip


@router.put("/trips/{id}")
async def update_trip(id: str, body: TripUpdate, current_user: dict = Depends(get_current_user)):
    del current_user
    updates = {key: value for key, value in body.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = _now_iso()
    trip = _update_record("travel_trips", id, updates)
    if not trip:
        raise HTTPException(404, "Trip not found")
    return trip


@router.delete("/trips/{id}")
async def delete_trip(id: str, current_user: dict = Depends(get_current_user)):
    del current_user
    if not _delete_record("travel_trips", id):
        raise HTTPException(404, "Trip not found")
    return {"id": id, "deleted": True}
