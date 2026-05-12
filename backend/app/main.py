from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import persons, aircraft, sorties, dashboard, scheduling, logging as flight_logging, syllabus, currency, maintenance

app = FastAPI(title="HSC Squadron Ops")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(persons.router)
app.include_router(aircraft.router)
app.include_router(sorties.router)
app.include_router(dashboard.router)
app.include_router(scheduling.router)
app.include_router(flight_logging.router)
app.include_router(syllabus.router)
app.include_router(currency.router)
app.include_router(maintenance.router)


@app.get("/health")
def health():
    return {"status": "ok"}