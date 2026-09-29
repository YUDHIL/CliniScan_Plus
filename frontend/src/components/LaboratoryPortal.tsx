'use client';

import React, { useState, useEffect } from 'react';
import { UserSession, InferenceResult, Doctor, ScanRecord } from '../types';
import { api } from '../lib/api';
import { 
  FlaskConical, 
  Upload, 
  Sparkles, 
  FileText, 
  CheckCircle2, 
  UserCheck, 
  Layers, 
  ShieldCheck,
  Calendar,
  Activity
} from 'lucide-react';

interface LaboratoryPortalProps {
  user: UserSession;
  cities: string[];
  onViewReport: (data: any) => void;
  samples?: Array<{ filename: string; directory: string; size_bytes: number }>;
}

export const LaboratoryPortal: React.FC<LaboratoryPortalProps> = ({
  user,
  cities,
  onViewReport,
  samples = [],
}) => {
  const [tab, setTab] = useState<'intake' | 'registry' | 'profile'>('intake');
  const [inputMode, setInputMode] = useState<'upload' | 'sample'>('upload');
  const [availableSamples, setAvailableSamples] = useState(samples);
  const [selectedSample, setSelectedSample] = useState<string>(samples[0]?.filename || '');
  
  // Intake state
  const [patientName, setPatientName] = useState('Arthur Pendelton');
  const [patientId, setPatientId] = useState('LAB-PAT-8812');
  const [patientAge, setPatientAge] = useState<number>(52);
  const [patientGender, setPatientGender] = useState('Male');
  const [patientCity, setPatientCity] = useState(user.city || 'Bangalore');
  const [referringDoctor, setReferringDoctor] = useState('St. Jude Respiratory Clinic');
  const [file, setFile] = useState<File | null>(null);
  const [confidence, setConfidence] = useState<number>(0.15);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [scanResult, setScanResult] = useState<InferenceResult | null>(null);
  const [routedSuccess, setRoutedSuccess] = useState<string>('');

  // Registry state
  const [scans, setScans] = useState<ScanRecord[]>([]);

  useEffect(() => {
    if (tab === 'registry') {
      loadRegistry();
    }
  }, [tab]);

  useEffect(() => {
    if (availableSamples.length === 0) {
      api.getSamples().then((res) => {
        if (res.samples && res.samples.length > 0) {
          setAvailableSamples(res.samples);
          if (!selectedSample) setSelectedSample(res.samples[0].filename);
        }
      }).catch(console.warn);
    } else if (!selectedSample && availableSamples.length > 0) {
      setSelectedSample(availableSamples[0].filename);
    }
  }, [availableSamples, selectedSample]);

  const loadRegistry = async () => {
    try {
      const res = await api.getScans(user.username);
      setScans(res.scans || []);
    } catch (e) {
      console.error('Failed to load lab registry', e);
    }
  };

  const handleExecuteLabScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMode === 'upload' && !file) {
      alert('Please upload patient radiograph');
      return;
    }
    if (inputMode === 'sample' && !selectedSample) {
      alert('Please select a test radiograph sample');
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      if (inputMode === 'upload' && file) {
        formData.append('file', file);
      } else {
        formData.append('sample_name', selectedSample);
      }
      formData.append('conf_threshold', confidence.toString());
      formData.append('iou_threshold', '0.45');

      const res = await api.detectXray(formData);
      setScanResult(res);

      // Save to MongoDB
      await api.saveScan({
        username: user.username,
        user_role: 'Laboratory',
        patient_name: patientName.trim(),
        patient_id: patientId.trim(),
        age: patientAge,
        gender: patientGender,
        city: patientCity,
        findings_count: res.findings_count,
        findings: res.detections,
        image_b64: res.annotated_image_b64,
      });
    } catch (err: any) {
      alert(`Lab scan failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };


  const handleRouteReferral = async (doc: Doctor) => {
    if (!scanResult) return;
    try {
      await api.createAppointment({
        patient_username: `pat_${patientId.toLowerCase()}`,
        patient_name: patientName,
        patient_phone: 'Lab Facility Referral',
        doctor_name: doc.doctor_name,
        specialization: doc.specialization,
        hospital: doc.hospital,
        city: doc.city,
        clinical_indication: `Lab Referral (${scanResult.recommendations?.target_findings.join(', ') || 'Chest X-ray'})`,
        appointment_slot: 'Priority Diagnostic Referral',
      });
      setRoutedSuccess(`Referral successfully routed to ${doc.doctor_name} at ${doc.hospital}!`);
      setTimeout(() => setRoutedSuccess(''), 4000);
    } catch (e: any) {
      alert(`Routing failed: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-800 to-teal-700 rounded-2xl p-6 sm:p-8 text-white shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 bg-emerald-500/20 px-3 py-1 rounded-full text-emerald-200 text-xs font-bold uppercase tracking-wider mb-2">
            <FlaskConical className="w-4 h-4 text-emerald-300" />
            <span>Diagnostic Laboratory Portal</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl tracking-tight">
            Laboratory Intake & Automated AI Triage
          </h2>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1">
            Center: <strong className="text-white">{user.full_name}</strong> | Accreditation:{' '}
            <strong className="text-white">{user.license_no || 'LAB-BLR-2026-981'}</strong>
          </p>
        </div>

        {/* Tab switcher */}
        <div className="bg-white/10 backdrop-blur-md p-1 rounded-xl border border-white/20 flex text-xs font-bold">
          <button
            onClick={() => setTab('intake')}
            className={`px-3.5 py-1.5 rounded-lg transition ${
              tab === 'intake' ? 'bg-white text-emerald-900 shadow-sm' : 'text-emerald-100 hover:text-white'
            }`}
          >
            🧪 Patient Intake
          </button>
          <button
            onClick={() => setTab('registry')}
            className={`px-3.5 py-1.5 rounded-lg transition ${
              tab === 'registry' ? 'bg-white text-emerald-900 shadow-sm' : 'text-emerald-100 hover:text-white'
            }`}
          >
            📊 Test Registry
          </button>
        </div>
      </div>

      {routedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold rounded-xl flex items-center space-x-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{routedSuccess}</span>
        </div>
      )}

      {/* TAB 1: INTAKE & TRIAGE */}
      {tab === 'intake' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Intake Form (5 Cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <h3 className="font-heading font-bold text-slate-900 text-base mb-4">
              1. Patient Registration & Radiograph Intake
            </h3>

            <form onSubmit={handleExecuteLabScan} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Patient Full Name *</label>
                <input
                  type="text"
                  required
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500 focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">MRN / Patient ID *</label>
                  <input
                    type="text"
                    required
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500 focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Age</label>
                  <input
                    type="number"
                    value={patientAge}
                    onChange={(e) => setPatientAge(parseInt(e.target.value) || 40)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-emerald-500 focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Gender</label>
                  <select
                    value={patientGender}
                    onChange={(e) => setPatientGender(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">City</label>
                  <select
                    value={patientCity}
                    onChange={(e) => setPatientCity(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                  >
                    {cities.filter(c => c !== 'All Cities').map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Referring Clinic / Physician</label>
                <input
                  type="text"
                  value={referringDoctor}
                  onChange={(e) => setReferringDoctor(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="pt-2">
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-bold text-slate-700">
                    Radiograph Source *
                  </label>
                  <div className="flex bg-slate-100 p-1 rounded-lg text-[11px] font-bold">
                    <button
                      type="button"
                      onClick={() => setInputMode('upload')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        inputMode === 'upload' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600'
                      }`}
                    >
                      📂 Upload
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputMode('sample')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        inputMode === 'sample' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600'
                      }`}
                    >
                      🔬 Demo Sample
                    </button>
                  </div>
                </div>

                {inputMode === 'upload' ? (
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => e.target.files && setFile(e.target.files[0])}
                    className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer"
                  />
                ) : (
                  <div className="space-y-2">
                    <select
                      value={selectedSample}
                      onChange={(e) => setSelectedSample(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium"
                    >
                      {availableSamples.map((s, idx) => (
                        <option key={s.filename} value={s.filename}>
                          Sample #{idx + 1}: {s.filename} ({(s.size_bytes / 1024).toFixed(0)} KB)
                        </option>
                      ))}
                    </select>
                    {selectedSample && (
                      <div className="p-2 bg-slate-50 rounded-lg text-[11px] text-slate-600 flex justify-between">
                        <span className="truncate">Sample: <strong>{selectedSample}</strong></span>
                        <span className="text-emerald-700 font-bold">Ready</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={isProcessing || (inputMode === 'upload' && !file)}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
              >

                {isProcessing ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    <span>Executing YOLO11 Lab Scan...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Run Automated Lab Triage</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Findings & Specialist Routing (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <h3 className="font-heading font-bold text-slate-900 text-base mb-3">
                2. Lab Diagnostic Findings & Certificate
              </h3>

              {scanResult ? (
                <div className="space-y-4">
                  <div className="aspect-[16/9] bg-slate-900 rounded-xl overflow-hidden flex items-center justify-center">
                    <img
                      src={scanResult.annotated_image_b64}
                      alt="Lab Scan"
                      className="w-full h-full object-contain"
                    />
                  </div>

                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-slate-800">
                      Findings Detected: <strong>{scanResult.findings_count}</strong>
                    </span>
                    <button
                      onClick={() => onViewReport({
                        report_id: `LAB-REP-${Math.floor(Math.random() * 900000 + 100000)}`,
                        patient_info: {
                          full_name: patientName,
                          patient_id: patientId,
                          age: patientAge,
                          gender: patientGender,
                          city: patientCity,
                          timestamp: new Date().toLocaleString(),
                        },
                        detection_results: scanResult,
                        annotated_img_b64: scanResult.annotated_image_b64,
                      })}
                      className="inline-flex items-center space-x-1.5 bg-emerald-600 text-white px-3.5 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-700 transition"
                    >
                      <FileText className="w-4 h-4" />
                      <span>Download Official Lab Report</span>
                    </button>
                  </div>

                  {/* Specialist Referral Routing */}
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <h4 className="font-heading font-bold text-sm text-slate-900 mb-2">
                      3. Route Patient to Verified Specialist:
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {(scanResult.recommendations?.doctors || []).slice(0, 4).map((doc, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between text-xs"
                        >
                          <div>
                            <div className="font-bold text-slate-900">{doc.doctor_name}</div>
                            <div className="text-emerald-700 font-semibold">{doc.specialization} &bull; {doc.hospital}</div>
                          </div>
                          <button
                            onClick={() => handleRouteReferral(doc)}
                            className="mt-2.5 w-full py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] rounded-lg shadow-sm transition"
                          >
                            Route Referral ➔
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center text-slate-400 text-xs">
                  Fill patient details and execute scan to generate diagnostic certificate and doctor routes.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REGISTRY */}
      {tab === 'registry' && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <h3 className="font-heading font-bold text-slate-900 text-lg mb-4">
            Laboratory Processed Tests Registry ({scans.length})
          </h3>

          {scans.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No processed scans found for this lab account.</p>
          ) : (
            <div className="space-y-3">
              {scans.map((s) => (
                <div
                  key={s.scan_id}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-900 text-sm">
                      #{s.scan_id} &bull; {s.patient_name} ({s.patient_id})
                    </div>
                    <div className="text-slate-500 mt-0.5">
                      Age: {s.age} &bull; Gender: {s.gender} &bull; City: {s.city} &bull; Findings:{' '}
                      <strong className="text-slate-800">{s.findings_count}</strong>
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">{s.timestamp?.slice(0, 16)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
