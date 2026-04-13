"use client";

interface Props {
  score: number;
}

export default function ComplianceHealthScore({ score }: Props) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6 flex flex-col items-center">
      <span className="text-xs text-gray-500 font-mono uppercase tracking-wider mb-4">Compliance Health</span>
      <div className="relative w-44 h-44">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={radius} stroke="#1f2937" strokeWidth="10" fill="none" />
          <circle
            cx="80" cy="80" r={radius}
            stroke={color}
            strokeWidth="10"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{score}%</span>
          <span className="text-xs text-gray-500">score</span>
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-3 text-center">Based on risk analysis across all regulatory sections</p>
    </div>
  );
}
