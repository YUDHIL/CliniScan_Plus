'use client';

import React, { useState, useEffect } from 'react';
import { Appointment, UserSession } from '../types';
import { api } from '../lib/api';
import { 
  Calendar, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  FileText, 
  Building, 
  User, 
  Download,
  Stethoscope
} from 'lucide-react';

interface AppointmentsListProps {
  user: UserSession;
  onViewReport: (data: any) => void;
}

export const AppointmentsList: React.FC<AppointmentsListProps> = ({
  user,
  onViewReport,
}) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    loadPatientAppointments();
  }, [user]);

  const loadPatientAppointments = async () => {
    setLoading(true);
    try {
      const res = await api.getAppointments({
        patient_username: user.username,
      });
      setAppointments(res.appointments || []);
    } catch (e) {
      console.error('Failed to load appointments', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex justify-between items-center">
        <div>
          <h2 className="font-heading font-extrabold text-2xl text-slate-900 tracking-tight">
            My Appointments & Referral Passes
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Track live doctor confirmation statuses, view prescription advice, and download referral certificates.
          </p>
        </div>
        <div className="bg-sky-50 text-sky-700 px-3.5 py-1.5 rounded-xl border border-sky-200 text-xs font-bold">
          Total Records: {appointments.length}
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-500 text-xs font-bold">Loading appointments...</div>
      ) : appointments.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <h4 className="font-heading font-bold text-base text-slate-700">No Appointments Booked Yet</h4>
          <p className="text-xs text-slate-500 mt-1">
            Scan your chest X-ray or browse the 2,000-doctor directory to book your first clinical consultation.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {appointments.map((apt) => (
            <div
              key={apt.appointment_id}
              className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-sky-300 shadow-sm transition space-y-3"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div>
                  <span className="font-bold text-slate-900 text-sm">Appointment #{apt.appointment_id}</span>
                  <span className="text-xs text-slate-400 ml-2 font-medium">Booked on {apt.created_at?.slice(0, 10)}</span>
                </div>
                <div>
                  {apt.status === 'Confirmed' ? (
                    <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full border border-emerald-200 inline-flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Confirmed by Specialist</span>
                    </span>
                  ) : apt.status === 'Declined' ? (
                    <span className="bg-red-100 text-red-800 text-xs font-bold px-3 py-1 rounded-full border border-red-200 inline-flex items-center space-x-1">
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Declined</span>
                    </span>
                  ) : (
                    <span className="bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full border border-amber-200 inline-flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Pending Doctor Confirmation</span>
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-700 pt-2 border-t border-slate-100">
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Attending Specialist</div>
                  <div className="font-bold text-sky-700 text-sm mt-0.5">{apt.doctor_name}</div>
                  <div className="text-slate-500">🏥 {apt.hospital}, {apt.city}</div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Clinical Indication</div>
                  <div className="font-semibold text-slate-900 mt-0.5">{apt.clinical_indication}</div>
                  <div className="text-slate-500">Specialty: {apt.specialization}</div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Scheduled Slot</div>
                  <div className="font-bold text-slate-900 mt-0.5">{apt.appointment_slot}</div>
                  <div className="text-slate-500">Status: {apt.status}</div>
                </div>
              </div>

              {/* Prescription notes from doctor */}
              {apt.doctor_notes && (
                <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl text-xs text-emerald-900">
                  <div className="font-bold flex items-center space-x-1.5 mb-0.5">
                    <Stethoscope className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Attending Specialist Prescription Notes:</span>
                  </div>
                  <p className="text-slate-700">{apt.doctor_notes}</p>
                </div>
              )}

              {/* Real-World Quick Hospital Links & Action Buttons */}
              <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${apt.doctor_name} ${apt.hospital} ${apt.city}`)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-lg text-xs font-bold border border-emerald-200 transition flex items-center space-x-1"
                  >
                    <span>📍 Google Maps Route</span>
                  </a>
                  <a
                    href={`tel:${apt.city === 'Bangalore' ? '+918040001234' : '+911126598700'}`}
                    className="px-3 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-800 rounded-lg text-xs font-bold border border-sky-200 transition flex items-center space-x-1"
                  >
                    <span>📞 Hospital Desk</span>
                  </a>
                </div>

                {/* Confirmed Referral Pass Download */}
                {apt.status === 'Confirmed' && (
                  <button
                    onClick={() => onViewReport({
                      report_id: apt.appointment_id,
                      patient_info: {
                        full_name: apt.patient_name || user.full_name,
                        patient_id: `PAT-${user.username.toUpperCase()}`,
                        age: user.age || 45,
                        gender: user.gender || 'Male',
                        city: apt.city || 'Bangalore',
                        timestamp: apt.doctor_confirmed_at || apt.created_at,
                      },
                      detection_results: { detections: [], model_version: 'CliniScan-YOLO11-v1' },
                      referred_doctor: {
                        doctor_name: apt.doctor_name,
                        specialization: apt.specialization || 'Specialist',
                        hospital: apt.hospital || 'AIIMS Hospital',
                        city: apt.city || 'Bangalore',
                        fees_inr: 800,
                        disease_expertise: apt.clinical_indication,
                      },
                      doctor_notes: apt.doctor_notes || 'Confirmed consultation.',
                    })}
                    className="inline-flex items-center space-x-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm transition active:scale-95 cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Confirmed Referral Pass</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
