'use client';

import React, { useState, useEffect } from 'react';
import { UserSession, Doctor, FilterMetadata } from '../types';
import { api } from '../lib/api';
import { Navbar } from '../components/Navbar';
import { LandingHeroAuth } from '../components/LandingHeroAuth';
import { AuthModal } from '../components/AuthModal';
import { XrayScanner } from '../components/XrayScanner';
import { DoctorDirectory } from '../components/DoctorDirectory';
import { BookingModal } from '../components/BookingModal';
import { DoctorTriageQueue } from '../components/DoctorTriageQueue';
import { DiagnosticStudio } from '../components/DiagnosticStudio';
import { LaboratoryPortal } from '../components/LaboratoryPortal';
import { AppointmentsList } from '../components/AppointmentsList';
import { ScanHistory } from '../components/ScanHistory';
import { DoctorRegistrationModal } from '../components/DoctorRegistrationModal';
import { ProfileSettings } from '../components/ProfileSettings';
import { ModelInsights } from '../components/ModelInsights';
import { ReportViewerModal } from '../components/ReportViewerModal';
import { ClinicalChatbot } from '../components/ClinicalChatbot';
import { 
  Activity, 
  Crosshair, 
  Search, 
  Calendar, 
  FolderOpen, 
  User, 
  Stethoscope, 
  FlaskConical, 
  Layers, 
  Clock, 
  ShieldCheck,
  ChevronRight,
  Sparkles,
  ArrowRight,
  HeartPulse,
  Award,
  PhoneCall,
  CheckCircle2
} from 'lucide-react';

export default function Home() {
  const [user, setUser] = useState<UserSession | null>(null);
  const [activeTab, setActiveTab] = useState<string>('scanner');
  const [activeDoctorPersona, setActiveDoctorPersona] = useState<string>('');
  
  // Metadata & Samples
  const [metadata, setMetadata] = useState<FilterMetadata>({
    cities: [],
    specializations: [],
    hospitals: [],
    target_classes: [],
    severity_mapping: {},
    storage_mode: 'MongoDB Live',
    total_doctors: 2000,
  });
  const [samples, setSamples] = useState<Array<{ filename: string; directory: string; size_bytes: number }>>([]);
  const [allRegisteredDoctors, setAllRegisteredDoctors] = useState<UserSession[]>([]);

  // Modals
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [bookingDoctor, setBookingDoctor] = useState<{ doctor: Doctor; findingNote?: string } | null>(null);
  const [isRegisterDoctorOpen, setIsRegisterDoctorOpen] = useState<boolean>(false);
  const [activeReportData, setActiveReportData] = useState<any | null>(null);

  useEffect(() => {
    // Check saved session in localStorage
    const savedUser = localStorage.getItem('cliniscan_user');
    if (savedUser) {
      try {
        const u = JSON.parse(savedUser);
        setUser(u);
        if (u.role === 'Doctor') setActiveDoctorPersona(u.full_name);
      } catch (e) {}
    }

    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [metaRes, samplesRes, demoUsersRes] = await Promise.all([
        api.getMetadata(),
        api.getSamples(),
        api.getDemoUsers(),
      ]);
      setMetadata(metaRes);
      setSamples(samplesRes.samples || []);
      
      const doctorsList = [
        ...(demoUsersRes.demo_accounts || []).filter(u => u.role === 'Doctor'),
        ...(demoUsersRes.custom_accounts || []).filter(u => u.role === 'Doctor'),
      ];
      setAllRegisteredDoctors(doctorsList);
    } catch (e) {
      console.error('Failed to load initial metadata', e);
    }
  };

  const handleUserLogin = (loggedUser: UserSession) => {
    setUser(loggedUser);
    localStorage.setItem('cliniscan_user', JSON.stringify(loggedUser));
    if (loggedUser.role === 'Doctor') {
      setActiveDoctorPersona(loggedUser.full_name);
      setActiveTab('triage');
    } else if (loggedUser.role === 'Laboratory') {
      setActiveTab('lab_intake');
    } else {
      setActiveTab('scanner');
    }
  };

  const handleSignOut = () => {
    setUser(null);
    localStorage.removeItem('cliniscan_user');
    setActiveDoctorPersona('');
  };

  const handleOpenBooking = (doc: Doctor, findingNote?: string) => {
    setBookingDoctor({ doctor: doc, findingNote });
  };

  // Dynamic Navigation menu items based on active role
  const getMenuItems = () => {
    if (!user || user.role === 'Patient') {
      return [
        { id: 'scanner', label: 'Scan X-ray & Match Doctor', icon: Crosshair, badge: 'AI Engine' },
        { id: 'directory', label: '2,000 Doctors Directory', icon: Search, badge: 'Network' },
        { id: 'appointments', label: 'My Appointments & Referrals', icon: Calendar, badge: 'Live' },
        { id: 'scans', label: 'My Diagnostic Scan Vault', icon: FolderOpen },
        { id: 'profile', label: 'My Profile & Settings', icon: User },
        { id: 'insights', label: 'Model & Research Insights', icon: Layers },
      ];
    } else if (user.role === 'Doctor') {
      return [
        { id: 'triage', label: 'Patient Triage Review Queue', icon: Clock, badge: 'Active' },
        { id: 'studio', label: 'Diagnostic Studio Lab', icon: Crosshair, badge: 'YOLO11' },
        { id: 'directory', label: '2,000 Doctors Directory', icon: Search },
        { id: 'profile', label: 'Practice Profile & Settings', icon: Stethoscope },
        { id: 'insights', label: 'Model & Research Insights', icon: Layers },
      ];
    } else {
      // Laboratory
      return [
        { id: 'lab_intake', label: 'Patient Intake & AI Triage', icon: FlaskConical, badge: 'Intake' },
        { id: 'directory', label: '2,000 Doctors Directory', icon: Search },
        { id: 'profile', label: 'Facility Profile & License', icon: User },
        { id: 'insights', label: 'Model & Research Insights', icon: Layers },
      ];
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans w-full">
      {/* Top Navbar (Expanded Full Width) */}
      <Navbar
        user={user}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onSignOut={handleSignOut}
        activeDoctorPersona={activeDoctorPersona}
        onSelectDoctorPersona={setActiveDoctorPersona}
        allDoctors={allRegisteredDoctors}
      />

      {/* Main Content Area (Full-Width Fluid Workspace) */}
      <div className="flex-1 w-full px-4 sm:px-6 lg:px-8 xl:px-10 py-6 sm:py-8">
        {!user ? (
          /* FRONT PAGE: Dedicated Landing, Hero, Login & Registration */
          <LandingHeroAuth
            onSuccess={handleUserLogin}
            cities={metadata.cities}
            specializations={metadata.specializations}
            hospitals={metadata.hospitals}
          />
        ) : (
          /* LOGGED IN: Wide Clinical Dashboard */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 xl:gap-8 items-start w-full">
            {/* Left Sidebar */}
            <aside className="lg:col-span-4 xl:col-span-3 2xl:col-span-2 space-y-6">
              {/* Main Navigation Card */}
              <div className="bg-white rounded-3xl p-6 border-2 border-slate-200/90 shadow-lg space-y-5">
                <div className="flex justify-between items-center pb-3 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
                    <span className="text-xs font-black text-slate-500 uppercase tracking-wider">
                      {user.role} Navigation Hub
                    </span>
                  </div>
                  <span className="text-xs font-extrabold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200">
                    Live
                  </span>
                </div>

                <nav className="space-y-2">
                  {getMenuItems().map(({ id, label, icon: Icon, badge }) => {
                    const isActive = activeTab === id;
                    return (
                      <button
                        key={id}
                        onClick={() => setActiveTab(id)}
                        className={`w-full text-left px-5 py-4 rounded-2xl text-sm sm:text-base font-black flex items-center justify-between transition cursor-pointer ${
                          isActive
                            ? 'bg-gradient-to-r from-sky-600 via-sky-700 to-indigo-800 text-white shadow-lg shadow-sky-600/30 ring-2 ring-sky-400/40'
                            : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                        }`}
                      >
                        <div className="flex items-center space-x-3.5">
                          <Icon className={`w-6 h-6 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                          <span className="leading-tight">{label}</span>
                        </div>
                        {badge && (
                          <span className={`text-[10px] font-black px-2.5 py-1 rounded-lg uppercase tracking-wider ${
                            isActive ? 'bg-white/25 text-white' : 'bg-slate-100 text-slate-700'
                          }`}>
                            {badge}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </nav>

                {/* Switch Role Quick Button */}
                <div className="pt-3 border-t border-slate-100">
                  <button
                    onClick={() => setIsAuthModalOpen(true)}
                    className="w-full py-3.5 px-4 bg-gradient-to-r from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100 rounded-2xl text-xs sm:text-sm font-black text-amber-950 border-2 border-amber-300 transition flex items-center justify-center space-x-2 shadow-sm"
                  >
                    <Sparkles className="w-5 h-5 text-amber-600 fill-amber-500" />
                    <span>⚡ Switch Role / Quick Access</span>
                  </button>
                </div>
              </div>

              {/* Live System Specs Widget */}
              <div className="bg-white rounded-3xl p-6 border-2 border-slate-200/90 shadow-lg text-sm text-slate-600 space-y-3.5">
                <div className="font-black text-slate-900 text-xs uppercase tracking-wider flex items-center space-x-2 pb-3 border-b border-slate-100">
                  <Activity className="w-5 h-5 text-sky-600" />
                  <span>Clinical Infrastructure Specs</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-medium">Detection Engine:</span>
                  <strong className="text-slate-900 font-black">YOLO11 Nano</strong>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-medium">Persistence Mode:</span>
                  <strong className="text-slate-900 font-black">{metadata.storage_mode}</strong>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-medium">Specialist Roster:</span>
                  <strong className="text-sky-700 font-black">2,000+ Doctors</strong>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-medium">Pathologies:</span>
                  <strong className="text-emerald-700 font-black">10 Target Classes</strong>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-medium">Median Latency:</span>
                  <strong className="text-sky-600 font-mono font-black">&lt;250 ms</strong>
                </div>
              </div>

              {/* Verified Hospital Network Badge */}
              <div className="bg-gradient-to-br from-slate-900 to-sky-950 rounded-3xl p-6 text-white shadow-lg space-y-3 border border-slate-800">
                <div className="flex items-center space-x-2 text-sky-400">
                  <ShieldCheck className="w-6 h-6" />
                  <span className="font-heading font-black text-sm uppercase tracking-wider">Hospital Accredited</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  Connected to 10 top hospital networks across 26 major cities with instant specialist triage routing.
                </p>
                <div className="text-[11px] text-sky-300 font-extrabold flex items-center space-x-1.5 pt-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>VinBigData Chest X-ray Engine</span>
                </div>
              </div>
            </aside>

            {/* Main Content Workspace (Full Width Responsive Workspace) */}
            <main className="lg:col-span-8 xl:col-span-9 2xl:col-span-10 space-y-8 w-full min-w-0">
              {/* PATIENT VIEWS */}
              {activeTab === 'scanner' && (
                <XrayScanner
                  user={user}
                  onBookDoctor={handleOpenBooking}
                  onViewReport={setActiveReportData}
                  samples={samples}
                />
              )}

              {activeTab === 'directory' && (
                <DoctorDirectory
                  cities={metadata.cities}
                  specializations={metadata.specializations}
                  hospitals={metadata.hospitals}
                  onBookDoctor={handleOpenBooking}
                  onOpenRegisterModal={() => setIsRegisterDoctorOpen(true)}
                />
              )}

              {activeTab === 'appointments' && (
                <AppointmentsList
                  user={user}
                  onViewReport={setActiveReportData}
                />
              )}

              {activeTab === 'scans' && (
                <ScanHistory
                  user={user}
                  onViewReport={setActiveReportData}
                />
              )}

              {/* DOCTOR VIEWS */}
              {activeTab === 'triage' && (
                <DoctorTriageQueue
                  user={user}
                  activeDoctorName={activeDoctorPersona || user.full_name}
                />
              )}

              {activeTab === 'studio' && (
                <DiagnosticStudio
                  user={user}
                  activeDoctorName={activeDoctorPersona || user.full_name}
                  onViewReport={setActiveReportData}
                  samples={samples}
                />
              )}

              {/* LABORATORY VIEWS */}
              {activeTab === 'lab_intake' && (
                <LaboratoryPortal
                  user={user}
                  cities={metadata.cities}
                  onViewReport={setActiveReportData}
                  samples={samples}
                />
              )}


              {/* COMMON VIEWS */}
              {activeTab === 'profile' && (
                <ProfileSettings
                  user={user}
                  cities={metadata.cities}
                  specializations={metadata.specializations}
                  hospitals={metadata.hospitals}
                  onUpdateSuccess={(updated) => {
                    setUser(updated);
                    localStorage.setItem('cliniscan_user', JSON.stringify(updated));
                  }}
                />
              )}

              {activeTab === 'insights' && (
                <ModelInsights
                  targetClasses={metadata.target_classes}
                  severityMapping={metadata.severity_mapping}
                  storageMode={metadata.storage_mode}
                />
              )}
            </main>
          </div>
        )}
      </div>

      {/* GLOBAL MODALS */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={handleUserLogin}
        cities={metadata.cities}
        specializations={metadata.specializations}
        hospitals={metadata.hospitals}
      />

      <BookingModal
        doctor={bookingDoctor?.doctor || null}
        user={user}
        defaultFindingNote={bookingDoctor?.findingNote}
        onClose={() => setBookingDoctor(null)}
        onSuccess={() => {
          if (user?.role === 'Patient') setActiveTab('appointments');
        }}
      />

      <DoctorRegistrationModal
        isOpen={isRegisterDoctorOpen}
        onClose={() => setIsRegisterDoctorOpen(false)}
        onSuccess={() => {
          setIsRegisterDoctorOpen(false);
          loadInitialData();
        }}
        cities={metadata.cities}
        specializations={metadata.specializations}
        hospitals={metadata.hospitals}
      />

      <ReportViewerModal
        reportData={activeReportData}
        onClose={() => setActiveReportData(null)}
      />

      {/* PERSISTENT CLINICAL AI CHATBOT (Always docked in bottom-right corner across all tabs) */}
      <ClinicalChatbot user={user} />
    </div>
  );
}
