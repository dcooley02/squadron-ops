"""CBR task options and capability area configs."""
from app.catalogs.cbr_enclosure2 import AREA_CONFIG_SPECS, CBR_TASK_SPECS
from app.models.models import CbrTaskOption, CapabilityAreaConfig

# ═══════════════════════════════════════════════════════════════════════════════
# CBR Task Options / Capability area configs (Enclosure 2-shaped catalog)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_capability_area_configs(db):
    count = 0
    for area, label, t1, t2, currencies, quals in AREA_CONFIG_SPECS:
        db.add(CapabilityAreaConfig(
            capability_area=area,
            label=label,
            t1_recency_days=t1,
            t2_recency_days=t2,
            currency_codes=currencies,
            min_qual_codes=quals,
        ))
        count += 1
    db.flush()
    return count


def seed_cbr_task_options(db):
    count = 0
    for spec in CBR_TASK_SPECS:
        db.add(CbrTaskOption(
            code=spec.code,
            capability_area=spec.capability_area,
            description=spec.description,
            crew_scope=spec.crew_scope,
            sim_eligible=spec.sim_eligible,
            min_time_hours=spec.min_time_hours,
            confers_codes=spec.confers_codes,
            moe_notes=spec.moe_notes,
            mop_notes=spec.mop_notes,
            is_active=True,
            is_anchor_task=spec.is_anchor_task,
        ))
        count += 1
    db.flush()
    return count
