'use client';

import React, { useState } from 'react';
import { UserSession } from '../types';
import { api } from '../lib/api';
import { 
  User, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  Key, 
  Building,
  Phone,
  Mail,
  MapPin
} from 'lucide-react';

interface ProfileSettingsProps {
  user: UserSession;
  cities: string[];
  specializations: string[];
  hospitals: string[];
  onUpdateSuccess: (updatedUser: UserSession) => void;
}

export const ProfileSettings: React.FC<ProfileSettingsProps> = ({
  user,
  cities,
  specializations,
  hospitals,
  onUpdateSuccess,
}) => {
  const [formData, setFormData] = useState({
    full_name: user.full_name || '',
    email: user.email || '',
    phone: user.phone || '',
    city: user.city || 'Bangalore',
    age: user.age || 45,
    gender: user.gender || 'Male',
    specialization: user.specialization || 'Pulmonologist',
    hospital: user.hospital || 'AIIMS Hospital',
    experience_years: user.experience_years || 15,
    fees_inr: user.fees_inr || 800,
    availability: user.availability || 'Available',
    disease_expertise: user.disease_expertise || 'Respiratory Evaluation',
    license_no: user.license_no || 'LAB-BLR-2026',
    new_password: '',
    confirm_password: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.new_password && formData.new_password !== formData.confirm_password) {
      setError('New password and confirmation do not match.');
      return;
    }

    setLoading(true);
    try {
      const updates: any = {
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim(),
        city: formData.city,
      };

      if (user.role === 'Patient') {
        updates.age = Number(formData.age);
        updates.gender = formData.gender;
      } else if (user.role === 'Doctor') {
        updates.specialization = formData.specialization;
        updates.hospital = formData.hospital;
        updates.experience_years = Number(formData.experience_years);
        updates.fees_inr = Number(formData.fees_inr);
        updates.availability = formData.availability;
        updates.disease_expertise = formData.disease_expertise;
      } else if (user.role === 'Laboratory') {
        updates.license_no = formData.license_no;
      }

      const res = await api.updateProfile(
        user.username,
        updates,
        formData.new_password.trim() || undefined
      );

      if (res.user) {
        setSuccess('Profile updated successfully and synced across network!');
        onUpdateSuccess(res.user);
      }
    } catch (err: any) {
      setError(err.message || 'Profile update failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <h2 className="font-heading font-extrabold text-2xl text-slate-900 tracking-tight">
          Account Profile & Facility Settings
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Manage your personal details, hospital coordinates, and role-specific clinical credentials.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Contact Phone *</label>
                <input
                  type="text"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">City Location *</label>
                <select
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                >
                  {cities.filter(c => c !== 'All Cities').map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Role specific section */}
            {user.role === 'Doctor' && (
              <div className="p-4 bg-sky-50/60 border border-sky-200 rounded-xl space-y-3">
                <div className="text-xs font-bold text-sky-900">🩺 Clinical Practice Information</div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">Specialization</label>
                    <select
                      value={formData.specialization}
                      onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md text-xs"
                    >
                      {specializations.filter(s => s !== 'All Specializations').map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">Hospital Network</label>
                    <select
                      value={formData.hospital}
                      onChange={(e) => setFormData({ ...formData, hospital: e.target.value })}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md text-xs"
                    >
                      {hospitals.filter(h => h !== 'All Hospitals').map(h => (
                        <option key={h} value={h}>{h}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">Experience (Yrs)</label>
                    <input
                      type="number"
                      value={formData.experience_years}
                      onChange={(e) => setFormData({ ...formData, experience_years: parseInt(e.target.value) || 10 })}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">Fee (₹)</label>
                    <input
                      type="number"
                      step="50"
                      value={formData.fees_inr}
                      onChange={(e) => setFormData({ ...formData, fees_inr: parseInt(e.target.value) || 800 })}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 mb-1">Availability</label>
                    <select
                      value={formData.availability}
                      onChange={(e) => setFormData({ ...formData, availability: e.target.value })}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-md text-xs"
                    >
                      <option value="Available">Available</option>
                      <option value="Busy">Busy</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Password update section */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
              <div className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                <Key className="w-3.5 h-3.5 text-slate-500" />
                <span>Security & Password (Optional)</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="password"
                  placeholder="New password"
                  value={formData.new_password}
                  onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs"
                />
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={formData.confirm_password}
                  onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="py-2.5 px-6 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow-md shadow-sky-500/20 transition active:scale-98 disabled:opacity-50 flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>{loading ? 'Saving Profile...' : 'Save Changes'}</span>
            </button>
          </form>
        </div>

        {/* Profile Pass Card (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-sky-600 text-white rounded-2xl flex items-center justify-center font-bold text-lg shadow-md shadow-sky-600/20">
                {user.full_name?.charAt(0) || 'U'}
              </div>
              <div>
                <h4 className="font-heading font-bold text-base text-slate-900 leading-tight">{user.full_name}</h4>
                <span className="text-xs font-bold text-sky-600">{user.role} Pass</span>
              </div>
            </div>

            <div className="space-y-2 text-xs text-slate-600 pt-3 border-t border-slate-100">
              <div><strong>User ID:</strong> <code className="bg-slate-100 px-1.5 py-0.5 rounded">{user.user_id || `@${user.username}`}</code></div>
              <div><strong>Username:</strong> @{user.username}</div>
              <div><strong>City:</strong> {user.city}</div>
              {user.role === 'Doctor' && (
                <>
                  <div><strong>Hospital:</strong> {user.hospital}</div>
                  <div><strong>Specialty:</strong> {user.specialization}</div>
                </>
              )}
            </div>
          </div>

          <div className="mt-6 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
            Authenticated via MongoDB Persistent Store
          </div>
        </div>
      </div>
    </div>
  );
};
