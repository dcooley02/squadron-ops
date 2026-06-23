from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.models import BoardStatus, BoardType


class InstructorCandidate(BaseModel):
    person_id: int
    person_name: str
    callsign: Optional[str] = None
    rank: Optional[str] = None
    score: int
    factors: List[str] = []


class BoardScheduleCreate(BaseModel):
    board_type: BoardType
    scheduled_at: datetime
    examinee_person_id: int
    instructor_person_id: Optional[int] = None
    syllabus_event_id: Optional[int] = None
    sortie_id: Optional[int] = None
    location: Optional[str] = None
    remarks: Optional[str] = None


class BoardScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    board_type: BoardType
    scheduled_at: datetime
    examinee_person_id: int
    examinee_name: str
    instructor_person_id: Optional[int] = None
    instructor_name: Optional[str] = None
    syllabus_event_id: Optional[int] = None
    event_code: Optional[str] = None
    gradecard_id: Optional[int] = None
    sortie_id: Optional[int] = None
    status: BoardStatus
    location: Optional[str] = None
    remarks: Optional[str] = None