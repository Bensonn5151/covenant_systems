import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  subtitle?: string;
  color?: string;
}

export default function StatCard({ label, value, icon, subtitle, color = "text-green-500" }: StatCardProps) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">{label}</span>
        {icon && <span className={`${color}`}>{icon}</span>}
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );
}
