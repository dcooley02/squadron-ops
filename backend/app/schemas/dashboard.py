from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_personnel: int
    total_pilots: int
    total_aircrew: int
    aircraft_total: int
    aircraft_fmc_count: int
    aircraft_pmc_count: int
    aircraft_nmc_count: int
    fmc_rate: float
    open_discrepancies_count: int
    currencies_expiring_14d_count: int
    currencies_expired_count: int
    sorties_last_30_days: int
    total_hours_last_30_days: float
