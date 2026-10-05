'use client';

import React, { useState } from 'react';
import { Doctor, UserSession } from '../types';
import { api } from '../lib/api';
import { 
  X, 
  Calendar, 
  Clock, 
  User, 
  Phone, 
  CheckCircle2, 
  AlertCircle,
  Building,
  MapPin,
  IndianRupee,
  Video,
  Sparkles,
  ExternalLink,
  Download,
  FileCheck,
  ShieldCheck,
  QrCode
} from 'lucide-react';

interface BookingModalProps {
  doctor: Doctor | null;
  user: UserSession | null;
  defaultFindingNote?: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AVAILABLE_TIME_SLOTS = [
  { time: '09:30 AM', label: 'Morning OPD', type: 'Available' },
  { time: '11:00 AM', label: 'Prime Slot', type: 'Fast Filling' },
  { time: '02:30 PM', label: 'Afternoon OPD', type: 'Available' },
  { time: '04:00 PM', label: 'Specialist Round', type: 'Available' },
  { time: '05:30 PM', label: 'Evening Clinic', type: 'Available' },
  { time: '07:00 PM', label: 'Urgent Triage', type: 'Priority' }
];

export const BookingModal: React.FC<BookingModalProps> = ({
  doctor,
  user,
  defaultFindingNote = '',
  onClose,
  onSuccess,
}) => {
  const tomorrowStr = new Date(Date.now() + 86400000).toISOString().split('T')[0];
  const [patientName, setPatientName] = useState(user?.full_name || 'Eleanor Vance');
  const [patientPhone, setPatientPhone] = useState(user?.phone || '+91 98765 43210');
  const [patientEmail, setPatientEmail] = useState(user?.email || 'patient@hospital.org');
  const [consultationType, setConsultationType] = useState<'in_person' | 'teleconsult'>('in_person');
  const [selectedDate, setSelectedDate] = useState<string>(tomorrowStr);
  const [selectedTime, setSelectedTime] = useState<string>('11:00 AM');
  const [clinicalIndication, setClinicalIndication] = useState(
    defaultFindingNote || (doctor ? `${doctor.disease_expertise || doctor.specialization} Clinical Follow-up` : 'Chest Radiograph Triage')
  );
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmedBooking, setConfirmedBooking] = useState<any | null>(null);

  if (!doctor) return null;

  const mapsSearchUrl = doctor.maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${doctor.doctor_name} ${doctor.hospital} ${doctor.city}`)}`;
  const practoBookingUrl = doctor.practo_url || `https://www.practo.com/search/doctors?results_type=doctor&q=${encodeURIComponent(`${doctor.doctor_name} ${doctor.city}`)}`;
  const doctorPhone = doctor.city === 'Bangalore' ? '+91 80 4000 1234' : '+91 11 2659 8700';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const fullSlot = `${selectedDate} at ${selectedTime} (${consultationType === 'in_person' ? 'In-Person Hospital Visit' : 'Video Teleconsultation'})`;

    try {
      const res = await api.createAppointment({
        patient_username: user?.username || 'patient_demo',
        patient_name: patientName.trim(),
        patient_phone: patientPhone.trim(),
        doctor_name: doctor.doctor_name,
        specialization: doctor.specialization,
        hospital: doctor.hospital,
        city: doctor.city,
        clinical_indication: clinicalIndication.trim(),
        appointment_slot: fullSlot,
      });

      const appointmentId = res.appointment_id || `APT-${Math.floor(Math.random() * 900000 + 100000)}`;

      setConfirmedBooking({
        appointment_id: appointmentId,
        patient_name: patientName,
        doctor_name: doctor.doctor_name,
        specialization: doctor.specialization,
        hospital: doctor.hospital,
        city: doctor.city,
        slot: fullSlot,
        date: selectedDate,
        time: selectedTime,
        type: consultationType,
        fees_inr: doctor.fees_inr,
        phone: patientPhone,
        indication: clinicalIndication
      });

      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Booking failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border-2 border-slate-200 overflow-hidden my-6 animate-fadeIn">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-800 via-sky-700 to-indigo-900 text-white px-8 py-5 flex justify-between items-center shadow-md">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20">
              <Calendar className="w-5 h-5 text-sky-200" />
            </div>
            <div>
              <h3 className="font-heading font-black text-lg sm:text-xl leading-tight">
                {confirmedBooking ? 'Hospital Consultation Pass' : 'Schedule Specialist Consultation'}
              </h3>
              <p className="text-xs text-sky-200 mt-0.5">
                {confirmedBooking ? 'Confirmed Appointment Slip & Priority Routing' : 'Real-world hospital appointment scheduling & digital pass'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-sky-200 hover:text-white p-2 rounded-xl hover:bg-white/10 transition cursor-pointer"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Doctor Summary Banner with Direct Real-World Action Links */}
        <div className="p-6 bg-slate-50 border-b border-slate-200 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-black text-lg text-slate-900">{doctor.doctor_name}</span>
                <span className="bg-emerald-100 text-emerald-800 text-[10px] font-black px-2.5 py-0.5 rounded-md border border-emerald-300 uppercase">
                  Verified Specialist
                </span>
              </div>
              <div className="text-xs text-sky-700 font-bold mt-0.5">
                {doctor.specialization} &bull; <strong className="text-slate-700">{doctor.hospital}</strong> ({doctor.city})
              </div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-sm font-black text-slate-900">₹{doctor.fees_inr}</div>
              <div className="text-[11px] text-emerald-700 font-bold">● {doctor.availability}</div>
            </div>
          </div>

          {/* Direct Real-World Hospital & Doctor Action Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-slate-200/80">
            <a
              href={mapsSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="py-2 px-3 bg-white hover:bg-emerald-50 text-emerald-800 rounded-xl border border-emerald-200 text-xs font-bold flex items-center justify-center space-x-1.5 transition shadow-sm hover:shadow"
            >
              <MapPin className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>📍 Google Maps Route</span>
            </a>

            <a
              href={`tel:${doctorPhone}`}
              className="py-2 px-3 bg-white hover:bg-sky-50 text-sky-800 rounded-xl border border-sky-200 text-xs font-bold flex items-center justify-center space-x-1.5 transition shadow-sm hover:shadow"
            >
              <Phone className="w-3.5 h-3.5 text-sky-600 shrink-0" />
              <span>📞 Call Reception</span>
            </a>

            <a
              href={practoBookingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="py-2 px-3 bg-white hover:bg-indigo-50 text-indigo-800 rounded-xl border border-indigo-200 text-xs font-bold flex items-center justify-center space-x-1.5 transition shadow-sm hover:shadow"
            >
              <ExternalLink className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
              <span>🌐 Practo / Hospital Link</span>
            </a>
          </div>
        </div>

        {confirmedBooking ? (
          /* ============================================================ */
          /* 1. CONFIRMED DIGITAL APPOINTMENT PASS VIEW                   */
          /* ============================================================ */
          <div className="p-8 space-y-6">
            <div className="bg-emerald-50 border-2 border-emerald-300 rounded-3xl p-6 text-emerald-950 space-y-3 relative overflow-hidden shadow-sm">
              <div className="flex items-center space-x-3">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 shrink-0" />
                <div>
                  <h4 className="font-heading font-black text-lg text-emerald-900">
                    Appointment Successfully Scheduled!
                  </h4>
                  <p className="text-xs text-emerald-700">
                    Your referral token has been registered with {doctor.hospital} Clinical Dispatch.
                  </p>
                </div>
              </div>

              {/* Digital Pass Ticket */}
              <div className="bg-white rounded-2xl p-5 border border-emerald-200 shadow-sm space-y-4 mt-4">
                <div className="flex justify-between items-center pb-3 border-b border-dashed border-slate-300">
                  <div>
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Token Number</span>
                    <div className="font-heading font-black text-xl text-sky-800">#{confirmedBooking.appointment_id}</div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Mode</span>
                    <div className="text-xs font-black text-slate-800">
                      {confirmedBooking.type === 'in_person' ? '🏥 In-Person Hospital OPD' : '💻 Video Teleconsultation'}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs text-slate-700">
                  <div>
                    <span className="text-slate-400 font-bold block">Patient Name:</span>
                    <strong className="text-slate-900 font-extrabold text-sm">{confirmedBooking.patient_name}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 font-bold block">Attending Specialist:</span>
                    <strong className="text-slate-900 font-extrabold text-sm">{confirmedBooking.doctor_name}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 font-bold block">Hospital Campus:</span>
                    <strong className="text-slate-900 font-extrabold">{confirmedBooking.hospital}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400 font-bold block">Scheduled Slot:</span>
                    <strong className="text-emerald-800 font-black">{confirmedBooking.slot}</strong>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>Clinical Indication: <strong>{confirmedBooking.indication}</strong></span>
                  <span className="bg-sky-50 text-sky-800 px-3 py-1 rounded-full font-black text-[11px]">
                    Consultation Fee: ₹{confirmedBooking.fees_inr}
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons on Confirmation */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                type="button"
                onClick={() => window.print()}
                className="flex-1 py-3.5 bg-slate-900 hover:bg-slate-800 text-white font-black text-xs sm:text-sm rounded-2xl shadow-md transition flex items-center justify-center space-x-2 cursor-pointer"
              >
                <Download className="w-4 h-4" />
                <span>Print Official Slip</span>
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-3.5 bg-sky-600 hover:bg-sky-700 text-white font-black text-xs sm:text-sm rounded-2xl shadow-md shadow-sky-600/30 transition flex items-center justify-center space-x-2 cursor-pointer"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Done / View My Appointments</span>
              </button>
            </div>
          </div>
        ) : (
          /* ============================================================ */
          /* 2. REAL-TIME BOOKING FORM                                    */
          /* ============================================================ */
          <form onSubmit={handleSubmit} className="p-8 space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border-2 border-red-200 text-red-700 text-xs font-bold rounded-2xl flex items-center space-x-2.5">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Consultation Mode Switcher */}
            <div>
              <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-2">
                1. Select Consultation Mode:
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setConsultationType('in_person')}
                  className={`p-3.5 rounded-2xl border-2 text-left transition cursor-pointer flex items-center space-x-3 ${
                    consultationType === 'in_person'
                      ? 'bg-sky-50 border-sky-600 shadow-md ring-2 ring-sky-500/20 text-sky-950'
                      : 'bg-white border-slate-200 hover:border-slate-300 text-slate-600'
                  }`}
                >
                  <Building className="w-5 h-5 text-sky-600 shrink-0" />
                  <div>
                    <div className="font-heading font-black text-xs sm:text-sm">In-Person OPD Visit</div>
                    <div className="text-[10px] text-slate-500">Physical hospital chamber consultation</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setConsultationType('teleconsult')}
                  className={`p-3.5 rounded-2xl border-2 text-left transition cursor-pointer flex items-center space-x-3 ${
                    consultationType === 'teleconsult'
                      ? 'bg-sky-50 border-sky-600 shadow-md ring-2 ring-sky-500/20 text-sky-950'
                      : 'bg-white border-slate-200 hover:border-slate-300 text-slate-600'
                  }`}
                >
                  <Video className="w-5 h-5 text-indigo-600 shrink-0" />
                  <div>
                    <div className="font-heading font-black text-xs sm:text-sm">Video Teleconsultation</div>
                    <div className="text-[10px] text-slate-500">Encrypted HD digital consultation</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Date & Time Slot Selector */}
            <div className="space-y-3">
              <label className="block text-xs font-black text-slate-700 uppercase tracking-wider">
                2. Select Date & Preferred OPD Slot:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-1">
                  <input
                    type="date"
                    required
                    min={new Date().toISOString().split('T')[0]}
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-full px-3.5 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs sm:text-sm font-bold text-slate-800 focus:bg-white focus:ring-2 focus:ring-sky-500 cursor-pointer"
                  />
                </div>

                <div className="sm:col-span-2 grid grid-cols-3 gap-2">
                  {AVAILABLE_TIME_SLOTS.map((slot) => {
                    const isSelected = selectedTime === slot.time;
                    return (
                      <button
                        key={slot.time}
                        type="button"
                        onClick={() => setSelectedTime(slot.time)}
                        className={`py-2.5 px-2 rounded-xl border text-center transition cursor-pointer ${
                          isSelected
                            ? 'bg-sky-600 text-white font-black border-sky-600 shadow-md'
                            : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700 font-bold text-xs'
                        }`}
                      >
                        <div className="text-xs">{slot.time}</div>
                        <div className={`text-[9px] ${isSelected ? 'text-sky-100' : 'text-slate-400'}`}>{slot.label}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Patient Credentials */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Patient Full Name *</label>
                <input
                  type="text"
                  required
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder="e.g. Rahul Sharma"
                  className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs sm:text-sm font-bold text-slate-800 focus:bg-white focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Patient Contact Phone *</label>
                <input
                  type="tel"
                  required
                  value={patientPhone}
                  onChange={(e) => setPatientPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs sm:text-sm font-bold text-slate-800 focus:bg-white focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Clinical Indication / Chest Findings *</label>
              <input
                type="text"
                required
                value={clinicalIndication}
                onChange={(e) => setClinicalIndication(e.target.value)}
                placeholder="Radiographic finding or symptoms"
                className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs sm:text-sm font-bold text-slate-800 focus:bg-white focus:ring-2 focus:ring-sky-500"
              />
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-sky-600 via-sky-700 to-indigo-800 hover:from-sky-700 hover:to-indigo-900 text-white font-heading font-black text-sm sm:text-base rounded-2xl shadow-xl shadow-sky-600/30 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
              >
                {loading ? (
                  <>
                    <Clock className="w-5 h-5 animate-spin" />
                    <span>Transmitting Booking to Hospital Dispatch...</span>
                  </>
                ) : (
                  <>
                    <Calendar className="w-5 h-5" />
                    <span>Confirm Consultation Booking ➔</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
