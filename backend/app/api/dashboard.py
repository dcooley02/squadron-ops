from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta, time as dt_time
from app.database import get_db
from app.models.models import (
    Person, Aircraft, Discrepancy, Currency, Sortie,
    Role, AircraftStatus,
)
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    """Compute squadron-wide readiness metrics."""
    today = date.today()
    cutoff_dt = datetime.combine(today - timedelta(days=30), dt_time.min)

    # Personnel
    total_personnel = db.query(func.count(Person.id)).filter(Person.is_active == True).scalar() or 0
    total_pilots = (
        db.query(func.count(Person.id))
        .filter(Person.role == Role.PILOT, Person.is_active == True)
        .scalar() or 0
    )
    total_aircrew = (
        db.query(func.count(Person.id))
        .filter(Person.role == Role.AIRCREW, Person.is_active == True)
        .scalar() or 0
    )

    # Aircraft
    aircraft_total = db.query(func.count(Aircraft.id)).scalar() or 0
    aircraft_fmc = (
        db.query(func.count(Aircraft.id))
        .filter(Aircraft.status == AircraftStatus.FMC)
        .scalar() or 0
    )
    aircraft_pmc = (
        db.query(func.count(Aircraft.id))
        .filter(Aircraft.status == AircraftStatus.PMC)
        .scalar() or 0
    )
    aircraft_nmc = (
        db.query(func.count(Aircraft.id))
        .filter(Aircraft.status.in_([AircraftStatus.NMC, AircraftStatus.NMCM, AircraftStatus.NMCS]))
        .scalar() or 0
    )
    fmc_rate = round(aircraft_fmc / aircraft_total * 100, 1) if aircraft_total > 0 else 0.0

    # Discrepancies
    open_discrepancies = (
        db.query(func.count(Discrepancy.id))
        .filter(Discrepancy.is_open == True)
        .scalar() or 0
    )

    # Currencies
    currencies_expiring_14d = (
        db.query(func.count(Currency.id))
        .filter(Currency.expires_date >= today, Currency.expires_date <= today + timedelta(days=14))
        .scalar() or 0
    )
    currencies_expired = (
        db.query(func.count(Currency.id))
        .filter(Currency.expires_date < today)
        .scalar() or 0
    )

    # Sorties / hours (last 30 days)
    sorties_30d = (
        db.query(func.count(Sortie.id))
        .filter(Sortie.is_complete == True, Sortie.takeoff_time >= cutoff_dt)
        .scalar() or 0
    )
    hours_30d_raw = (
        db.query(func.sum(Sortie.duration_hours))
        .filter(Sortie.is_complete == True, Sortie.takeoff_time >= cutoff_dt)
        .scalar()
    )

    return DashboardSummary(
        total_personnel=total_personnel,
        total_pilots=total_pilots,
        total_aircrew=total_aircrew,
        aircraft_total=aircraft_total,
        aircraft_fmc_count=aircraft_fmc,
        aircraft_pmc_count=aircraft_pmc,
        aircraft_nmc_count=aircraft_nmc,
        fmc_rate=fmc_rate,
        open_discrepancies_count=open_discrepancies,
        currencies_expiring_14d_count=currencies_expiring_14d,
        currencies_expired_count=currencies_expired,
        sorties_last_30_days=sorties_30d,
        total_hours_last_30_days=round(float(hours_30d_raw or 0.0), 1),
    )
