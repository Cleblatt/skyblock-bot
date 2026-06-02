"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Footprints, HeartPulse, MoonStar, Flame, AlertCircle } from "lucide-react";
import SummaryCard from "@/components/SummaryCard";
import StepChart from "@/components/StepChart";

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/fitbit/activity")
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Hello, {session?.user?.name?.split(' ')[0] || 'Guest'}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Here's your daily health summary.
          </p>
        </div>
        
        {data?.mockData && (
          <div className="flex items-center gap-2 px-4 py-2 bg-amber-100 text-amber-800 dark:bg-amber-500/10 dark:text-amber-400 rounded-lg text-sm font-medium border border-amber-200 dark:border-amber-500/20">
            <AlertCircle size={16} />
            <span>Using mock data. Setup tokens for real metrics.</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard 
          title="Daily Steps" 
          value={data?.today?.steps?.toLocaleString()} 
          subtitle="/ 10,000"
          icon={<Footprints size={24} />} 
          trend="+12% vs yesterday"
          trendPositive={true}
        />
        <SummaryCard 
          title="Current Heart Rate" 
          value={data?.today?.heartRate?.current} 
          subtitle="bpm"
          icon={<HeartPulse size={24} />} 
          trend={`Resting: ${data?.today?.heartRate?.resting} bpm`}
        />
        <SummaryCard 
          title="Sleep Duration" 
          value={data?.today?.sleep?.split(' ')[0]} 
          subtitle={data?.today?.sleep?.split(' ')[1]}
          icon={<MoonStar size={24} />} 
          trend="-30m vs avg"
          trendPositive={false}
        />
        <SummaryCard 
          title="Calories Burned" 
          value={data?.today?.calories?.toLocaleString()} 
          subtitle="kcal"
          icon={<Flame size={24} />} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Activity Overview</h2>
            <select className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm rounded-lg px-3 py-1.5 outline-none">
              <option>Last 7 Days</option>
              <option>This Month</option>
            </select>
          </div>
          {data?.history && <StepChart data={data.history} />}
        </div>
        
        <div className="rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 p-6 shadow-sm text-white relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-20 -mt-20"></div>
          
          <div className="relative z-10">
            <h2 className="text-xl font-bold mb-2">Weekly Goal</h2>
            <p className="text-blue-100 text-sm">You are on track to beat your weekly step goal. Keep it up!</p>
          </div>
          
          <div className="relative z-10 mt-8">
            <div className="flex justify-between items-end mb-2">
              <span className="text-4xl font-bold tracking-tight">72%</span>
              <span className="text-sm font-medium text-blue-200">50k / 70k steps</span>
            </div>
            <div className="w-full bg-black/20 rounded-full h-3">
              <div className="bg-white rounded-full h-3" style={{ width: '72%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
