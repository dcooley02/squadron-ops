import clsx from "clsx";

interface RateRingProps {
  rate: number;     // percentage, 0-100
  label: string;
}

export default function RateRing({ rate, label }: RateRingProps) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (rate / 100) * circumference;

  // Color: green ≥ 75%, yellow ≥ 50%, red below
  const color =
    rate >= 75 ? "text-green-500" :
    rate >= 50 ? "text-yellow-500" : "text-red-500";

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
          {/* Background ring */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-slate-800"
          />
          {/* Progress ring */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={clsx("transition-all duration-700", color)}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={clsx("text-3xl font-semibold", color)}>
            {rate.toFixed(1)}%
          </div>
        </div>
      </div>
      <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mt-2">
        {label}
      </div>
    </div>
  );
}