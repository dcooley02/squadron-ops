"""Shared seed constants and package-wide aliases."""
import random
from datetime import date

from passlib.hash import bcrypt as bc
from app.models.models import (
    GradecardSection, LineItemRole, GradingScheme,
    SyllabusLevel, SyllabusStage, SyllabusTrack, EventVenue,
)

random.seed(42)

DEMO_PW = bc.hash("demo1234")
TODAY = date.today()

GCS = GradecardSection
LIR = LineItemRole
GS  = GradingScheme
SL  = SyllabusLevel
SS  = SyllabusStage
ST  = SyllabusTrack
EV  = EventVenue
