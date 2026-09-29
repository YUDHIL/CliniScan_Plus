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
  IndianRupee
} from 'lucide-react';

interface BookingModalProps {
  doctor: Doctor | null;
  user: UserSession | null;
  defaultFindingNote?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const BookingModal: React.FC<BookingModalProps> = ({
  doctor,
  user,
  defaultFindingNote = '',
  onClose,
  onSuccess,
}) => {
  const [patientName, setPatientName] = useState(user?.full_name || 'Eleanor Vance');
  const [patientPhone, setPatientPhone] = useState(user?.phone || '+91 98765 43210');
  const [clinicalIndication, setClinicalIndication] = useState(
    defaultFindingNote || (doctor ? `${doctor.disease_expertise} Consultation` : 'Respiratory Evaluation')
  );
  const [appointmentSlot, setAppointmentSlot] = useState('Tomorrow 10:30 AM (Priority Slot)');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (!doctor) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.createAppointment({
        patient_username: user?.username || 'patient_demo',
        patient_name: patientName.trim(),
        patient_phone: patientPhone.trim(),
        doctor_name: doctor.doctor_name,
        specialization: doctor.specialization,
        hospital: doctor.hospital,
        city: doctor.city,
        clinical_indication: clinicalIndication.trim(),
        appointment_slot: appointmentSlot,
      });

      setSuccess(`Consultation booked with ${doctor.doctor_name}! Request sent to doctor's queue.`);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Booking failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-700 to-sky-600 text-white px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-sky-200" />
            <h3 className="font-heading font-bold text-base">Schedule Specialist Consultation</h3>
          </div>
          <button
            onClick={onClose}
            className="text-sky-200 hover:text-white p-1 rounded-lg hover:bg-white/10 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Doctor Summary Pill */}
        <div className="p-4 bg-sky-50/70 border-b border-sky-100 flex items-center justify-between">
          <div>
            <div className="font-heading font-bold text-sm text-slate-900">{doctor.doctor_name}</div>
            <div className="text-xs text-sky-700 font-semibold">{doctor.specialization} &bull; {doctor.hospital}</div>
          </div>
          <div className="text-right">
            <div className="text-xs font-bold text-slate-800">₹{doctor.fees_inr}</div>
            <div className="text-[10px] text-emerald-600 font-bold">● {doctor.availability}</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Patient Full Name *</label>
            <input
              type="text"
              required
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Patient Contact Phone *</label>
            <input
              type="text"
              required
              value={patientPhone}
              onChange={(e) => setPatientPhone(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Clinical Indication / Reason *</label>
            <input
              type="text"
              required
              value={clinicalIndication}
              onChange={(e) => setClinicalIndication(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Preferred Consultation Slot *</label>
            <select
              value={appointmentSlot}
              onChange={(e) => setAppointmentSlot(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:bg-white"
            >
              <option value="Tomorrow 10:30 AM (Priority Slot)">Tomorrow 10:30 AM (Priority Slot)</option>
              <option value="Tomorrow 02:00 PM (Afternoon OPD)">Tomorrow 02:00 PM (Afternoon OPD)</option>
              <option value="Day After Tomorrow 11:00 AM">Day After Tomorrow 11:00 AM</option>
              <option value="Weekend Urgent Consultation">Weekend Urgent Consultation</option>
            </select>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow-md shadow-sky-500/20 transition active:scale-98 disabled:opacity-50"
            >
              {loading ? 'Confirming Slot...' : 'Confirm Appointment Request ➔'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
