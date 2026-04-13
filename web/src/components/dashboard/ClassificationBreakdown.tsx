"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import type { ClassificationLabel } from "@/lib/types";

const COLORS: Record<ClassificationLabel, string> = {
  obligation: "#3b82f6",
  prohibition: "#ef4444",
  permission: "#10b981",
  definition: "#8b5cf6",
  procedural: "#6b7280",
};

interface Props {
  data: Record<ClassificationLabel, number>;
}

export default function ClassificationBreakdown({ data }: Props) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));

  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
      <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Classification Breakdown</span>
      <div className="h-48 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={chartData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={2} dataKey="value">
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name as ClassificationLabel] || "#6b7280"} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ backgroundColor: "#111", border: "1px solid #333", borderRadius: "8px", fontSize: "12px" }}
              itemStyle={{ color: "#ccc" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-2">
        {chartData.map(({ name, value }) => (
          <div key={name} className="flex items-center gap-2 text-xs">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[name as ClassificationLabel] }} />
            <span className="text-gray-400 capitalize">{name}</span>
            <span className="text-gray-500 ml-auto font-mono">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
