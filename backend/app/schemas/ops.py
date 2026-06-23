from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.models import SortieOpsStatus, WatchbillRole


class SchedulePublishRequest(BaseModel):
    published_by_person_id: Optional[int] = None
    remarks: Optional[str] = None


class SchedulePublicationOut(BaseModel):
    id: int
    schedule_date: date
    published_at: datetime
    published_by_name: Optional[str] = None
    remarks: Optional[str] = None


class WatchbillEntryCreate(BaseModel):
    duty_date: date
    role: WatchbillRole
    person_id: int
    shift_label: Optional[str] = None
    notes: Optional[str] = None


class WatchbillEntryOut(BaseModel):
    id: int
    duty_date: date
    role: WatchbillRole
    person_id: int
    person_name: str
    shift_label: Optional[str] = None
    notes: Optional[str] = None


class DayOpsCrewSlot(BaseModel):
    person_id: int
    person_name: str
    crew_position: str


class DayOpsSortie(BaseModel):
    id: int
    event_code: Optional[str] = None
    event_type: Optional[str] = None
    aircraft_side_number: Optional[str] = None
    brief_time: Optional[datetime] = None
    takeoff_time: Optional[datetime] = None
    land_time: Optional[datetime] = None
    ops_status: SortieOpsStatus
    is_complete: bool
    mission_summary: Optional[str] = None
    comm_plan: Optional[str] = None
    crew: List[DayOpsCrewSlot] = []


class DayOpsOut(BaseModel):
    ops_date: date
    is_published: bool
    publication: Optional[SchedulePublicationOut] = None
    watchbill: List[WatchbillEntryOut] = []
    sorties: List[DayOpsSortie] = []
    sortie_count: int
    airborne_count: int


class SortieOpsStatusPatch(BaseModel):
    ops_status: SortieOpsStatus
    mission_summary: Optional[str] = None
    comm_plan: Optional[str] = None
    brief_sheet_notes: Optional[str] = None