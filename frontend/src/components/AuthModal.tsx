'use client';

import React, { useState, useEffect } from 'react';
import { UserSession, UserRole } from '../types';
import { api } from '../lib/api';
import { 
  X, 
  LogIn, 
  UserPlus, 
  User, 
  Stethoscope, 
  FlaskConical, 
  ShieldCheck, 
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Activity
} from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: UserSession) => void;
  cities: string[];
  specializations: string[];
  hospitals: string[];
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  cities,
  specializations,
  hospitals,
}) => {
  const [tab, setTab] = useState<'signin' | 'signup'>('signin');
  const [role, setRole] = useState<UserRole>('Patient');

  // Sign In State
  const [signInUsername, setSignInUsername] = useState('');
  const [signInPassword, setSignInPassword] = useState('');
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
    hospital: 'AIIMS',
    experience_years: 15,
    fees_inr: 800,
    license_no: 'LAB-BLR-2026',
  });
  const [signUpError, setSignUpError] = useState('');
  const [signUpSuccess, setSignUpSuccess] = useState('');

  // Demo Accounts
  const [demoAccounts, setDemoAccounts] = useState<UserSession[]>([]);
  const [customAccounts, setCustomAccounts] = useState<UserSession[]>([]);
  const [demoLoadingKey, setDemoLoadingKey] = useState<string | null>(null);
  const [demoSectionError, setDemoSectionError] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      loadDemoUsers();
    }
  }, [isOpen]);

  const loadDemoUsers = async () => {
    try {
      const data = await api.getDemoUsers();
      setDemoAccounts(data.demo_accounts || []);
      setCustomAccounts(data.custom_accounts || []);
    } catch (e) {
      console.error('Failed to load demo accounts', e);
    }
  };

  if (!isOpen) return null;

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignInError('');
    setLoading(true);
    try {
      const res = await api.login(signInUsername, signInPassword, role);
      if (res.user) {
        onSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setSignInError(err.message || 'Invalid username or password.');
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
        setSignUpSuccess('Account registered successfully! Signing in...');
        setTimeout(() => {
          onSuccess(res.user);
          onClose();
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
        onClose();
        return;
      }
    } catch (err: any) {
      console.warn('API login note, fallback to demo session:', err);
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
      onClose();
    } finally {
      setDemoLoadingKey(null);
    }
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8">
        {/* Header Bar */}
        <div className="bg-gradient-to-r from-sky-700 via-sky-600 to-sky-800 text-white px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-6 h-6 text-sky-200" />
            <div>
              <h3 className="font-heading font-bold text-lg leading-tight">CliniScan+ Hospital Access Portal</h3>
              <p className="text-xs text-sky-100 font-medium">Multi-Role Clinical Authentication & Verification</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-sky-200 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12">
          {/* Main Form Area (7 Cols) */}
          <div className="lg:col-span-7 p-6 sm:p-8 border-b lg:border-b-0 lg:border-r border-slate-200">
            {/* Tabs */}
            <div className="flex border-b border-slate-200 mb-6">
              <button
                onClick={() => setTab('signin')}
                className={`flex-1 pb-3 text-sm font-bold flex items-center justify-center space-x-2 border-b-2 transition ${
                  tab === 'signin'
                    ? 'border-sky-600 text-sky-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </button>
              <button
                onClick={() => setTab('signup')}
                className={`flex-1 pb-3 text-sm font-bold flex items-center justify-center space-x-2 border-b-2 transition ${
                  tab === 'signup'
                    ? 'border-sky-600 text-sky-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <UserPlus className="w-4 h-4" />
                <span>Create Account</span>
              </button>
            </div>

            {/* Role Switcher */}
            <div className="mb-5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Select Your Role
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { r: 'Patient' as UserRole, icon: User, label: 'Patient', color: 'text-indigo-600' },
                  { r: 'Doctor' as UserRole, icon: Stethoscope, label: 'Doctor', color: 'text-sky-600' },
                  { r: 'Laboratory' as UserRole, icon: FlaskConical, label: 'Laboratory', color: 'text-emerald-600' },
                ].map(({ r, icon: Icon, label, color }) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-bold transition ${
                      role === r
                        ? 'bg-sky-50 border-sky-500 text-sky-900 shadow-sm'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Icon className={`w-5 h-5 mb-1 ${role === r ? 'text-sky-600' : 'text-slate-400'}`} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* TAB 1: SIGN IN */}
            {tab === 'signin' && (
              <form onSubmit={handleSignIn} className="space-y-4">
                {signInError && (
                  <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{signInError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Username *</label>
                  <input
                    type="text"
                    required
                    value={signInUsername}
                    onChange={(e) => setSignInUsername(e.target.value)}
                    placeholder={`e.g. ${role.toLowerCase()}_demo`}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Password *</label>
                  <input
                    type="password"
                    required
                    value={signInPassword}
                    onChange={(e) => setSignInPassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold text-sm rounded-xl shadow-md shadow-sky-500/20 transition active:scale-98 disabled:opacity-50"
                >
                  {loading ? 'Authenticating...' : `Sign In as ${role} ➔`}
                </button>
              </form>
            )}

            {/* TAB 2: SIGN UP */}
            {tab === 'signup' && (
              <form onSubmit={handleSignUp} className="space-y-3.5">
                {signUpError && (
                  <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{signUpError}</span>
                  </div>
                )}
                {signUpSuccess && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                    <span>{signUpSuccess}</span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Username *</label>
                    <input
                      type="text"
                      required
                      value={signUpData.username}
                      onChange={(e) => setSignUpData({ ...signUpData, username: e.target.value })}
                      placeholder="e.g. john_doe"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
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
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      {role === 'Doctor' ? 'Full Name (with Dr.) *' : role === 'Laboratory' ? 'Lab Name *' : 'Full Name *'}
                    </label>
                    <input
                      type="text"
                      required
                      value={signUpData.full_name}
                      onChange={(e) => setSignUpData({ ...signUpData, full_name: e.target.value })}
                      placeholder={role === 'Doctor' ? 'Dr. Name' : 'Full Name'}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Email *</label>
                    <input
                      type="email"
                      required
                      value={signUpData.email}
                      onChange={(e) => setSignUpData({ ...signUpData, email: e.target.value })}
                      placeholder="name@hospital.med"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Phone Number *</label>
                    <input
                      type="text"
                      required
                      value={signUpData.phone}
                      onChange={(e) => setSignUpData({ ...signUpData, phone: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">City Location *</label>
                    <select
                      value={signUpData.city}
                      onChange={(e) => setSignUpData({ ...signUpData, city: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
                    >
                      {cities.filter(c => c !== 'All Cities').map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Role Specific Extra Inputs */}
                {role === 'Doctor' && (
                  <div className="grid grid-cols-2 gap-3 p-3 bg-sky-50 border border-sky-200 rounded-xl">
                    <div>
                      <label className="block text-[11px] font-bold text-sky-800 mb-1">Specialization *</label>
                      <select
                        value={signUpData.specialization}
                        onChange={(e) => setSignUpData({ ...signUpData, specialization: e.target.value })}
                        className="w-full px-2.5 py-1.5 bg-white border border-sky-300 rounded-md text-xs"
                      >
                        {specializations.filter(s => s !== 'All Specializations').map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-sky-800 mb-1">Hospital Network *</label>
                      <select
                        value={signUpData.hospital}
                        onChange={(e) => setSignUpData({ ...signUpData, hospital: e.target.value })}
                        className="w-full px-2.5 py-1.5 bg-white border border-sky-300 rounded-md text-xs"
                      >
                        {hospitals.filter(h => h !== 'All Hospitals').map(h => (
                          <option key={h} value={h}>{h}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-sky-800 mb-1">Experience (Years)</label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={signUpData.experience_years}
                        onChange={(e) => setSignUpData({ ...signUpData, experience_years: parseInt(e.target.value) || 10 })}
                        className="w-full px-2.5 py-1.5 bg-white border border-sky-300 rounded-md text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-sky-800 mb-1">Consultation Fee (₹)</label>
                      <input
                        type="number"
                        min="100"
                        max="5000"
                        step="50"
                        value={signUpData.fees_inr}
                        onChange={(e) => setSignUpData({ ...signUpData, fees_inr: parseInt(e.target.value) || 800 })}
                        className="w-full px-2.5 py-1.5 bg-white border border-sky-300 rounded-md text-xs"
                      />
                    </div>
                  </div>
                )}

                {role === 'Patient' && (
                  <div className="grid grid-cols-2 gap-3 p-3 bg-indigo-50 border border-indigo-200 rounded-xl">
                    <div>
                      <label className="block text-[11px] font-bold text-indigo-800 mb-1">Age</label>
                      <input
                        type="number"
                        min="1"
                        max="120"
                        value={signUpData.age}
                        onChange={(e) => setSignUpData({ ...signUpData, age: parseInt(e.target.value) || 30 })}
                        className="w-full px-2.5 py-1.5 bg-white border border-indigo-300 rounded-md text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-indigo-800 mb-1">Gender</label>
                      <select
                        value={signUpData.gender}
                        onChange={(e) => setSignUpData({ ...signUpData, gender: e.target.value })}
                        className="w-full px-2.5 py-1.5 bg-white border border-indigo-300 rounded-md text-xs"
                      >
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                )}

                {role === 'Laboratory' && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                    <label className="block text-[11px] font-bold text-emerald-800 mb-1">Lab Accreditation Number *</label>
                    <input
                      type="text"
                      value={signUpData.license_no}
                      onChange={(e) => setSignUpData({ ...signUpData, license_no: e.target.value })}
                      placeholder="LAB-BLR-2026"
                      className="w-full px-2.5 py-1.5 bg-white border border-emerald-300 rounded-md text-xs"
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow-md shadow-sky-500/20 transition active:scale-98 disabled:opacity-50"
                >
                  {loading ? 'Registering...' : `Create ${role} Account & Sync ➔`}
                </button>
              </form>
            )}
          </div>

          {/* Side Area: Quick Demo Accounts (5 Cols) */}
          <div className="lg:col-span-5 p-6 bg-slate-50 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 text-sky-800 mb-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <h4 className="font-heading font-bold text-sm">1-Click Quick Demo Sign In</h4>
              </div>
              <p className="text-xs text-slate-500 mb-4">
                Instantly switch roles to test full clinical and diagnostic workflows without entering credentials:
              </p>

              {demoSectionError && (
                <div className="p-3 mb-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{demoSectionError}</span>
                </div>
              )}

              <div className="space-y-2.5">
                <button
                  type="button"
                  disabled={loading || demoLoadingKey !== null}
                  onClick={() => handleQuickDemoSignIn('patient_demo', 'patient123', 'Patient')}
                  className="w-full text-left p-3 rounded-xl bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 shadow-sm transition group cursor-pointer disabled:opacity-70"
                >
                  <div className="flex justify-between items-center">
                    <div className="font-bold text-xs text-slate-800 group-hover:text-indigo-900 flex items-center space-x-2">
                      <span>🧑‍🦱 Eleanor Vance (Patient)</span>
                      {demoLoadingKey === 'patient_demo' && (
                        <Activity className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                      )}
                    </div>
                    <span className="text-[10px] bg-indigo-100 text-indigo-700 font-bold px-2 py-0.5 rounded-md">
                      {demoLoadingKey === 'patient_demo' ? 'Entering...' : 'Patient'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Upload radiograph, view detections, match doctors & book slots.
                  </div>
                </button>

                <button
                  type="button"
                  disabled={loading || demoLoadingKey !== null}
                  onClick={() => handleQuickDemoSignIn('doctor_demo', 'doctor123', 'Doctor')}
                  className="w-full text-left p-3 rounded-xl bg-white hover:bg-sky-50 border border-slate-200 hover:border-sky-300 shadow-sm transition group cursor-pointer disabled:opacity-70"
                >
                  <div className="flex justify-between items-center">
                    <div className="font-bold text-xs text-slate-800 group-hover:text-sky-900 flex items-center space-x-2">
                      <span>👨‍⚕️ Dr. Yukti Chauhan (Doctor)</span>
                      {demoLoadingKey === 'doctor_demo' && (
                        <Activity className="w-3.5 h-3.5 animate-spin text-sky-600" />
                      )}
                    </div>
                    <span className="text-[10px] bg-sky-100 text-sky-700 font-bold px-2 py-0.5 rounded-md">
                      {demoLoadingKey === 'doctor_demo' ? 'Entering...' : 'Pulmonologist'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Triage pending requests, 1-click confirmation & prescription notes.
                  </div>
                </button>

                <button
                  type="button"
                  disabled={loading || demoLoadingKey !== null}
                  onClick={() => handleQuickDemoSignIn('lab_demo', 'lab123', 'Laboratory')}
                  className="w-full text-left p-3 rounded-xl bg-white hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 shadow-sm transition group cursor-pointer disabled:opacity-70"
                >
                  <div className="flex justify-between items-center">
                    <div className="font-bold text-xs text-slate-800 group-hover:text-emerald-900 flex items-center space-x-2">
                      <span>🔬 Apex Diagnostic Lab</span>
                      {demoLoadingKey === 'lab_demo' && (
                        <Activity className="w-3.5 h-3.5 animate-spin text-emerald-600" />
                      )}
                    </div>
                    <span className="text-[10px] bg-emerald-100 text-emerald-700 font-bold px-2 py-0.5 rounded-md">
                      {demoLoadingKey === 'lab_demo' ? 'Entering...' : 'Lab Facility'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Patient intake, automated YOLO11 scan & routing to specialists.
                  </div>
                </button>
              </div>

              {/* Custom registered accounts */}
              {customAccounts.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-200">
                  <div className="text-[11px] font-bold text-slate-600 mb-2">
                    Recently Created Accounts ({customAccounts.length}):
                  </div>
                  <div className="max-h-32 overflow-y-auto space-y-1.5 pr-1">
                    {customAccounts.map(cu => (
                      <button
                        key={cu.username}
                        type="button"
                        onClick={() => {
                          onSuccess(cu);
                          onClose();
                        }}
                        className="w-full text-left p-2 rounded-lg bg-white border border-slate-200 text-xs flex justify-between items-center hover:bg-slate-100 transition cursor-pointer"
                      >
                        <span className="font-medium text-slate-800 truncate">{cu.full_name}</span>
                        <span className="text-[10px] text-slate-500 font-mono">@{cu.username}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>


            <div className="mt-4 pt-3 border-t border-slate-200 text-[11px] text-slate-400">
              🔒 Powered by YOLO11 Deep Learning & MongoDB Audit Trail
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
