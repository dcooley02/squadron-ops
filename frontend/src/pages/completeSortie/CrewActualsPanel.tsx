import type { Dispatch, SetStateAction } from "react";
import Badge from "../../components/Badge";
import type { CrewActual } from "./helpers";
import { Section, Lbl, INPUT_CLS } from "./Section";

type Props = {
  crewActuals: CrewActual[];
  setCrewActuals: Dispatch<SetStateAction<CrewActual[]>>;
  duration: string;
  nightH: string;
  nvgH: string;
  instrH: string;
};

export default function CrewActualsPanel({
  crewActuals,
  setCrewActuals,
  duration,
  nightH,
  nvgH,
  instrH,
}: Props) {
  return (
    <Section title="Crew Hours" required defaultOpen>
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() =>
            setCrewActuals((prev) =>
              prev.map((c) => ({
                ...c,
                hours_logged: duration,
                night_hours: nightH,
                nvg_hours: nvgH,
                actual_instrument_hours: instrH,
              }))
            )
          }
          className="text-xs text-blue-400 hover:text-blue-300"
        >
          Apply mission profile to all crew
        </button>
        <button
          type="button"
          onClick={() =>
            setCrewActuals((prev) => prev.map((c) => ({ ...c, hours_logged: duration })))
          }
          className="text-xs text-blue-400 hover:text-blue-300"
        >
          Set all to {duration}h
        </button>
      </div>
      {crewActuals.length === 0 ? (
        <p className="text-sm text-slate-500">No crew assigned to this sortie.</p>
      ) : (
        <div className="space-y-2">
          {crewActuals.map((ca, i) => (
            <div key={ca.flight_log_id} className="space-y-2 py-2 border-b border-slate-800 last:border-0">
              <div className="flex items-center gap-3">
                <Badge variant="neutral" className="shrink-0 text-xs">
                  {ca.crew_position.replace(/_/g, " ")}
                </Badge>
                <span className="text-sm text-slate-300 flex-1 min-w-0 truncate">
                  {ca.person_name}
                </span>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={ca.hours_logged}
                  onChange={(e) =>
                    setCrewActuals((prev) =>
                      prev.map((c, j) =>
                        j === i ? { ...c, hours_logged: e.target.value } : c
                      )
                    )
                  }
                  className="w-24 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
                />
                <span className="text-xs text-slate-500 w-4">h</span>
              </div>
              <div className="grid grid-cols-3 gap-2 pl-1">
                {(
                  [
                    ["Night", "night_hours"],
                    ["NVG", "nvg_hours"],
                    ["Instr", "actual_instrument_hours"],
                  ] as const
                ).map(([label, field]) => (
                  <div key={field}>
                    <Lbl>{label}</Lbl>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={ca[field]}
                      onChange={(e) =>
                        setCrewActuals((prev) =>
                          prev.map((c, j) =>
                            j === i ? { ...c, [field]: e.target.value } : c
                          )
                        )
                      }
                      className={INPUT_CLS}
                    />
                  </div>
                ))}
              </div>
              <div className="pl-1">
                <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">
                  Landings (per crew)
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                  {(
                    [
                      ["Day", "landings_day"],
                      ["Night", "landings_night"],
                      ["DVE Day", "landings_dve_day"],
                      ["DVE Nt", "landings_dve_night"],
                      ["Ship Day", "landings_shipboard_day"],
                      ["Ship Nt", "landings_shipboard_night"],
                    ] as const
                  ).map(([label, field]) => (
                    <div key={field}>
                      <Lbl>{label}</Lbl>
                      <input
                        type="number"
                        step="1"
                        min="0"
                        value={ca[field]}
                        onChange={(e) =>
                          setCrewActuals((prev) =>
                            prev.map((c, j) =>
                              j === i ? { ...c, [field]: e.target.value } : c
                            )
                          )
                        }
                        className={INPUT_CLS}
                        placeholder="0"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}
