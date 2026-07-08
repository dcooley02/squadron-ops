import { describe, expect, it } from "vitest";
import {
  addHoursToStr,
  buildFlightLogActuals,
  durationBetween,
  emptyCrewLandings,
  hasPerCrewLandings,
  roleHoursForPosition,
  sumCrewLandings,
  toInputDT,
  type CrewActual,
} from "./helpers";

const baseCrew = (over: Partial<CrewActual> = {}): CrewActual => ({
  flight_log_id: 1,
  person_name: "TEST",
  crew_position: "HAC",
  hours_logged: "2.0",
  night_hours: "0.5",
  nvg_hours: "0",
  actual_instrument_hours: "0",
  ...emptyCrewLandings(),
  ...over,
});


describe("completeSortie helpers", () => {
  it("toInputDT truncates ISO to datetime-local", () => {
    expect(toInputDT("2026-07-08T14:30:00Z")).toBe("2026-07-08T14:30");
    expect(toInputDT(null)).toBe("");
  });

  it("addHoursToStr and durationBetween round-trip", () => {
    const land = addHoursToStr("2026-07-08T10:00", 2.5);
    expect(land).toBe("2026-07-08T12:30");
    expect(durationBetween("2026-07-08T10:00", land)).toBe(2.5);
  });

  it("roleHoursForPosition maps HAC and aircrew", () => {
    expect(roleHoursForPosition("HAC", 1.5)).toEqual({
      ac_commander_hours: 1.5,
      first_pilot_hours: 1.5,
    });
    expect(roleHoursForPosition("AWS", 1.0)).toEqual({ special_crew_time_hours: 1.0 });
  });

  it("buildFlightLogActuals derives role hours", () => {
    const rows = buildFlightLogActuals(
      [baseCrew()],
      { nightH: "0", nvgH: "0", instrH: "0" },
      "P200"
    );
    expect(rows).toHaveLength(1);
    expect(rows[0].hours_logged).toBe(2);
    expect(rows[0].ac_commander_hours).toBe(2);
    expect(rows[0].syllabus_event_completed).toBe("P200");
    expect(rows[0].landings_day).toBeUndefined();
  });

  it("includes per-crew landings when any landing field is set", () => {
    const crew = [
      baseCrew({ landings_day: "2", landings_night: "1" }),
      baseCrew({
        flight_log_id: 2,
        crew_position: "H2P",
        landings_day: "1",
      }),
    ];
    expect(hasPerCrewLandings(crew)).toBe(true);
    expect(sumCrewLandings(crew).landings_day).toBe(3);
    const rows = buildFlightLogActuals(crew, { nightH: "0", nvgH: "0", instrH: "0" }, null);
    expect(rows[0].landings_day).toBe(2);
    expect(rows[1].landings_day).toBe(1);
  });
});
