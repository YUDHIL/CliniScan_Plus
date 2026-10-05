'use client';

import React, { useState, useEffect } from 'react';
import { UserSession, UserRole } from '../types';
import { api } from '../lib/api';
import { 
  Activity, 
  LogIn, 
  UserPlus, 
  User, 
  Stethoscope, 
  FlaskConical, 
  ShieldCheck, 
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Cpu,
  Layers,
  Search,
  ArrowRight,
  HeartPulse,
  Building,
  Check
} from 'lucide-react';

interface LandingHeroAuthProps {
  onSuccess: (user: UserSession) => void;
  cities: string[];
  specializations: string[];
  hospitals: string[];
}

export const LandingHeroAuth: React.FC<LandingHeroAuthProps> = ({
  onSuccess,
  cities = [],
  specializations = [],
  hospitals = [],
}) => {
  const [tab, setTab] = useState<'signin' | 'signup'>('signin');
  const [role, setRole] = useState<UserRole>('Patient');

  // Sign In State
  const [signInUsername, setSignInUsername] = useState('patient_demo');
  const [signInPassword, setSignInPassword] = useState('patient123');
  const [signInError, setSignInError] = useState('');
  const [loading, setLoading] = useState(false);

  // Sign Up State
  const [signUpData, setSignUpData] = useState({
    username: '',
    password: '',
    full_name: '',
    email: '',
    phone: '+91 98765 43210',
    city: 'Bangalore',
    age: 38,
    gender: 'Male',
    specialization: 'Pulmonologist',
    hospital: 'AIIMS Hospital',
    experience_years: 15,
    fees_inr: 800,
    license_no: 'LAB-BLR-2026',
  });
  const [signUpError, setSignUpError] = useState('');
  const [signUpSuccess, setSignUpSuccess] = useState('');

  // Demo Accounts
  const [demoAccounts, setDemoAccounts] = useState<UserSession[]>([]);
  const [customAccounts, setCustomAccounts] = useState<UserSession[]>([]);
  const [storageMode, setStorageMode] = useState('MongoDB');
  const [demoLoadingKey, setDemoLoadingKey] = useState<string | null>(null);
  const [demoSectionError, setDemoSectionError] = useState<string>('');

  useEffect(() => {
    loadDemoUsers();
  }, []);

  const loadDemoUsers = async () => {
    try {
      const data = await api.getDemoUsers();
      setDemoAccounts(data.demo_accounts || []);
      setCustomAccounts(data.custom_accounts || []);
      setStorageMode(data.storage_mode || 'MongoDB');
    } catch (e) {
      console.error('Failed to load demo accounts', e);
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignInError('');
    setLoading(true);
    try {
      const res = await api.login(signInUsername, signInPassword, role);
      if (res.user) {
        onSuccess(res.user);
      }
    } catch (err: any) {
      setSignInError(err.message || 'Invalid username, password, or role.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignUpError('');
    setSignUpSuccess('');
    setLoading(true);

    try {
      const extraData: any = {};
      if (role === 'Doctor') {
        extraData.specialization = signUpData.specialization;
        extraData.hospital = signUpData.hospital;
        extraData.experience_years = Number(signUpData.experience_years);
        extraData.fees_inr = Number(signUpData.fees_inr);
        extraData.rating = 5.0;
        extraData.availability = 'Available';
      } else if (role === 'Patient') {
        extraData.age = Number(signUpData.age);
        extraData.gender = signUpData.gender;
      } else if (role === 'Laboratory') {
        extraData.license_no = signUpData.license_no;
      }

      const res = await api.register({
        username: signUpData.username.trim().toLowerCase(),
        password: signUpData.password,
        role: role,
        full_name: signUpData.full_name.trim(),
        email: signUpData.email.trim(),
        phone: signUpData.phone.trim(),
        city: signUpData.city,
        extra_data: extraData,
      });

      if (res.user) {
        setSignUpSuccess('🎉 Account registered successfully! Signing in to your portal...');
        setTimeout(() => {
          onSuccess(res.user);
        }, 800);
      }
    } catch (err: any) {
      setSignUpError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoSignIn = async (username: string, pass: string, demoRole: string) => {
    setSignInError('');
    setDemoSectionError('');
    setDemoLoadingKey(username);
    try {
      const res = await api.login(username, pass, demoRole);
      if (res.user) {
        onSuccess(res.user);
        return;
      }
    } catch (err: any) {
      console.warn('API login note, using instant fallback demo session:', err);
      const fallbackUser: UserSession = {
        user_id: `DEMO-${demoRole.toUpperCase()}`,
        username: username,
        role: demoRole as UserRole,
        full_name:
          demoRole === 'Doctor'
            ? 'Dr. Yukti Chauhan'
            : demoRole === 'Laboratory'
            ? 'Apex Diagnostic Lab'
            : 'Eleanor Vance',
        email: `${username}@cliniscan.med`,
        phone: '+91 98765 43210',
        city: 'Bangalore',
        specialization: demoRole === 'Doctor' ? 'Pulmonologist' : undefined,
        hospital: demoRole === 'Doctor' ? 'AIIMS Hospital' : undefined,
        experience_years: demoRole === 'Doctor' ? 20 : undefined,
        fees_inr: demoRole === 'Doctor' ? 800 : undefined,
        rating: demoRole === 'Doctor' ? 5.0 : undefined,
        age: demoRole === 'Patient' ? 58 : undefined,
        gender: demoRole === 'Patient' ? 'Female' : undefined,
        license_no: demoRole === 'Laboratory' ? 'LAB-BLR-2026-981' : undefined,
      };
      onSuccess(fallbackUser);
    } finally {
      setDemoLoadingKey(null);
    }
  };


  return (
    <div className="space-y-10 py-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-slate-900 via-sky-950 to-indigo-950 rounded-3xl p-8 sm:p-12 text-white shadow-2xl relative overflow-hidden border border-slate-800">
        <div className="relative z-10 max-w-4xl space-y-4">
          <div className="inline-flex items-center space-x-2.5 bg-sky-500/20 backdrop-blur-md px-4 py-1.5 rounded-full text-sky-300 text-xs sm:text-sm font-extrabold uppercase tracking-wider border border-sky-400/30">
            <Activity className="w-4 h-4 text-sky-400 animate-pulse" />
            <span>Hospital-Grade Clinical AI Triage Platform</span>
          </div>

          <h1 className="font-heading text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-none text-white">
            Chest Radiograph AI Triage & <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-teal-300 to-cyan-300">Specialist Referral Network</span>
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-3xl leading-relaxed pt-2">
            Empowering <strong className="text-white">Patients</strong>, <strong className="text-white">Attending Doctors</strong>, and <strong className="text-white">Diagnostic Laboratories</strong> with sub-second YOLO11 abnormality localization, anatomical quadrant mapping, and 2,000-specialist consultation routing.
          </p>

          {/* Quick Metrics Bar */}
          <div className="pt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl">
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-3.5 text-center">
              <div className="font-heading text-2xl sm:text-3xl font-extrabold text-sky-400">YOLO11</div>
              <div className="text-xs text-slate-300 font-medium mt-0.5">Deep Learning Engine</div>
            </div>
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-3.5 text-center">
              <div className="font-heading text-2xl sm:text-3xl font-extrabold text-teal-300">10 Pathologies</div>
              <div className="text-xs text-slate-300 font-medium mt-0.5">VinBigData Classes</div>
            </div>
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-3.5 text-center">
              <div className="font-heading text-2xl sm:text-3xl font-extrabold text-indigo-300">2,000+</div>
              <div className="text-xs text-slate-300 font-medium mt-0.5">Verified Specialists</div>
            </div>
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-3.5 text-center">
              <div className="font-heading text-2xl sm:text-3xl font-extrabold text-emerald-400">&lt;250 ms</div>
              <div className="text-xs text-slate-300 font-medium mt-0.5">Inference Latency</div>
            </div>
          </div>
        </div>

        {/* Decorative Background Glow */}
        <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-10 top-1/2 -translate-y-1/2 opacity-5 hidden lg:block pointer-events-none">
          <Activity className="w-[500px] h-[500px] text-white" />
        </div>
      </div>

      {/* Main Authentication & Quick Access Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: Interactive Auth Form (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-3xl p-6 sm:p-10 border border-slate-200 shadow-xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
            <div className="flex-1 min-w-0">
              <h2 className="font-heading text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Hospital Clinical Gateway
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Select your role and sign in to access tailored clinical tools
              </p>
            </div>
            <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 text-sm font-bold shrink-0 self-start sm:self-auto shadow-inner">
              <button
                type="button"
                onClick={() => setTab('signin')}
                className={`px-5 py-2.5 rounded-xl transition cursor-pointer ${
                  tab === 'signin'
                    ? 'bg-sky-600 text-white shadow-md'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setTab('signup')}
                className={`px-5 py-2.5 rounded-xl transition cursor-pointer ${
                  tab === 'signup'
                    ? 'bg-sky-600 text-white shadow-md'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                Register
              </button>
            </div>
          </div>

          {/* Role Selection Cards */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2.5">
              Access Role Persona *
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { r: 'Patient' as UserRole, icon: User, label: 'Patient Portal', sub: 'Scan & Consult' },
                { r: 'Doctor' as UserRole, icon: Stethoscope, label: 'Attending Doctor', sub: 'Triage & Prescribe' },
                { r: 'Laboratory' as UserRole, icon: FlaskConical, label: 'Diagnostic Lab', sub: 'Intake & Route' },
              ].map(({ r, icon: Icon, label, sub }) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => {
                    setRole(r);
                    if (tab === 'signin') {
                      setSignInUsername(`${r.toLowerCase()}_demo`);
                      setSignInPassword(`${r.toLowerCase()}123`);
                    }
                  }}
                  className={`flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition text-center ${
                    role === r
                      ? 'bg-sky-50/80 border-sky-600 text-sky-900 shadow-md ring-2 ring-sky-500/20'
                      : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-2 ${
                    role === r ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-200 text-slate-600'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="font-heading font-bold text-sm leading-tight">{label}</span>
                  <span className="text-[11px] text-slate-400 mt-0.5">{sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* SIGN IN FORM */}
          {tab === 'signin' && (
            <form onSubmit={handleSignIn} className="space-y-4 pt-2">
              {signInError && (
                <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-2xl flex items-center space-x-2.5">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{signInError}</span>
                </div>
              )}

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1.5">Username *</label>
                <input
                  type="text"
                  required
                  value={signInUsername}
                  onChange={(e) => setSignInUsername(e.target.value)}
                  placeholder={`e.g. ${role.toLowerCase()}_demo`}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1.5">Password *</label>
                <input
                  type="password"
                  required
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  placeholder="Enter account password"
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-700 hover:to-sky-800 text-white font-heading font-bold text-base rounded-2xl shadow-lg shadow-sky-500/25 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <>
                    <Activity className="w-5 h-5 animate-spin" />
                    <span>Verifying Clinical Credentials...</span>
                  </>
                ) : (
                  <>
                    <LogIn className="w-5 h-5" />
                    <span>Sign In to {role} Portal ➔</span>
                  </>
                )}
              </button>
            </form>
          )}

          {/* SIGN UP FORM */}
          {tab === 'signup' && (
            <form onSubmit={handleSignUp} className="space-y-4 pt-2">
              {signUpError && (
                <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-2xl flex items-center space-x-2.5">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{signUpError}</span>
                </div>
              )}
              {signUpSuccess && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-2xl flex items-center space-x-2.5">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <span>{signUpSuccess}</span>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Username *</label>
                  <input
                    type="text"
                    required
                    value={signUpData.username}
                    onChange={(e) => setSignUpData({ ...signUpData, username: e.target.value })}
                    placeholder="e.g. dr_smith or patient_jane"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Password *</label>
                  <input
                    type="password"
                    required
                    value={signUpData.password}
                    onChange={(e) => setSignUpData({ ...signUpData, password: e.target.value })}
                    placeholder="Create password"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    {role === 'Doctor' ? 'Doctor Full Name (with Dr.) *' : role === 'Laboratory' ? 'Laboratory Center Name *' : 'Patient Full Name *'}
                  </label>
                  <input
                    type="text"
                    required
                    value={signUpData.full_name}
                    onChange={(e) => setSignUpData({ ...signUpData, full_name: e.target.value })}
                    placeholder={role === 'Doctor' ? 'Dr. Sarah Connor' : 'Jane Doe'}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Email Address *</label>
                  <input
                    type="email"
                    required
                    value={signUpData.email}
                    onChange={(e) => setSignUpData({ ...signUpData, email: e.target.value })}
                    placeholder="name@hospital.med"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Contact Phone *</label>
                  <input
                    type="text"
                    required
                    value={signUpData.phone}
                    onChange={(e) => setSignUpData({ ...signUpData, phone: e.target.value })}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">City Location *</label>
                  <select
                    value={signUpData.city}
                    onChange={(e) => setSignUpData({ ...signUpData, city: e.target.value })}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium"
                  >
                    {cities.filter(c => c !== 'All Cities').map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Role-Specific Additions */}
              {role === 'Doctor' && (
                <div className="p-4 bg-sky-50/80 border border-sky-200 rounded-2xl space-y-3">
                  <div className="text-xs font-bold text-sky-900">🩺 Specialist Practice Profile</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Specialization *</label>
                      <select
                        value={signUpData.specialization}
                        onChange={(e) => setSignUpData({ ...signUpData, specialization: e.target.value })}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs"
                      >
                        {specializations.filter(s => s !== 'All Specializations').map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Hospital Network *</label>
                      <select
                        value={signUpData.hospital}
                        onChange={(e) => setSignUpData({ ...signUpData, hospital: e.target.value })}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs"
                      >
                        {hospitals.filter(h => h !== 'All Hospitals').map(h => (
                          <option key={h} value={h}>{h}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Experience (Years)</label>
                      <input
                        type="number"
                        value={signUpData.experience_years}
                        onChange={(e) => setSignUpData({ ...signUpData, experience_years: parseInt(e.target.value) || 15 })}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Consultation Fee (₹)</label>
                      <input
                        type="number"
                        step="50"
                        value={signUpData.fees_inr}
                        onChange={(e) => setSignUpData({ ...signUpData, fees_inr: parseInt(e.target.value) || 800 })}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}

              {role === 'Patient' && (
                <div className="grid grid-cols-2 gap-3 p-4 bg-indigo-50/80 border border-indigo-200 rounded-2xl">
                  <div>
                    <label className="block text-xs font-bold text-indigo-900 mb-1">Age</label>
                    <input
                      type="number"
                      value={signUpData.age}
                      onChange={(e) => setSignUpData({ ...signUpData, age: parseInt(e.target.value) || 35 })}
                      className="w-full px-3 py-2 bg-white border border-indigo-300 rounded-lg text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-indigo-900 mb-1">Gender</label>
                    <select
                      value={signUpData.gender}
                      onChange={(e) => setSignUpData({ ...signUpData, gender: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-indigo-300 rounded-lg text-xs"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>
              )}

              {role === 'Laboratory' && (
                <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-2xl">
                  <label className="block text-xs font-bold text-emerald-900 mb-1">Lab Accreditation Number *</label>
                  <input
                    type="text"
                    value={signUpData.license_no}
                    onChange={(e) => setSignUpData({ ...signUpData, license_no: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-emerald-300 rounded-lg text-xs"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-700 hover:to-sky-800 text-white font-heading font-bold text-base rounded-2xl shadow-lg shadow-sky-500/25 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {loading ? 'Creating Account & Syncing Network...' : `Register New ${role} Account ➔`}
              </button>
            </form>
          )}
        </div>

        {/* Right Side: 1-Click Quick Demo Accounts (5 Cols) */}
        <div className="lg:col-span-5 bg-gradient-to-b from-slate-900 to-slate-950 text-white rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-xl space-y-6">
          <div>
            <div className="flex items-center space-x-2 text-amber-400 mb-1.5">
              <Sparkles className="w-5 h-5 fill-amber-400" />
              <h3 className="font-heading font-bold text-lg text-white">Instant 1-Click Role Logins</h3>
            </div>
            <p className="text-xs text-slate-400">
              Test any clinical role immediately with pre-loaded medical records and sample radiographs:
            </p>
          </div>

          {demoSectionError && (
            <div className="p-3.5 bg-red-950/80 border border-red-500/50 text-red-200 text-xs rounded-2xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
              <span>{demoSectionError}</span>
            </div>
          )}

          <div className="space-y-3.5">
            {/* Patient Demo Card */}
            <button
              type="button"
              disabled={loading || demoLoadingKey !== null}
              onClick={() => handleQuickDemoSignIn('patient_demo', 'patient123', 'Patient')}
              className="w-full text-left p-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-indigo-400/50 transition group flex items-center justify-between cursor-pointer disabled:opacity-70"
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-12 h-12 rounded-2xl bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 flex items-center justify-center group-hover:scale-105 transition flex-shrink-0">
                  {demoLoadingKey === 'patient_demo' ? (
                    <Activity className="w-6 h-6 animate-spin text-indigo-300" />
                  ) : (
                    <User className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <div className="font-heading font-bold text-sm text-white group-hover:text-indigo-300 transition">
                    Eleanor Vance
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Patient Persona &bull; Scan & Consult</div>
                </div>
              </div>
              <span className="text-xs font-bold text-indigo-400 bg-indigo-950/60 px-3 py-1 rounded-full border border-indigo-500/30 flex items-center space-x-1">
                {demoLoadingKey === 'patient_demo' ? (
                  <span>Entering...</span>
                ) : (
                  <span>Patient ➔</span>
                )}
              </span>
            </button>

            {/* Doctor Demo Card */}
            <button
              type="button"
              disabled={loading || demoLoadingKey !== null}
              onClick={() => handleQuickDemoSignIn('doctor_demo', 'doctor123', 'Doctor')}
              className="w-full text-left p-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-sky-400/50 transition group flex items-center justify-between cursor-pointer disabled:opacity-70"
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-12 h-12 rounded-2xl bg-sky-600/30 border border-sky-500/40 text-sky-300 flex items-center justify-center group-hover:scale-105 transition flex-shrink-0">
                  {demoLoadingKey === 'doctor_demo' ? (
                    <Activity className="w-6 h-6 animate-spin text-sky-300" />
                  ) : (
                    <Stethoscope className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <div className="font-heading font-bold text-sm text-white group-hover:text-sky-300 transition">
                    Dr. Yukti Chauhan
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Pulmonologist &bull; AIIMS Hospital</div>
                </div>
              </div>
              <span className="text-xs font-bold text-sky-400 bg-sky-950/60 px-3 py-1 rounded-full border border-sky-500/30 flex items-center space-x-1">
                {demoLoadingKey === 'doctor_demo' ? (
                  <span>Entering...</span>
                ) : (
                  <span>Doctor ➔</span>
                )}
              </span>
            </button>

            {/* Lab Demo Card */}
            <button
              type="button"
              disabled={loading || demoLoadingKey !== null}
              onClick={() => handleQuickDemoSignIn('lab_demo', 'lab123', 'Laboratory')}
              className="w-full text-left p-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-400/50 transition group flex items-center justify-between cursor-pointer disabled:opacity-70"
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-12 h-12 rounded-2xl bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 flex items-center justify-center group-hover:scale-105 transition flex-shrink-0">
                  {demoLoadingKey === 'lab_demo' ? (
                    <Activity className="w-6 h-6 animate-spin text-emerald-300" />
                  ) : (
                    <FlaskConical className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <div className="font-heading font-bold text-sm text-white group-hover:text-emerald-300 transition">
                    Apex Diagnostic Lab
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Facility License: LAB-BLR-2026-981</div>
                </div>
              </div>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950/60 px-3 py-1 rounded-full border border-emerald-500/30 flex items-center space-x-1">
                {demoLoadingKey === 'lab_demo' ? (
                  <span>Entering...</span>
                ) : (
                  <span>Laboratory ➔</span>
                )}
              </span>
            </button>
          </div>

          {/* Registered Custom Accounts */}
          {customAccounts.length > 0 && (
            <div className="pt-4 border-t border-slate-800">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
                Your Custom Registered Accounts ({customAccounts.length}):
              </div>
              <div className="max-h-40 overflow-y-auto space-y-2 pr-1">
                {customAccounts.map((cu) => (
                  <button
                    key={cu.username}
                    type="button"
                    onClick={() => {
                      setDemoLoadingKey(cu.username);
                      onSuccess(cu);
                    }}
                    className="w-full text-left p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-slate-800 text-xs flex justify-between items-center transition cursor-pointer"
                  >
                    <div>
                      <div className="font-bold text-white truncate">{cu.full_name}</div>
                      <div className="text-[11px] text-slate-400">@{cu.username} &bull; {cu.role}</div>
                    </div>
                    <span className="text-sky-400 text-xs font-bold">Launch ➔</span>
                  </button>
                ))}
              </div>
            </div>
          )}


          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
            <span>Audit Engine: {storageMode}</span>
            <span>VinBigData Chest X-ray</span>
          </div>
        </div>
      </div>
    </div>
  );
};
