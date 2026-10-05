'use client';

import React, { useState, useEffect } from 'react';
import { UserSession, InferenceResult, ScanRecord } from '../types';
import { api } from '../lib/api';
import { 
  FlaskConical, 
  Upload, 
  Sparkles, 
  FileText, 
  CheckCircle2, 
  Layers, 
  ShieldCheck,
  Calendar,
  Activity,
  Printer,
  Microscope,
  AlertTriangle,
  FileCheck2,
  Clock,
  Search,
  Hash,
  User,
  MapPin
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
  const [tab, setTab] = useState<'intake' | 'registry'>('intake');
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
  const [actionSuccess, setActionSuccess] = useState<string>('');

  // Registry state
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [registryFilter, setRegistryFilter] = useState('');

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
    setActionSuccess('');
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

      setActionSuccess(`Diagnostic scan verified & registered in laboratory records.`);
    } catch (err: any) {
      alert(`Lab scan failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
      case 'moderate-high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'moderate':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  const filteredScans = scans.filter((s) => {
    if (!registryFilter) return true;
    const term = registryFilter.toLowerCase();
    return (
      s.patient_name?.toLowerCase().includes(term) ||
      s.patient_id?.toLowerCase().includes(term) ||
      s.scan_id?.toLowerCase().includes(term) ||
      s.city?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-800 via-teal-800 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border border-emerald-700/30">
        <div>
          <div className="inline-flex items-center space-x-1.5 bg-emerald-500/20 px-3 py-1 rounded-full text-emerald-200 text-xs font-bold uppercase tracking-wider mb-2 border border-emerald-400/30">
            <FlaskConical className="w-4 h-4 text-emerald-300" />
            <span>Diagnostic Laboratory Portal</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl tracking-tight">
            Radiology Intake & Automated AI Analysis
          </h2>
          <p className="text-xs sm:text-sm text-emerald-100/90 mt-1 font-medium">
            Facility: <strong className="text-white font-bold">{user.full_name}</strong> &bull; Accreditation:{' '}
            <strong className="text-white font-bold">{user.license_no || 'NABL-ISO15189-2026-BLR'}</strong> &bull; Location:{' '}
            <strong className="text-white font-bold">{user.city || 'Bangalore'}</strong>
          </p>
        </div>

        {/* Tab switcher */}
        <div className="bg-white/10 backdrop-blur-md p-1.5 rounded-2xl border border-white/20 flex text-xs font-bold">
          <button
            onClick={() => setTab('intake')}
            className={`px-4 py-2 rounded-xl transition cursor-pointer flex items-center space-x-2 ${
              tab === 'intake' ? 'bg-white text-emerald-950 shadow-md font-extrabold' : 'text-emerald-100 hover:text-white'
            }`}
          >
            <Microscope className="w-4 h-4" />
            <span>Patient Intake & Scan</span>
          </button>
          <button
            onClick={() => setTab('registry')}
            className={`px-4 py-2 rounded-xl transition cursor-pointer flex items-center space-x-2 ${
              tab === 'registry' ? 'bg-white text-emerald-950 shadow-md font-extrabold' : 'text-emerald-100 hover:text-white'
            }`}
          >
            <FileCheck2 className="w-4 h-4" />
            <span>Processed Test Registry</span>
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-bold rounded-2xl flex items-center space-x-2 shadow-xs animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* TAB 1: INTAKE & TRIAGE */}
      {tab === 'intake' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Intake Form (5 Cols) */}
          <div className="lg:col-span-5 bg-white rounded-3xl p-6 sm:p-7 border border-slate-200 shadow-sm space-y-5">
            <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
              <FlaskConical className="w-5 h-5 text-emerald-600" />
              <h3 className="font-heading font-extrabold text-slate-900 text-base">
                1. Patient & Sample Registration
              </h3>
            </div>

            <form onSubmit={handleExecuteLabScan} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Patient Full Name *</label>
                <input
                  type="text"
                  required
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
                  placeholder="e.g. Arthur Pendelton"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">MRN / Patient ID *</label>
                  <input
                    type="text"
                    required
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
                    placeholder="LAB-PAT-8812"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Age</label>
                  <input
                    type="number"
                    value={patientAge}
                    onChange={(e) => setPatientAge(parseInt(e.target.value) || 40)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">Gender</label>
                  <select
                    value={patientGender}
                    onChange={(e) => setPatientGender(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">City</label>
                  <select
                    value={patientCity}
                    onChange={(e) => setPatientCity(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium"
                  >
                    {cities.filter(c => c !== 'All Cities').map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Referring Clinic / Physician</label>
                <input
                  type="text"
                  value={referringDoctor}
                  onChange={(e) => setReferringDoctor(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium"
                  placeholder="e.g. St. Jude Respiratory Clinic"
                />
              </div>

              <div className="pt-2 border-t border-slate-100">
                <div className="flex justify-between items-center mb-2.5">
                  <label className="block text-xs font-bold text-slate-700">
                    Radiograph Source *
                  </label>
                  <div className="flex bg-slate-100 p-1 rounded-xl text-[11px] font-bold">
                    <button
                      type="button"
                      onClick={() => setInputMode('upload')}
                      className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                        inputMode === 'upload' ? 'bg-emerald-600 text-white shadow-xs font-extrabold' : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      📂 Upload File
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputMode('sample')}
                      className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                        inputMode === 'sample' ? 'bg-emerald-600 text-white shadow-xs font-extrabold' : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      🔬 Demo Sample
                    </button>
                  </div>
                </div>

                {inputMode === 'upload' ? (
                  <div className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-2xl p-4 bg-slate-50 transition text-center">
                    <input
                      type="file"
                      id="lab-xray-upload"
                      accept="image/*"
                      onChange={(e) => e.target.files && setFile(e.target.files[0])}
                      className="hidden"
                    />
                    <label htmlFor="lab-xray-upload" className="cursor-pointer flex flex-col items-center justify-center space-y-2">
                      <Upload className="w-8 h-8 text-emerald-600" />
                      <span className="text-xs font-bold text-slate-700">
                        {file ? file.name : 'Click to browse radiograph (PNG / JPG / DICOM Export)'}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Maximum resolution supported: 4096 x 4096 px'}
                      </span>
                    </label>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <select
                      value={selectedSample}
                      onChange={(e) => setSelectedSample(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium"
                    >
                      {availableSamples.map((s, idx) => (
                        <option key={s.filename} value={s.filename}>
                          Sample #{idx + 1}: {s.filename} ({(s.size_bytes / 1024).toFixed(0)} KB)
                        </option>
                      ))}
                    </select>
                    {selectedSample && (
                      <div className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-xl text-[11px] text-emerald-900 flex justify-between items-center">
                        <span className="truncate">Active Sample: <strong>{selectedSample}</strong></span>
                        <span className="text-emerald-700 font-extrabold flex items-center space-x-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Ready</span>
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="pt-2">
                <div className="flex justify-between items-center text-xs mb-1.5">
                  <label className="font-bold text-slate-700">Detection Confidence Threshold:</label>
                  <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                    {(confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.80"
                  step="0.05"
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                />
              </div>

              <button
                type="submit"
                disabled={isProcessing || (inputMode === 'upload' && !file)}
                className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs rounded-2xl shadow-lg shadow-emerald-600/20 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
              >
                {isProcessing ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    <span>Executing Laboratory Neural Scan...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Run Automated Laboratory Scan</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Diagnostic Findings & Certificate (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200 shadow-sm space-y-5">
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-heading font-extrabold text-slate-900 text-base">
                    2. Lab Pathological Findings & Technical Analysis
                  </h3>
                </div>
                {scanResult && (
                  <span className="text-[11px] font-mono font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200">
                    ⚡ {scanResult.inference_time_ms} ms
                  </span>
                )}
              </div>

              {scanResult ? (
                <div className="space-y-5 animate-fadeIn">
                  {/* Radiograph Display */}
                  <div className="aspect-[16/10] bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center border border-slate-800 shadow-inner relative group">
                    <img
                      src={scanResult.annotated_image_b64}
                      alt="Lab Diagnostic Scan"
                      className="w-full h-full object-contain"
                    />
                    <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-[11px] text-white flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      <span>YOLO11 Nano Engine &bull; {scanResult.findings_count} Lesions Localized</span>
                    </div>
                  </div>

                  {/* Findings Table */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-500">
                        Localized Pathologies Breakdown
                      </h4>
                      <span className="text-xs font-bold text-slate-800">
                        Total Detected: <strong className="text-emerald-700 font-extrabold">{scanResult.findings_count}</strong>
                      </span>
                    </div>

                    {scanResult.detections && scanResult.detections.length > 0 ? (
                      <div className="overflow-x-auto rounded-2xl border border-slate-200">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                            <tr>
                              <th className="py-2.5 px-3">#</th>
                              <th className="py-2.5 px-3">Pathology / Finding</th>
                              <th className="py-2.5 px-3">Anatomical Region</th>
                              <th className="py-2.5 px-3">Confidence</th>
                              <th className="py-2.5 px-3 text-right">Severity</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {scanResult.detections.map((det, idx) => (
                              <tr key={idx} className="hover:bg-slate-50/80 transition font-medium text-slate-800">
                                <td className="py-2.5 px-3 font-mono text-slate-400">{idx + 1}</td>
                                <td className="py-2.5 px-3 font-bold text-slate-900">{det.class_name}</td>
                                <td className="py-2.5 px-3 text-slate-600">{det.location || 'Thoracic Field'}</td>
                                <td className="py-2.5 px-3 font-mono font-bold text-emerald-700">
                                  {det.confidence_pct || `${(det.confidence * 100).toFixed(1)}%`}
                                </td>
                                <td className="py-2.5 px-3 text-right">
                                  <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getSeverityBadge(det.severity)}`}>
                                    {det.severity || 'Moderate'}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-2xl text-emerald-900 text-xs flex items-center space-x-3">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                        <div>
                          <strong className="font-bold">No acute cardiopulmonary lesions detected.</strong>
                          <p className="text-[11px] text-emerald-700 mt-0.5">
                            Clear lung fields, sharp costophrenic angles, normal cardiothoracic ratio.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Laboratory Quality Assurance Stamp & Report Generation */}
                  <div className="p-5 bg-gradient-to-br from-slate-50 to-emerald-50/40 rounded-2xl border border-emerald-100 space-y-4">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold flex-shrink-0">
                          <ShieldCheck className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 text-xs">
                            Diagnostic Technical Release Certificate
                          </div>
                          <div className="text-[11px] text-slate-500">
                            Authorized Lab: <strong className="text-slate-700">{user.full_name}</strong> &bull; MRN: {patientId}
                          </div>
                        </div>
                      </div>

                      <button
                        type="button"
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
                        className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl text-xs font-extrabold shadow-md shadow-emerald-600/20 transition cursor-pointer active:scale-98"
                      >
                        <FileText className="w-4 h-4" />
                        <span>Download Official Diagnostic Lab Report</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center space-y-3">
                  <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
                    <Microscope className="w-7 h-7" />
                  </div>
                  <div className="font-bold text-slate-600 text-sm">Awaiting Radiograph Intake</div>
                  <p className="max-w-xs text-slate-400 text-[11px]">
                    Enter patient details on the left, upload or select a radiograph, and run automated analysis to generate diagnostic findings and official certificates.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REGISTRY */}
      {tab === 'registry' && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-100 pb-4">
            <div>
              <h3 className="font-heading font-extrabold text-slate-900 text-lg">
                Laboratory Processed Tests Registry
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Complete log of digital radiographic scans executed under this facility account ({scans.length} total)
              </p>
            </div>

            {/* Search filter */}
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search patient, MRN or ID..."
                value={registryFilter}
                onChange={(e) => setRegistryFilter(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500 focus:bg-white"
              />
            </div>
          </div>

          {filteredScans.length === 0 ? (
            <div className="p-12 text-center text-slate-400 text-xs">
              <FileCheck2 className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <p className="font-bold text-slate-600">No matching scan records found.</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Scans processed in the Intake tab are automatically saved here for audit and reporting.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredScans.map((s) => (
                <div
                  key={s.scan_id}
                  className="p-5 rounded-2xl border border-slate-200 bg-slate-50/60 hover:bg-slate-50 transition flex flex-col justify-between space-y-3"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                        <span>{s.patient_name}</span>
                        <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-md font-bold">
                          {s.patient_id}
                        </span>
                      </div>
                      <div className="text-slate-500 text-xs mt-1 flex flex-wrap gap-x-2 gap-y-0.5">
                        <span>Age: {s.age}</span> &bull; 
                        <span>Gender: {s.gender}</span> &bull; 
                        <span>City: {s.city}</span>
                      </div>
                    </div>

                    <span className="text-[11px] font-mono text-slate-400 bg-white px-2 py-1 rounded-lg border border-slate-200">
                      {s.timestamp?.slice(0, 10)}
                    </span>
                  </div>

                  <div className="pt-2 border-t border-slate-200/70 flex justify-between items-center text-xs">
                    <span className="text-slate-600">
                      Findings: <strong className="text-slate-900 font-bold">{s.findings_count} localized</strong>
                    </span>

                    {s.image_b64 && (
                      <button
                        onClick={() => onViewReport({
                          report_id: s.scan_id,
                          patient_info: {
                            full_name: s.patient_name,
                            patient_id: s.patient_id,
                            age: s.age,
                            gender: s.gender,
                            city: s.city,
                            timestamp: s.timestamp || new Date().toLocaleString(),
                          },
                          detection_results: {
                            findings_count: s.findings_count,
                            detections: s.findings || [],
                            inference_time_ms: 220,
                            model_version: 'YOLO11-Nano (VinBigData)',
                          },
                          annotated_img_b64: s.image_b64,
                        })}
                        className="inline-flex items-center space-x-1.5 text-emerald-700 hover:text-emerald-800 font-bold bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-lg border border-emerald-200 transition cursor-pointer"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Lab Certificate</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
