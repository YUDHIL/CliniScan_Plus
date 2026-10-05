'use client';

import React from 'react';
import { UserSession } from '../types';
import { 
  Activity, 
  User, 
  Stethoscope, 
  FlaskConical, 
  LogOut, 
  LogIn, 
  ShieldCheck,
  ChevronDown,
  Sparkles,
  HeartPulse,
  PhoneCall
} from 'lucide-react';

interface NavbarProps {
  user: UserSession | null;
  onOpenAuth: () => void;
  onSignOut: () => void;
  activeDoctorPersona?: string;
  onSelectDoctorPersona?: (name: string) => void;
  allDoctors?: UserSession[];
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onOpenAuth,
  onSignOut,
  activeDoctorPersona,
  onSelectDoctorPersona,
  allDoctors = []
}) => {
  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-xl border-b border-slate-200 shadow-sm w-full">
      <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-10">
        <div className="flex justify-between items-center h-24">
          {/* Brand Logo & Hospital Title */}
          <div className="flex items-center space-x-4 cursor-pointer" onClick={() => !user && onOpenAuth()}>
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-600 via-sky-500 to-cyan-400 flex items-center justify-center text-white shadow-xl shadow-sky-500/30 flex-shrink-0">
              <Activity className="w-8 h-8 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <span className="font-heading font-black text-3xl sm:text-4xl text-slate-900 tracking-tight">
                  CliniScan<span className="text-sky-600">+</span>
                </span>
                <span className="bg-gradient-to-r from-sky-600 to-indigo-600 text-white text-xs font-black px-3.5 py-1 rounded-full uppercase tracking-wider shadow-sm">
                  YOLO11 AI CLINICAL SUITE
                </span>
              </div>
              <p className="text-sm font-bold text-slate-500 hidden sm:block mt-0.5">
                Hospital-Grade Chest Radiograph AI Triage, Abnormality Localization & 2,000+ Specialist Network
              </p>
            </div>
          </div>

          {/* Right Controls & User Persona */}
          <div className="flex items-center space-x-4 sm:space-x-6">
            {/* Clinical Hotline Badge */}
            <div className="hidden xl:flex items-center space-x-2.5 bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-2xl text-xs font-bold text-slate-700">
              <PhoneCall className="w-4 h-4 text-emerald-600 animate-bounce" />
              <span>Hospital AI Helpdesk: <strong className="text-slate-900">+91 800-CLINISCAN</strong></span>
            </div>

            {user ? (
              <div className="flex items-center space-x-3 sm:space-x-5">
                {/* Doctor Persona Switcher (If Doctor) */}
                {user.role === 'Doctor' && onSelectDoctorPersona && (
                  <div className="hidden lg:flex items-center bg-sky-50 border-2 border-sky-300 rounded-2xl px-4 py-2.5 text-xs sm:text-sm font-black shadow-sm">
                    <Stethoscope className="w-5 h-5 text-sky-600 mr-2" />
                    <span className="text-slate-500 mr-2 font-bold">Attending:</span>
                    <select
                      value={activeDoctorPersona || user.full_name}
                      onChange={(e) => onSelectDoctorPersona(e.target.value)}
                      className="bg-transparent text-sky-950 font-black outline-none cursor-pointer text-sm"
                    >
                      <option value={user.full_name}>{user.full_name} (Signed In)</option>
                      {allDoctors
                        .filter(d => d.full_name !== user.full_name)
                        .map(d => (
                          <option key={d.username} value={d.full_name}>
                            {d.full_name} ({d.hospital || 'AIIMS'})
                          </option>
                        ))}
                    </select>
                  </div>
                )}

                {/* User Session Profile Pill */}
                <div className="flex items-center space-x-3.5 bg-slate-100/90 border-2 border-slate-200/90 rounded-2xl px-5 py-2.5 shadow-sm">
                  <div className={`w-11 h-11 rounded-2xl flex items-center justify-center text-white text-base font-extrabold shadow-md ${
                    user.role === 'Doctor' ? 'bg-sky-600 shadow-sky-600/30' : user.role === 'Laboratory' ? 'bg-emerald-600 shadow-emerald-600/30' : 'bg-indigo-600 shadow-indigo-600/30'
                  }`}>
                    {user.role === 'Doctor' ? <Stethoscope className="w-6 h-6" /> : user.role === 'Laboratory' ? <FlaskConical className="w-6 h-6" /> : <User className="w-6 h-6" />}
                  </div>
                  <div className="text-left hidden md:block">
                    <div className="text-base font-black text-slate-900 leading-tight">{user.full_name}</div>
                    <div className="text-xs font-black text-sky-700 uppercase tracking-wider">{user.role} Portal</div>
                  </div>
                </div>

                {/* Quick Role Switcher */}
                <button
                  onClick={onOpenAuth}
                  className="hidden sm:inline-flex items-center space-x-2 bg-gradient-to-r from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100 text-amber-900 text-xs sm:text-sm font-extrabold px-4 py-2.5 rounded-2xl border-2 border-amber-300 transition shadow-sm active:scale-95"
                >
                  <Sparkles className="w-4 h-4 text-amber-600 fill-amber-500" />
                  <span>Switch Role</span>
                </button>

                {/* Sign Out Button */}
                <button
                  onClick={onSignOut}
                  className="inline-flex items-center justify-center p-3 rounded-2xl text-slate-500 hover:text-red-600 hover:bg-red-50 border-2 border-slate-200 hover:border-red-200 transition"
                  title="Sign Out"
                >
                  <LogOut className="w-6 h-6" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="inline-flex items-center space-x-2.5 bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-700 hover:to-sky-800 text-white text-base font-black px-7 py-3 rounded-2xl shadow-xl shadow-sky-500/30 transition active:scale-95 cursor-pointer"
              >
                <LogIn className="w-6 h-6" />
                <span>Hospital Sign In ➔</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
