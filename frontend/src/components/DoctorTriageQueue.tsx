'use client';

import React, { useState, useEffect } from 'react';
import { Appointment, UserSession } from '../types';
import { api } from '../lib/api';
import { 
  Clock, 
  CheckCircle2, 
  XCircle, 
  Zap, 
  FileEdit, 
  User, 
  Phone, 
  Building, 
  AlertCircle,
  Stethoscope,
  Sparkles,
  Calendar
} from 'lucide-react';

interface DoctorTriageQueueProps {
  user: UserSession;
  activeDoctorName: string;
}

export const DoctorTriageQueue: React.FC<DoctorTriageQueueProps> = ({
  user,
  activeDoctorName,
}) => {
  const [mode, setMode] = useState<'all' | 'assigned'>('all');
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeNoteModalApt, setActiveNoteModalApt] = useState<Appointment | null>(null);
  const [docNotes, setDocNotes] = useState<string>(
    'Confirmed. Please bring previous chest radiographs and report for physical consultation.'
  );
  const [actionSuccess, setActionSuccess] = useState<string>('');

  useEffect(() => {
    loadAppointments();
  }, [mode, activeDoctorName]);

  const loadAppointments = async () => {
    setLoading(true);
    try {
      const res = await api.getAppointments({
        doctor_name: mode === 'assigned' ? activeDoctorName : undefined,
      });
      setAppointments(res.appointments || []);
    } catch (e) {
      console.error('Failed to load doctor triage appointments', e);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickConfirm = async (apt: Appointment) => {
    const targetDoc = apt.doctor_name || activeDoctorName;
    try {
      await api.confirmAppointment(apt.appointment_id, {
        doctor_name: targetDoc,
        doctor_notes: 'Confirmed by attending specialist. Please report to the pulmonary clinic 15 minutes before scheduled slot.',
        status: 'Confirmed',
      });
      setActionSuccess(`🎉 Appointment #${apt.appointment_id} confirmed successfully!`);
      setTimeout(() => setActionSuccess(''), 3000);
      loadAppointments();
    } catch (e: any) {
      alert(`Confirmation failed: ${e.message}`);
    }
  };

  const handleCustomConfirm = async (status: 'Confirmed' | 'Declined') => {
    if (!activeNoteModalApt) return;
    try {
      await api.confirmAppointment(activeNoteModalApt.appointment_id, {
        doctor_name: activeNoteModalApt.doctor_name || activeDoctorName,
        doctor_notes: docNotes,
        status: status,
      });
      setActiveNoteModalApt(null);
      setActionSuccess(`Appointment #${activeNoteModalApt.appointment_id} marked as ${status}!`);
      setTimeout(() => setActionSuccess(''), 3000);
      loadAppointments();
    } catch (e: any) {
      alert(`Action failed: ${e.message}`);
    }
  };

  const pendingApts = appointments.filter(a => a.status === 'Pending');
  const confirmedApts = appointments.filter(a => a.status === 'Confirmed');

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-sky-900 via-sky-800 to-indigo-950 rounded-3xl p-8 sm:p-10 text-white shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border border-sky-800/60">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 bg-sky-500/20 px-3.5 py-1.5 rounded-full text-sky-200 text-xs sm:text-sm font-extrabold uppercase tracking-wider">
            <Stethoscope className="w-4 h-4 text-sky-300" />
            <span>Doctor Clinical Triage Hub</span>
          </div>
          <h2 className="font-heading font-extrabold text-3xl sm:text-4xl tracking-tight">
            Patient Consultation Review Queue
          </h2>
          <p className="text-sm text-sky-100">
            Attending Specialist: <strong className="text-white font-extrabold">{activeDoctorName}</strong> ({user.hospital || 'AIIMS Hospital'})
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="bg-white/10 backdrop-blur-md p-1.5 rounded-2xl border border-white/20 flex text-xs sm:text-sm font-extrabold">
          <button
            onClick={() => setMode('all')}
            className={`px-4 py-2 rounded-xl transition ${
              mode === 'all' ? 'bg-white text-sky-950 shadow-md' : 'text-sky-100 hover:text-white'
            }`}
          >
            🌐 All Hospital Requests
          </button>
          <button
            onClick={() => setMode('assigned')}
            className={`px-4 py-2 rounded-xl transition ${
              mode === 'assigned' ? 'bg-white text-sky-950 shadow-md' : 'text-sky-100 hover:text-white'
            }`}
          >
            🩺 Assigned to Me
          </button>
        </div>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="bg-white rounded-3xl p-7 border-l-8 border-l-amber-500 border border-slate-200 shadow-md flex items-center justify-between">
          <div>
            <div className="text-xs font-black text-slate-500 uppercase tracking-wider">Pending Review Requests</div>
            <div className="font-heading text-4xl sm:text-5xl font-black text-amber-600 mt-2">{pendingApts.length}</div>
          </div>
          <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center">
            <Clock className="w-8 h-8" />
          </div>
        </div>

        <div className="bg-white rounded-3xl p-7 border-l-8 border-l-emerald-500 border border-slate-200 shadow-md flex items-center justify-between">
          <div>
            <div className="text-xs font-black text-slate-500 uppercase tracking-wider">Confirmed Consultations</div>
            <div className="font-heading text-4xl sm:text-5xl font-black text-emerald-600 mt-2">{confirmedApts.length}</div>
          </div>
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-500 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8" />
          </div>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-5 bg-emerald-50 border-2 border-emerald-200 text-emerald-900 text-sm font-extrabold rounded-2xl flex items-center space-x-3 animate-fadeIn">
          <CheckCircle2 className="w-6 h-6 flex-shrink-0 text-emerald-600" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* PENDING APPOINTMENTS */}
      <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-md space-y-6">
        <h3 className="font-heading font-extrabold text-slate-900 text-xl sm:text-2xl flex items-center space-x-3">
          <Clock className="w-6 h-6 text-amber-500" />
          <span>Pending Patient Requests Requiring Review ({pendingApts.length})</span>
        </h3>

        {loading ? (
          <div className="py-16 text-center text-slate-500 text-sm font-bold">Loading queue...</div>
        ) : pendingApts.length === 0 ? (
          <div className="p-10 bg-emerald-50 border-2 border-emerald-200 rounded-3xl text-center text-emerald-900 space-y-2">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
            <div className="font-heading font-extrabold text-lg">All Patient Requests Are Up to Date!</div>
            <p className="text-sm text-emerald-700">No pending consultation requests requiring confirmation in this queue.</p>
          </div>
        ) : (
          <div className="space-y-5">
            {pendingApts.map((apt) => (
              <div
                key={apt.appointment_id}
                className="p-6 rounded-3xl border-2 border-slate-200 bg-slate-50/70 hover:bg-white hover:border-sky-400 transition shadow-sm space-y-4"
              >
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                  <div className="flex items-center space-x-3">
                    <span className="font-heading font-extrabold text-slate-900 text-base sm:text-lg">
                      Appointment #{apt.appointment_id}
                    </span>
                    <span className="bg-amber-100 text-amber-900 text-xs font-black px-3 py-1 rounded-full border border-amber-300">
                      ⏳ Pending Doctor Confirmation
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 font-semibold">Booked on {apt.created_at?.slice(0, 10)}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs sm:text-sm text-slate-700 pt-3 border-t border-slate-200">
                  <div className="bg-white p-3.5 rounded-2xl border border-slate-200/80">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Patient Coordinates</div>
                    <div className="font-extrabold text-slate-900 text-base mt-0.5">{apt.patient_name}</div>
                    <div className="text-slate-500 mt-0.5 font-medium">📞 {apt.patient_phone}</div>
                  </div>

                  <div className="bg-white p-3.5 rounded-2xl border border-slate-200/80">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Assigned Doctor & Hospital</div>
                    <div className="font-extrabold text-sky-800 text-base mt-0.5">{apt.doctor_name}</div>
                    <div className="text-slate-500 mt-0.5 font-medium">🏥 {apt.hospital}, {apt.city}</div>
                  </div>

                  <div className="bg-white p-3.5 rounded-2xl border border-slate-200/80">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Clinical Indication & Slot</div>
                    <div className="font-extrabold text-red-600 text-sm mt-0.5 truncate">{apt.clinical_indication}</div>
                    <div className="text-slate-500 mt-0.5 font-medium">📅 {apt.appointment_slot}</div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                  <button
                    onClick={() => handleQuickConfirm(apt)}
                    className="w-full sm:w-auto flex-1 py-3 px-6 bg-sky-600 hover:bg-sky-700 text-white font-heading font-extrabold text-xs sm:text-sm rounded-2xl shadow-md shadow-sky-600/25 transition flex items-center justify-center space-x-2"
                  >
                    <Zap className="w-4 h-4" />
                    <span>1-Click Confirm as {apt.doctor_name || activeDoctorName}</span>
                  </button>

                  <button
                    onClick={() => {
                      setActiveNoteModalApt(apt);
                      setDocNotes(
                        `Confirmed consultation. Patient presents with indications for ${apt.clinical_indication}. Please bring previous radiographs and laboratory results.`
                      );
                    }}
                    className="w-full sm:w-auto py-3 px-6 bg-white hover:bg-slate-100 text-slate-800 font-heading font-extrabold text-xs sm:text-sm rounded-2xl border-2 border-slate-300 transition flex items-center justify-center space-x-2"
                  >
                    <FileEdit className="w-4 h-4" />
                    <span>Custom Prescription & Advice</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* CONFIRMED PATIENTS */}
      <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-md space-y-6">
        <h3 className="font-heading font-extrabold text-slate-900 text-xl sm:text-2xl flex items-center space-x-3">
          <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          <span>Confirmed Patient Consultation Roster ({confirmedApts.length})</span>
        </h3>

        {confirmedApts.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No confirmed appointments currently on record.</p>
        ) : (
          <div className="space-y-4">
            {confirmedApts.map((ca) => (
              <div
                key={ca.appointment_id}
                className="p-5 rounded-2xl border-2 border-emerald-200 bg-emerald-50/30 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs sm:text-sm"
              >
                <div>
                  <div className="flex items-center space-x-3">
                    <span className="font-heading font-extrabold text-slate-900 text-base">
                      #{ca.appointment_id} &bull; {ca.patient_name}
                    </span>
                    <span className="bg-emerald-100 text-emerald-900 font-extrabold px-3 py-1 rounded-full text-xs">
                      Confirmed
                    </span>
                  </div>
                  <div className="text-slate-600 mt-1.5 font-medium">
                    <strong>Clinical Indication:</strong> {ca.clinical_indication} &nbsp;|&nbsp; <strong>Slot:</strong> {ca.appointment_slot}
                  </div>
                  {ca.doctor_notes && (
                    <div className="mt-2 text-emerald-900 bg-white p-3 rounded-xl border border-emerald-200 text-xs font-medium">
                      👨‍⚕️ <strong>Prescription:</strong> {ca.doctor_notes}
                    </div>
                  )}
                </div>
                <div className="text-right text-xs text-slate-500 font-medium">
                  Confirmed by: <strong className="text-slate-800">{ca.doctor_name}</strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Custom Note & Prescription Modal */}
      {activeNoteModalApt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="w-full max-w-xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-gradient-to-r from-sky-800 to-sky-700 text-white px-8 py-5 flex justify-between items-center">
              <h4 className="font-heading font-extrabold text-lg">Physician Prescription & Clinical Protocol</h4>
              <button
                onClick={() => setActiveNoteModalApt(null)}
                className="text-sky-200 hover:text-white p-1"
              >
                ✕
              </button>
            </div>
            <div className="p-8 space-y-5">
              <div className="text-xs sm:text-sm text-slate-600 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                Patient: <strong className="text-slate-900 font-extrabold">{activeNoteModalApt.patient_name}</strong> | Slot:{' '}
                <strong className="text-slate-900 font-extrabold">{activeNoteModalApt.appointment_slot}</strong>
              </div>

              <div>
                <label className="block text-xs font-extrabold text-slate-700 uppercase tracking-wider mb-2">
                  Attending Physician Notes / Clinical Advice:
                </label>
                <textarea
                  rows={4}
                  value={docNotes}
                  onChange={(e) => setDocNotes(e.target.value)}
                  className="w-full p-4 bg-slate-50 border-2 border-slate-200 rounded-2xl text-sm font-medium focus:ring-2 focus:ring-sky-500 focus:bg-white"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  onClick={() => handleCustomConfirm('Confirmed')}
                  className="flex-1 py-3.5 bg-sky-600 hover:bg-sky-700 text-white font-heading font-extrabold text-sm rounded-2xl shadow-md transition"
                >
                  ✅ Save Notes & Confirm
                </button>
                <button
                  onClick={() => handleCustomConfirm('Declined')}
                  className="py-3.5 px-6 bg-red-50 hover:bg-red-100 text-red-700 font-heading font-extrabold text-sm rounded-2xl border-2 border-red-200 transition"
                >
                  ❌ Decline
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
