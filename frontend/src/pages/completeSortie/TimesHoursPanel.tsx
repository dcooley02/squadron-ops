import type { FlightMode } from "./helpers";
import { Section, Lbl, INPUT_CLS } from "./Section";

type Props = {
  takeoff: string;
  land: string;
  duration: string;
  flightMode: FlightMode;
  dayH: string;
  nightH: string;
  nvgH: string;
  instrH: string;
  hourMismatch: boolean;
  sumH: number;
  dur: number;
  onTakeoffChange: (v: string) => void;
  onLandChange: (v: string) => void;
  setDuration: (v: string) => void;
  setFlightMode: (m: FlightMode) => void;
  setDayH: (v: string) => void;
  setNightH: (v: string) => void;
  setNvgH: (v: string) => void;
  setInstrH: (v: string) => void;
};

export default function TimesHoursPanel({
  takeoff,
  land,
  duration,
  flightMode,
  dayH,
  nightH,
  nvgH,
  instrH,
  hourMismatch,
  sumH,
  dur,
  onTakeoffChange,
  onLandChange,
  setDuration,
  setFlightMode,
  setDayH,
  setNightH,
  setNvgH,
  setInstrH,
}: Props) {
  return (
    <Section title="Times & Hours" required defaultOpen>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Lbl>Actual Takeoff</Lbl>
          <input
            type="datetime-local"
            value={takeoff}
            onChange={(e) => onTakeoffChange(e.target.value)}
            className={INPUT_CLS}
          />
        </div>
        <div>
          <Lbl>Actual Land</Lbl>
          <input
            type="datetime-local"
            value={land}
            onChange={(e) => onLandChange(e.target.value)}
            className={INPUT_CLS}
          />
        </div>
      </div>

      <div className="flex items-end gap-4">
        <div className="w-36">
          <Lbl>Duration (hrs)</Lbl>
          <input
            type="number"
            step="0.1"
            min="0"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className={INPUT_CLS}
          />
        </div>
        <div>
          <Lbl>Flight Mode</Lbl>
          <div className="flex rounded overflow-hidden border border-slate-700">
            {(["LIVE", "SIM_TOFT"] as FlightMode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setFlightMode(m)}
                className={`px-4 py-1.5 text-sm font-medium transition-colors ${
                  flightMode === m
                    ? "bg-blue-700 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {m === "LIVE" ? "Live" : "Sim / TOFT"}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div>
        <Lbl>Hour Breakdown</Lbl>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            ["Day", dayH, setDayH],
            ["Night", nightH, setNightH],
            ["NVG", nvgH, setNvgH],
            ["Instrument", instrH, setInstrH],
          ].map(([label, val, setter]) => (
            <div key={label as string}>
              <Lbl>{label as string}</Lbl>
              <input
                type="number"
                step="0.1"
                min="0"
                value={val as string}
                onChange={(e) => (setter as (v: string) => void)(e.target.value)}
                className={INPUT_CLS}
              />
            </div>
          ))}
        </div>
        {hourMismatch && (
          <p className="text-xs text-yellow-400 mt-1.5">
            Hour breakdown ({sumH.toFixed(1)}) doesn't match duration ({dur.toFixed(1)}) — note
            that overlap between categories is normal.
          </p>
        )}
      </div>
    </Section>
  );
}
