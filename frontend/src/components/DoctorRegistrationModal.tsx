'use client';

import React, { useState } from 'react';
import { api } from '../lib/api';
import { 
  X, 
  UserPlus, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles,
  Stethoscope
} from 'lucide-react';

interface DoctorRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  cities: string[];
  specializations: string[];
  hospitals: string[];
}

export const DoctorRegistrationModal: React.FC<DoctorRegistrationModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  cities,
  specializations,
  hospitals,
}) => {
  const [name, setName] = useState('');
  const [specialization, setSpecialization] = useState(specializations[0] || 'Pulmonologist');
  const [hospital, setHospital] = useState(hospitals[0] || 'AIIMS Hospital');
  const [city, setCity] = useState(cities.filter(c => c !== 'All Cities')[0] || 'Bangalore');
  const [experience, setExperience] = useState(15);
  const [fees, setFees] = useState(800);
  const [disease, setDisease] = useState('');
  const [availability, setAvailability] = useState('Available');

  const [customUsername, setCustomUsername] = useState('');
  const [customEmail, setCustomEmail] = useState('');
  const [customPassword, setCustomPassword] = useState('Doctor123!');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successInfo, setSuccessInfo] = useState<any>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please enter doctor full name.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const cleanName = name.trim().startsWith('Dr. ') ? name.trim() : `Dr. ${name.trim()}`;
      const res = await api.registerSpecialist({
        Doctor_Name: cleanName,
        Specialization: specialization,
        Experience: experience,
        Fees: fees,
        Hospital: hospital,
        City: city,
        Disease: disease.trim() || specialization,
        Availability: availability,
        username: customUsername.trim() || undefined,
        email: customEmail.trim() || undefined,
        password: customPassword.trim() || 'Doctor123!',
      });

      setSuccessInfo(res.doctor);
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8">
        <div className="bg-gradient-to-r from-emerald-700 to-teal-700 text-white px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Stethoscope className="w-5 h-5 text-emerald-200" />
            <h3 className="font-heading font-bold text-base">Register Specialist Into Healthcare Directory</h3>
          </div>
          <button onClick={onClose} className="text-emerald-200 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successInfo && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl space-y-1">
              <div className="font-bold flex items-center space-x-1.5 text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Specialist Registered Successfully!</span>
              </div>
              <div>Username: <code className="font-bold">@{successInfo.username}</code> &bull; Password: <code className="font-bold">{successInfo.password}</code></div>
              <p className="text-[11px] text-emerald-700">Doctor is now active across 2,000-doctor search and live AI recommendations.</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Doctor Full Name *</label>
              <input
                type="text"
                required
                placeholder="Dr. Rajeshwari Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Medical Specialization *</label>
              <select
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              >
                {specializations.filter(s => s !== 'All Specializations').map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Hospital Network *</label>
              <select
                value={hospital}
                onChange={(e) => setHospital(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              >
                {hospitals.filter(h => h !== 'All Hospitals').map(h => (
                  <option key={h} value={h}>{h}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Practice City *</label>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              >
                {cities.filter(c => c !== 'All Cities').map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Experience (Yrs)</label>
              <input
                type="number"
                min="1"
                max="50"
                value={experience}
                onChange={(e) => setExperience(parseInt(e.target.value) || 15)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Consultation Fee (₹)</label>
              <input
                type="number"
                min="100"
                max="5000"
                step="50"
                value={fees}
                onChange={(e) => setFees(parseInt(e.target.value) || 800)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Availability</label>
              <select
                value={availability}
                onChange={(e) => setAvailability(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              >
                <option value="Available">Available</option>
                <option value="Busy">Busy</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Pathology / Disease Expertise</label>
            <input
              type="text"
              placeholder="e.g. Pleural effusion, Pulmonary fibrosis"
              value={disease}
              onChange={(e) => setDisease(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition active:scale-98 disabled:opacity-50"
            >
              {loading ? 'Registering & Syncing Datasets...' : '➕ Register Specialist & Sync Network ➔'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
