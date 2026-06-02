import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";

export async function GET() {
  const session: any = await getServerSession();

  // For now, always return mock data so you can see the UI working
  // Real implementation will check session.provider and session.accessToken
  return NextResponse.json({
    mockData: true,
    today: {
      steps: 8432,
      heartRate: { current: 72, resting: 65 },
      sleep: "7h 24m",
      calories: 2150
    },
    history: [
      { day: "Mon", steps: 7200 },
      { day: "Tue", steps: 8100 },
      { day: "Wed", steps: 9500 },
      { day: "Thu", steps: 6400 },
      { day: "Fri", steps: 10200 },
      { day: "Sat", steps: 12500 },
      { day: "Sun", steps: 8432 },
    ]
  });
}
