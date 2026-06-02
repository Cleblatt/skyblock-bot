"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import { Activity, LogOut, LogIn } from "lucide-react";

export default function NavBar() {
  const { data: session } = useSession();

  return (
    <nav className="w-full border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 p-2 rounded-xl text-white">
            <Activity size={24} />
          </div>
          <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
            FitDash
          </span>
        </div>
        
        <div>
          {session ? (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                {session.user?.image && (
                  <img 
                    src={session.user.image} 
                    alt="Profile" 
                    className="w-9 h-9 rounded-full ring-2 ring-blue-500/30"
                  />
                )}
                <span className="font-medium hidden sm:block text-slate-700 dark:text-slate-300">
                  {session.user?.name}
                </span>
              </div>
              <button 
                onClick={() => signOut()}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 transition-colors text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                <LogOut size={16} />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <button 
              onClick={() => signIn("google")}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors shadow-lg shadow-blue-500/20 text-sm font-medium"
            >
              <LogIn size={16} />
              Login with Google
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
