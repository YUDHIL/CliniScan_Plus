'use client';

import React, { useState, useEffect } from 'react';
import { Doctor } from '../types';
import { api } from '../lib/api';
import { 
  Search, 
  Filter, 
  UserPlus, 
  MapPin, 
  Building, 
  Star, 
  Award, 
  IndianRupee, 
  CheckCircle2, 
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Sparkles,
  Stethoscope
} from 'lucide-react';

interface DoctorDirectoryProps {
  cities: string[];
  specializations: string[];
  hospitals: string[];
  onBookDoctor: (doc: Doctor) => void;
  onOpenRegisterModal: () => void;
}

export const DoctorDirectory: React.FC<DoctorDirectoryProps> = ({
  cities,
  specializations,
  hospitals,
  onBookDoctor,
  onOpenRegisterModal,
}) => {
  const [query, setQuery] = useState('');
  const [city, setCity] = useState('All Cities');
  const [specialization, setSpecialization] = useState('All Specializations');
  const [hospital, setHospital] = useState('All Hospitals');
  const [minRating, setMinRating] = useState<number>(0);
  const [maxFee, setMaxFee] = useState<number | undefined>(undefined);
  const [availability, setAvailability] = useState('All');
  
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchDoctors();
  }, [query, city, specialization, hospital, minRating, maxFee, availability, page]);

  const fetchDoctors = async () => {
    setLoading(true);
    try {
      const res = await api.getDoctors({
        query: query.trim() || undefined,
        city: city !== 'All Cities' ? city : undefined,
        specialization: specialization !== 'All Specializations' ? specialization : undefined,
        hospital: hospital !== 'All Hospitals' ? hospital : undefined,
        min_rating: minRating > 0 ? minRating : undefined,
        max_fee: maxFee,
        availability: availability !== 'All' ? availability : undefined,
        page,
        limit: 12,
      });

      setDoctors(res.doctors || []);
      setTotalCount(res.total_count || 0);
      setTotalPages(res.total_pages || 1);
    } catch (e) {
      console.error('Failed to fetch doctors', e);
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setQuery('');
    setCity('All Cities');
    setSpecialization('All Specializations');
    setHospital('All Hospitals');
    setMinRating(0);
    setMaxFee(undefined);
    setAvailability('All');
    setPage(1);
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <div className="flex items-center space-x-2 text-sky-600 mb-1">
            <Stethoscope className="w-5 h-5" />
            <span className="text-xs font-black uppercase tracking-wider">Hospital Specialist Directory</span>
          </div>
          <h2 className="font-heading font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
            2,000+ Verified Clinical Specialists
          </h2>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            Search, filter, and schedule appointments with certified specialists across 26 major cities and 10 premier hospital networks.
          </p>
        </div>

        <button
          onClick={onOpenRegisterModal}
          className="inline-flex items-center space-x-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-extrabold px-6 py-3.5 rounded-2xl shadow-lg shadow-emerald-600/25 transition active:scale-95 cursor-pointer flex-shrink-0"
        >
          <UserPlus className="w-5 h-5" />
          <span>+ Register Specialist</span>
        </button>
      </div>

      {/* Filter Workspace */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-md space-y-5">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-6 h-6 absolute left-4 top-3.5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search by doctor name, medical specialization, disease expertise, hospital, or city..."
            className="w-full pl-12 pr-5 py-3.5 bg-slate-50 border-2 border-slate-200 rounded-2xl text-sm sm:text-base font-medium focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
          />
        </div>

        {/* Dropdowns Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div>
            <label className="block text-xs font-extrabold text-slate-600 uppercase mb-1.5">City</label>
            <select
              value={city}
              onChange={(e) => { setCity(e.target.value); setPage(1); }}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
            >
              {cities.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-extrabold text-slate-600 uppercase mb-1.5">Specialization</label>
            <select
              value={specialization}
              onChange={(e) => { setSpecialization(e.target.value); setPage(1); }}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
            >
              {specializations.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-extrabold text-slate-600 uppercase mb-1.5">Hospital</label>
            <select
              value={hospital}
              onChange={(e) => { setHospital(e.target.value); setPage(1); }}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
            >
              {hospitals.map((h) => (
                <option key={h} value={h}>{h}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-extrabold text-slate-600 uppercase mb-1.5">Min Rating</label>
            <select
              value={minRating}
              onChange={(e) => { setMinRating(parseFloat(e.target.value)); setPage(1); }}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
            >
              <option value="0">All Ratings</option>
              <option value="4.0">★ 4.0 & Above</option>
              <option value="4.5">★ 4.5 & Above</option>
              <option value="4.8">★ 4.8 & Above</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-extrabold text-slate-600 uppercase mb-1.5">Max Fee (₹)</label>
            <input
              type="number"
              placeholder="Max ₹"
              value={maxFee || ''}
              onChange={(e) => {
                const v = parseInt(e.target.value);
                setMaxFee(isNaN(v) ? undefined : v);
                setPage(1);
              }}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
            />
          </div>

          <div>
            <label className="block text-xs font-extrabold text-slate-600 uppercase mb-1.5">Availability</label>
            <select
              value={availability}
              onChange={(e) => { setAvailability(e.target.value); setPage(1); }}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-800"
            >
              <option value="All">All Statuses</option>
              <option value="Available">● Available Now</option>
              <option value="Busy">● Busy</option>
            </select>
          </div>
        </div>

        {/* Counter and reset */}
        <div className="flex justify-between items-center pt-2 text-xs sm:text-sm text-slate-500 font-medium">
          <div>
            Showing <strong className="text-slate-900 font-extrabold">{doctors.length}</strong> of{' '}
            <strong className="text-slate-900 font-extrabold">{totalCount}</strong> verified doctors
          </div>
          {(query || city !== 'All Cities' || specialization !== 'All Specializations' || hospital !== 'All Hospitals' || minRating > 0 || maxFee) && (
            <button
              onClick={handleResetFilters}
              className="text-sky-600 font-extrabold hover:underline"
            >
              Reset All Filters
            </button>
          )}
        </div>
      </div>

      {/* Doctor Cards Grid */}
      {loading ? (
        <div className="py-24 text-center text-slate-500 space-y-3">
          <div className="w-10 h-10 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-extrabold">Searching 2,000-Doctor Directory...</p>
        </div>
      ) : doctors.length === 0 ? (
        <div className="bg-white rounded-3xl p-16 text-center border border-slate-200 space-y-3">
          <p className="text-base font-extrabold text-slate-800">No specialists matched your criteria.</p>
          <button
            onClick={handleResetFilters}
            className="text-sm text-sky-600 font-extrabold hover:underline"
          >
            Clear filters to view all doctors
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doc, idx) => (
            <div
              key={idx}
              className="bg-white rounded-3xl p-7 border-2 border-slate-200/90 hover:border-sky-400 shadow-md hover:shadow-xl transition flex flex-col justify-between space-y-5"
            >
              <div className="space-y-4">
                {/* Header */}
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-heading font-extrabold text-lg text-slate-900 leading-tight">
                      {doc.doctor_name}
                    </h3>
                    <div className="text-xs sm:text-sm font-extrabold text-sky-600 mt-1">{doc.specialization}</div>
                  </div>
                  <div className="flex items-center space-x-1.5 bg-amber-50 text-amber-900 text-xs font-black px-3 py-1 rounded-xl border border-amber-200">
                    <Star className="w-4 h-4 fill-amber-500 text-amber-500" />
                    <span>{doc.rating.toFixed(1)}</span>
                  </div>
                </div>

                {/* Sub-specialty expertise badge */}
                <div className="bg-slate-50 rounded-xl px-3.5 py-2 text-xs text-slate-700 border border-slate-200/60">
                  <span className="text-slate-400 font-bold uppercase text-[10px]">Pathology Expertise:</span>{' '}
                  <span className="font-extrabold text-slate-900 block mt-0.5">{doc.disease_expertise}</span>
                </div>

                {/* Meta list */}
                <div className="space-y-2 text-xs sm:text-sm text-slate-600">
                  <div className="flex items-center space-x-2">
                    <Building className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <span>{doc.hospital}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <span>{doc.city}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Award className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <span>{doc.experience_years} Years Clinical Experience</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <IndianRupee className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <span className="font-extrabold text-slate-900">₹{doc.fees_inr} Consultation</span>
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <span className={`text-xs font-extrabold px-3 py-1 rounded-full border ${
                  doc.availability.toLowerCase() === 'available'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : 'bg-slate-100 text-slate-600 border-slate-200'
                }`}>
                  ● {doc.availability}
                </span>

                <div className="flex items-center gap-2">
                  <a
                    href={doc.maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${doc.doctor_name} ${doc.hospital} ${doc.city}`)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-xl border border-emerald-300 transition active:scale-95 flex items-center space-x-1 text-xs font-bold cursor-pointer"
                    title={`View ${doc.hospital} on Google Maps`}
                  >
                    <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Maps</span>
                  </a>

                  <button
                    onClick={() => onBookDoctor(doc)}
                    className="inline-flex items-center space-x-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs sm:text-sm font-extrabold px-4 py-2.5 rounded-xl shadow-md shadow-sky-600/25 transition active:scale-95 cursor-pointer"
                  >
                    <Calendar className="w-4 h-4" />
                    <span>Book Slot</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-3 pt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-3 rounded-xl border-2 border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-40 transition font-bold"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="text-sm font-extrabold text-slate-700 px-4">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="p-3 rounded-xl border-2 border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-40 transition font-bold"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
};
