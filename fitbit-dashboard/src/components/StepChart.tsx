"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface StepChartProps {
  data: { day: string; steps: number }[];
}

export default function StepChart({ data }: StepChartProps) {
  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
          <XAxis 
            dataKey="day" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#64748b', fontSize: 12 }}
            dy={10}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#64748b', fontSize: 12 }}
            tickFormatter={(value) => `${value / 1000}k`}
          />
          <Tooltip 
            cursor={{ fill: '#334155', opacity: 0.1 }}
            contentStyle={{ 
              backgroundColor: '#0f172a', 
              border: 'none',
              borderRadius: '8px',
              color: '#f8fafc',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)'
            }}
            itemStyle={{ color: '#38bdf8' }}
          />
          <Bar dataKey="steps" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={index === data.length - 1 ? '#3b82f6' : '#94a3b8'} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
