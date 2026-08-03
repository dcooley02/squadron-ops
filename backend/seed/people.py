"""Persons, qualifications, currencies, and Wing Table B-2 currency types."""
import random
from datetime import timedelta

from app.models.models import (
    Person, Qualification, Currency, CurrencyType, CurrencyApplicability,
    Role, CurrencyAudience,
)

from seed.constants import DEMO_PW, TODAY

# ═══════════════════════════════════════════════════════════════════════════════
# Wing Table B-2 Currency Types
# ═══════════════════════════════════════════════════════════════════════════════

_CA = CurrencyAudience

_CURRENCY_TYPES = [
    dict(
        code="NIGHT_NVD", name="Night/NVD",
        periodicity_days=45, requirement_text="2.0 hrs night/NVD",
        min_hours=2.0, sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="NVD_TERF", name="NVD TERF (Terrain Following)",
        periodicity_days=30, requirement_text="2.0 hrs NVD TERF",
        min_hours=2.0, sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="NVD_TERF_INST", name="NVD TERF Instructor",
        periodicity_days=45, requirement_text="10.0 flight hours",
        min_hours=10.0, sim_eligible=False,
        references=["3710.7G Table B-2 Note 1"],
        applicability=[(_CA.HAC_ONLY, None)],
    ),
    dict(
        code="DAY_DVE", name="Day DVE Approaches",
        periodicity_days=60,
        requirement_text="3 day DVE approaches to a landing",
        min_count=3, count_unit="approaches", sim_eligible=False,
        description="NVD DVE approaches confer Day DVE approaches per Wing Note 2.",
        references=["3710.7G Table B-2 Note 2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="NVD_DVE", name="NVD DVE Approaches",
        periodicity_days=30, requirement_text="6 NVD landings",
        min_count=6, count_unit="landings", sim_eligible=False,
        references=["3710.7G Table B-2 Note 2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="STRAFE_DRY", name="Strafe Dry Fire",
        periodicity_days=90, requirement_text="3 day and 3 night profiles",
        min_count=6, count_unit="profiles", sim_eligible=True,
        sim_notes="May be conducted in Aircraft, TOFT or WTT per Wing Note 3. Night must be conducted wearing NVDs.",
        references=["3710.7G Table B-2 Note 3"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="STRAFE_LIVE", name="Strafe Live Fire",
        periodicity_days=90,
        requirement_text="300×20mm or 9 UGR; day or night",
        min_count=300, count_unit="rounds 20mm OR 9 UGR", sim_eligible=False,
        description="Annual evaluation required regardless of 90-day currency. Annual eval shall be completed post-FRS training.",
        references=["3710.7G Table B-2 Note 4"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="CSW", name="Crew-Served Weapons",
        periodicity_days=90, requirement_text="400 rounds (min 200 night)",
        min_count=400, count_unit="rounds (min 200 night)", sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.ALL_PILOTS, None), (_CA.ALL_AIRCREWMEN, None)],
    ),
    dict(
        code="ALMDS_PILOT", name="ALMDS (Pilot)",
        periodicity_days=180, requirement_text="1.0 hour",
        min_hours=1.0, sim_eligible=False,
        description="PAC shall be up night couplers. Not required to be accomplished in AMCM-configured aircraft.",
        references=["3710.7G Table B-2 Note 5"],
        applicability=[(_CA.AMCM_QUAL_PILOTS, None)],
    ),
    dict(
        code="ALMDS_SO", name="ALMDS (Sensor Operator)",
        periodicity_days=180, requirement_text="1.0 hour",
        min_hours=1.0, sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.AWS_ONLY, "AMCM_SO")],
    ),
    dict(
        code="AMNS_PILOT", name="AMNS (Pilot)",
        periodicity_days=180,
        requirement_text="2 simulated or actual NVD iterations",
        min_count=2, count_unit="iterations", sim_eligible=True,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.AMCM_QUAL_PILOTS, None)],
    ),
    dict(
        code="AMNS_SO", name="AMNS (Sensor Operator)",
        periodicity_days=180,
        requirement_text="2 NTR vs 2 mines, day or night",
        min_count=2, count_unit="NTRs", sim_eligible=True,
        sim_notes="May be completed in the WTT per Wing Note 6",
        references=["3710.7G Table B-2 Note 6"],
        applicability=[(_CA.AWS_ONLY, "AMCM_SO")],
    ),
    dict(
        code="CSTRS_WINCH", name="CSTRS Winch Operator",
        periodicity_days=180, requirement_text="2 stream/recovery",
        min_count=2, count_unit="stream/recovery", sim_eligible=False,
        description="The shore-based CSTRS-T may be applied for non-consecutive 180-day periods.",
        references=["3710.7G Table B-2 Note 7"],
        applicability=[(_CA.HOIST_OP_QUAL, None)],
    ),
]


def seed_currency_types(db):
    ct_count = 0
    ca_count = 0
    for entry in _CURRENCY_TYPES:
        applicability = entry.pop("applicability")
        ct = CurrencyType(**entry)
        db.add(ct)
        db.flush()
        for audience, req_qual in applicability:
            db.add(CurrencyApplicability(
                currency_type_id=ct.id,
                applies_to=audience,
                required_qualification=req_qual,
            ))
            ca_count += 1
        ct_count += 1
    db.flush()
    return ct_count, ca_count


# ═══════════════════════════════════════════════════════════════════════════════
# Persons
# ═══════════════════════════════════════════════════════════════════════════════

_PILOTS = [
    ("Mitchell",  "James",    "LCDR", "VIPER"),
    ("Torres",    "Maria",    "LCDR", "GHOST"),
    ("Navarro",   "Carlos",   "LCDR", "RAZOR"),
    ("Bennett",   "Sarah",    "LT",   "HAMMER"),
    ("Collins",   "Derek",    "LT",   "ATLAS"),
    ("Walsh",     "Patrick",  "LT",   "FANG"),
    ("Nguyen",    "Linh",     "LT",   "NOVA"),
    ("Reyes",     "Marcus",   "LT",   "DUKE"),
    ("Foster",    "Amanda",   "LT",   "DAGGER"),
    ("Holloway",  "Tyler",    "LTJG", "SLICK"),
    ("Park",      "Jenna",    "LTJG", "SPARK"),
    ("Graham",    "Ethan",    "LTJG", "ROOK"),
]

_AIRCREW = [
    ("Davis",    "Aaron",  "AWS1"),
    ("Simmons",  "Brian",  "AWS2"),
    ("Ramos",    "Elena",  "AWS1"),
    ("Knight",   "Kevin",  "AWS3"),
    ("Larson",   "Tasha",  "AWS2"),
    ("Fleming",  "Jason",  "AWS3"),
    ("Ortega",   "Rosa",   "AWS1"),
    ("Hughes",   "Miles",  "AWS2"),
]

_STAFF = [
    ("Anderson",  "Robert",  "LCDR", Role.SDO,           None),
    ("Cooper",    "Lisa",    "LT",   Role.TRAINING_O,    None),
    ("Morgan",    "David",   "LCDR", Role.MAINT_CONTROL, None),
    ("Hawkins",   "Charles", "CDR",  Role.CO_XO,         None),
    ("admin",     "admin",   "",     Role.ADMIN,         None),
]


def seed_persons(db):
    pilots, aircrew = [], []

    for last, first, rank, callsign in _PILOTS:
        p = Person(
            last_name=last, first_name=first, rank=rank, callsign=callsign,
            role=Role.PILOT,
            username=f"{last.lower()}.{first.lower()}",
            password_hash=DEMO_PW, is_active=True,
        )
        db.add(p)
        pilots.append(p)

    for last, first, rank in _AIRCREW:
        p = Person(
            last_name=last, first_name=first, rank=rank, callsign=None,
            role=Role.AIRCREW,
            username=f"{last.lower()}.{first.lower()}",
            password_hash=DEMO_PW, is_active=True,
        )
        db.add(p)
        aircrew.append(p)

    for last, first, rank, role, callsign in _STAFF:
        username = "admin" if role == Role.ADMIN else f"{last.lower()}.{first.lower()}"
        p = Person(
            last_name=last, first_name=first, rank=rank, callsign=callsign,
            role=role, username=username,
            password_hash=DEMO_PW, is_active=True,
        )
        db.add(p)

    db.flush()
    return pilots, aircrew


# ═══════════════════════════════════════════════════════════════════════════════
# Qualifications & Currencies  (unchanged from batch-2)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_qualifications(db, pilots, aircrew):
    hac_pilots = []
    count = 0

    for pilot in pilots:
        rank = pilot.rank
        db.add(Qualification(person_id=pilot.id, qual_code="H2P",
                             qualified_date=TODAY - timedelta(days=random.randint(180, 1500))))
        count += 1

        hac_p = 0.85 if rank == "LCDR" else (0.60 if rank == "LT" else 0.15)
        if random.random() < hac_p:
            db.add(Qualification(person_id=pilot.id, qual_code="HAC",
                                 qualified_date=TODAY - timedelta(days=random.randint(90, 800))))
            hac_pilots.append(pilot)
            count += 1

        if random.random() < 0.70:
            db.add(Qualification(person_id=pilot.id, qual_code="NVG",
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 600))))
            count += 1

        special_p = 0.60 if rank == "LCDR" else 0.20
        if random.random() < special_p:
            code = random.choice(["FCP", "NSI", "INSTR"])
            db.add(Qualification(person_id=pilot.id, qual_code=code,
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 600))))
            count += 1

    for ac in aircrew:
        db.add(Qualification(person_id=ac.id, qual_code="AIRCREW_QUAL",
                             qualified_date=TODAY - timedelta(days=random.randint(90, 1000))))
        count += 1
        if random.random() < 0.50:
            db.add(Qualification(person_id=ac.id, qual_code="AWS_QUAL",
                                 qualified_date=TODAY - timedelta(days=random.randint(90, 800))))
            count += 1
        # AMCM_SO qual → unlocks ALMDS_SO and AMNS_SO currencies (B4a-1)
        if ac.last_name in ("Davis", "Ortega"):
            db.add(Qualification(person_id=ac.id, qual_code="AMCM_SO",
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 400))))
            count += 1
        # HOIST_OP_QUAL → unlocks CSTRS_WINCH currency (B4a-1)
        if ac.last_name in ("Davis", "Ramos"):
            db.add(Qualification(person_id=ac.id, qual_code="HOIST_OP_QUAL",
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 400))))
            count += 1

    db.flush()
    return hac_pilots, count


def seed_currencies(db, persons, currency_types=None):
    """
    Create a Currency row for each Wing Table B-2 type that applies to each active
    person (based on their role + quals). Randomize last_event_date within
    1.5× the periodicity window to produce a mix of current and lapsed currencies.

    `currency_types` is accepted but unused — currencies_for_person does its own
    DB query so the rows must already exist (seed_currency_types must run first).
    """
    from app.services.currency_applicability import currencies_for_person

    rows = []
    for person in persons:
        if not person.is_active:
            continue
        applicable = currencies_for_person(person, db)
        for ct in applicable:
            # Demo posture: ~88% current, ~8% expiring within 14d, ~4% lapsed.
            roll = random.random()
            if roll < 0.88:
                days_ago = random.randint(0, max(0, int(ct.periodicity_days * 0.65)))
            elif roll < 0.96:
                days_until_expire = random.randint(1, 14)
                days_ago = max(0, ct.periodicity_days - days_until_expire)
            else:
                days_ago = ct.periodicity_days + random.randint(5, 45)
            last = TODAY - timedelta(days=days_ago)
            expires = last + timedelta(days=ct.periodicity_days)
            rows.append(Currency(
                person_id=person.id,
                currency_type_id=ct.id,
                currency_code=ct.code,   # backward compat for any frontend still using it
                last_event_date=last,
                expires_date=expires,
            ))
    db.add_all(rows)
    db.flush()
    return rows
