'use client';

import React, { useState, useEffect, useRef } from 'react';
import { UserSession, InferenceResult, Doctor } from '../types';
import { api } from '../lib/api';
import { 
  Upload, 
  Sliders, 
  Activity, 
  Sparkles, 
  FileText, 
  Download, 
  AlertTriangle, 
  CheckCircle2, 
  Calendar,
  Layers,
  Eye,
  Crosshair,
  UserCheck,
  Building,
  Star,
  MapPin,
  Clock,
  ShieldCheck,
  Stethoscope,
  Maximize2,
  RefreshCw,
  Cpu,
  Zap,
  Info
} from 'lucide-react';

interface XrayScannerProps {
  user: UserSession | null;
  onBookDoctor: (doctor: Doctor, findingNote?: string) => void;
  onViewReport: (data: any) => void;
  samples: Array<{ filename: string; directory: string; size_bytes: number }>;
}

export const XrayScanner: React.FC<XrayScannerProps> = ({
  user,
  onBookDoctor,
  onViewReport,
  samples = [],
}) => {
  const [inputMode, setInputMode] = useState<'upload' | 'sample'>('upload');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedSample, setSelectedSample] = useState<string>(samples[0]?.filename || '');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0.15);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (samples.length > 0 && !selectedSample) {
      setSelectedSample(samples[0].filename);
    }
  }, [samples]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setSelectedFile(f);
      setPreviewUrl(URL.createObjectURL(f));
      setResult(null);
      setError('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const f = e.dataTransfer.files[0];
      setSelectedFile(f);
      setPreviewUrl(URL.createObjectURL(f));
      setInputMode('upload');
      setResult(null);
      setError('');
    }
  };

  const handleRunInference = async () => {
    setError('');
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('conf_threshold', confidence.toString());
      formData.append('iou_threshold', '0.45');

      if (inputMode === 'upload') {
        if (!selectedFile) {
          throw new Error('Please select or drop an image file to upload.');
        }
        formData.append('file', selectedFile);
      } else {
        if (!selectedSample) {
          throw new Error('Please select a test sample chest radiograph.');
        }
        formData.append('sample_name', selectedSample);
      }

      const res = await api.detectXray(formData);
      setResult(res);

      if (user) {
        try {
          await api.saveScan({
            username: user.username,
            user_role: user.role,
            patient_name: user.full_name,
            patient_id: user.user_id || `PAT-${user.username.toUpperCase()}`,
            age: user.age || 45,
            gender: user.gender || 'Male',
            city: user.city || 'Bangalore',
            findings_count: res.findings_count,
            findings: res.detections,
            image_b64: res.annotated_image_b64,
          });
        } catch (saveErr) {
          console.warn('Could not auto-save scan record:', saveErr);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Inference triage failed. Please verify that the FastAPI backend server is running on port 8000.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8 w-full">
      {/* Top Banner (Expanded & Rich) */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950 to-indigo-950 rounded-3xl p-8 sm:p-12 text-white shadow-2xl relative overflow-hidden border border-slate-800">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center space-x-2.5 bg-sky-500/20 backdrop-blur-md px-4 py-1.5 rounded-full text-sky-300 text-xs sm:text-sm font-black uppercase tracking-wider border border-sky-400/30">
            <Activity className="w-5 h-5 animate-pulse text-sky-400" />
            <span>Ultralytics YOLO11 Deep Learning AI Engine</span>
          </div>

          <h1 className="font-heading text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            AI Chest Radiograph Triage & <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-teal-300">Abnormality Localization</span>
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-4xl leading-relaxed">
            Upload your chest X-ray for sub-second abnormality localization across 10 targeted pulmonary/pleural pathologies, anatomical quadrant mapping, and instant matching with 2,000+ verified hospital specialists.
          </p>

          {/* Quick Specs Pill Row */}
          <div className="pt-3 flex flex-wrap gap-3 text-xs font-bold text-slate-300">
            <span className="bg-white/10 px-3.5 py-1.5 rounded-xl border border-white/10 flex items-center space-x-1.5">
              <Cpu className="w-4 h-4 text-sky-400" />
              <span>Model: YOLO11 Nano Backbone</span>
            </span>
            <span className="bg-white/10 px-3.5 py-1.5 rounded-xl border border-white/10 flex items-center space-x-1.5">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>Inference Time: &lt;250ms</span>
            </span>
            <span className="bg-white/10 px-3.5 py-1.5 rounded-xl border border-white/10 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Dataset: VinBigData (70/15/15 Split)</span>
            </span>
          </div>
        </div>

        <div className="absolute right-6 top-1/2 -translate-y-1/2 opacity-10 pointer-events-none hidden lg:block">
          <Activity className="w-[450px] h-[450px] text-white" />
        </div>
      </div>

      {/* Main Workspace Grid (6 Cols / 6 Cols, Expanded) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start w-full">
        {/* Left Column: Upload Controls (6 Cols) */}
        <div className="xl:col-span-6 bg-white rounded-3xl p-8 sm:p-10 border-2 border-slate-200 shadow-xl space-y-7">
          <div className="space-y-4 pb-5 border-b border-slate-200">
            {/* 1. Header Title & Subtitle */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-2xl bg-sky-100 text-sky-600 flex items-center justify-center shrink-0 shadow-sm border border-sky-200">
                <Crosshair className="w-6 h-6" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-heading font-black text-slate-900 text-xl sm:text-2xl leading-tight">
                  1. Select Radiograph Source
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Upload a patient radiograph or select a pre-loaded sample image
                </p>
              </div>
            </div>

            {/* 2. Mode Switcher Tabs (Full-Width Responsive 2-Segment Control) */}
            <div className="grid grid-cols-2 gap-2 p-1.5 bg-slate-100 rounded-2xl border border-slate-200 text-xs sm:text-sm font-black shadow-inner">
              <button
                type="button"
                onClick={() => {
                  setInputMode('upload');
                  setResult(null);
                  setError('');
                }}
                className={`py-2.5 px-3 sm:px-4 rounded-xl transition cursor-pointer flex items-center justify-center gap-2 ${
                  inputMode === 'upload'
                    ? 'bg-sky-600 text-white shadow-md font-black'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <span>📂</span>
                <span>Upload File</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setInputMode('sample');
                  setResult(null);
                  setError('');
                }}
                className={`py-2.5 px-3 sm:px-4 rounded-xl transition cursor-pointer flex items-center justify-center gap-2 ${
                  inputMode === 'sample'
                    ? 'bg-sky-600 text-white shadow-md font-black'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <span>🔬</span>
                <span>VinBigData Samples</span>
              </button>
            </div>
          </div>

          {inputMode === 'upload' ? (
            <div>
              <input
                ref={fileInputRef}
                type="file"
                id="xray-file-input"
                accept="image/png, image/jpeg, image/jpg, .png, .jpg, .jpeg, .dicom"
                onChange={handleFileChange}
                className="hidden"
              />
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onDrop={handleDrop}
                className="border-3 border-dashed border-sky-300 hover:border-sky-500 bg-sky-50/40 hover:bg-sky-50/70 rounded-3xl p-8 sm:p-12 text-center transition cursor-pointer group shadow-sm hover:shadow-md"
              >
                <div className="w-20 h-20 bg-sky-100 text-sky-600 rounded-3xl flex items-center justify-center mx-auto mb-4 shadow-md group-hover:scale-110 transition">
                  <Upload className="w-10 h-10" />
                </div>
                {selectedFile ? (
                  <div className="space-y-2">
                    <div className="text-base sm:text-lg font-black text-slate-900 font-heading">
                      📁 {selectedFile.name}
                    </div>
                    <div className="text-xs text-sky-700 font-bold bg-sky-100 inline-block px-3 py-1 rounded-full">
                      {(selectedFile.size / 1024).toFixed(0)} KB &bull; Ready for YOLO11 Triage
                    </div>
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          fileInputRef.current?.click();
                        }}
                        className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-xl transition shadow-sm cursor-pointer"
                      >
                        Change Radiograph File
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="text-lg sm:text-xl font-black text-slate-900 font-heading">
                      Click to Browse or Drag & Drop Radiograph
                    </div>
                    <p className="text-xs sm:text-sm text-slate-500 font-semibold max-w-md mx-auto">
                      Supports high-resolution JPEG, PNG, JPG chest X-rays up to 25MB
                    </p>
                    <div className="pt-1">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          fileInputRef.current?.click();
                        }}
                        className="inline-flex items-center space-x-2 bg-sky-600 group-hover:bg-sky-700 text-white px-5 py-2.5 rounded-xl text-xs sm:text-sm font-black shadow-md transition cursor-pointer"
                      >
                        <Upload className="w-4 h-4" />
                        <span>Open File Explorer</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <label className="block text-xs sm:text-sm font-black text-slate-700 uppercase tracking-wider">
                  🔬 Curated VinBigData Clinical Test Cases:
                </label>
                <span className="text-[11px] font-bold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200">
                  {samples.length} Samples Available
                </span>
              </div>

              {/* 1-Click Curated Presets */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {[
                  { id: '006e5626f560c1a2a74f953d71f16c11.jpg', title: 'Case 1: Pleural Effusion', desc: 'Thoracentesis & Fluid Layering', badge: 'High Priority' },
                  { id: '010a3dbb67bc37800a041866844861b1.jpg', title: 'Case 2: Interstitial Lung Disease', desc: 'Reticular Pattern & Fibrosis', badge: 'Chronic' },
                  { id: '01b0510a8d3b0860429536653db5eb21.jpg', title: 'Case 3: Lung Opacity & Nodule', desc: 'Parenchymal Lesion Staging', badge: 'Oncology' },
                  { id: '0204800ac6954c809315ea6e1e6948fe.jpg', title: 'Case 4: Consolidation / Infiltrate', desc: 'Acute Pulmonary Infection', badge: 'Urgent' },
                ].map((c) => {
                  const isCuratedActive = selectedSample === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        setSelectedSample(c.id);
                        setResult(null);
                        setError('');
                      }}
                      className={`text-left p-3 rounded-2xl border-2 transition cursor-pointer ${
                        isCuratedActive
                          ? 'bg-sky-50 border-sky-600 shadow-md ring-2 ring-sky-500/20'
                          : 'bg-slate-50 border-slate-200 hover:border-sky-300 hover:bg-slate-100'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-heading font-bold text-xs text-slate-900">{c.title}</span>
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                          isCuratedActive ? 'bg-sky-600 text-white' : 'bg-slate-200 text-slate-700'
                        }`}>
                          {c.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate">{c.desc}</p>
                    </button>
                  );
                })}
              </div>

              {/* Full Sample Dropdown */}
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Or Choose from All Pre-Loaded Test Radiographs:
                </label>
                <select
                  value={selectedSample}
                  onChange={(e) => {
                    setSelectedSample(e.target.value);
                    setResult(null);
                    setError('');
                  }}
                  className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs sm:text-sm font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition cursor-pointer"
                >
                  {samples.map((s, idx) => (
                    <option key={s.filename} value={s.filename}>
                      Radiograph #{idx + 1}: {s.filename} ({(s.size_bytes / 1024).toFixed(0)} KB)
                    </option>
                  ))}
                </select>
              </div>

              {selectedSample && (
                <div className="p-3 bg-slate-100 rounded-2xl flex items-center justify-between text-xs text-slate-700 font-bold">
                  <span className="truncate">Selected Sample: <strong>{selectedSample}</strong></span>
                  <span className="bg-sky-100 text-sky-800 px-3 py-1 rounded-full text-[10px] font-black flex-shrink-0 ml-2">
                    Ready for YOLO11
                  </span>
                </div>
              )}
            </div>

          )}

          {/* Confidence Slider & Execute Button */}
          <div className="pt-6 border-t border-slate-200 space-y-5">
            <div className="flex justify-between items-center">
              <span className="text-sm sm:text-base font-black text-slate-800 flex items-center space-x-2.5">
                <Sliders className="w-6 h-6 text-sky-600" />
                <span>Detection Confidence Sensitivity Threshold</span>
              </span>
              <span className="text-base font-black text-sky-900 bg-sky-100 px-4 py-1.5 rounded-full border-2 border-sky-300 font-mono">
                {(confidence * 100).toFixed(0)}% Confidence
              </span>
            </div>

            <input
              type="range"
              min="0.05"
              max="0.70"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-full h-3.5 bg-slate-200 rounded-xl appearance-none cursor-pointer accent-sky-600"
            />

            <div className="flex justify-between text-xs sm:text-sm text-slate-500 font-bold px-1">
              <span>5% (High Sensitivity / Early Triage)</span>
              <span>35% (Clinical Balance)</span>
              <span>70% (High Specificity)</span>
            </div>

            {error && (
              <div className="p-5 bg-red-50 border-2 border-red-200 text-red-700 text-sm font-bold rounded-2xl flex items-center space-x-3">
                <AlertTriangle className="w-6 h-6 flex-shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="button"
              onClick={handleRunInference}
              disabled={isAnalyzing || (inputMode === 'upload' && !selectedFile)}
              className="w-full py-5 bg-gradient-to-r from-sky-600 via-sky-700 to-indigo-800 hover:from-sky-700 hover:to-indigo-900 text-white font-heading font-black text-lg sm:text-xl rounded-2xl shadow-xl shadow-sky-600/30 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-3 cursor-pointer"
            >
              {isAnalyzing ? (
                <>
                  <Activity className="w-7 h-7 animate-spin text-white" />
                  <span>Processing Radiograph with YOLO11...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-7 h-7 text-amber-300 fill-amber-300" />
                  <span>Run YOLO11 Diagnostic Triage ➔</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Visual Radiograph Canvas (6 Cols) */}
        <div className="xl:col-span-6 bg-white rounded-3xl p-8 sm:p-10 border-2 border-slate-200 shadow-xl flex flex-col justify-between space-y-6">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div className="flex-1 min-w-0">
                <h3 className="font-heading font-black text-slate-900 text-lg sm:text-xl md:text-2xl flex items-center gap-2.5">
                  <Eye className="w-6 h-6 sm:w-7 sm:h-7 text-sky-600 shrink-0" />
                  <span>Diagnostic Radiograph View</span>
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">High-resolution bounding box localization & canvas</p>
              </div>

              {result && (
                <span className="self-start sm:self-auto bg-slate-900 text-white text-xs sm:text-sm font-mono font-black px-4 py-1.5 rounded-full shadow-md shrink-0">
                  ⚡ {result.inference_time_ms} ms
                </span>
              )}
            </div>

            {/* High-Res Radiograph Canvas View (Responsive & Fully Contained) */}
            <div className="w-full aspect-[4/3] max-h-[520px] bg-slate-950 rounded-3xl overflow-hidden flex items-center justify-center border-4 border-slate-800 relative group shadow-2xl">
              {result ? (
                <img
                  src={result.annotated_image_b64}
                  alt="YOLO11 Annotated Chest Radiograph"
                  className="w-full h-full object-contain"
                />
              ) : (inputMode === 'upload' && previewUrl) ? (
                <img src={previewUrl} alt="Preview" className="w-full h-full object-contain" />
              ) : (inputMode === 'sample' && selectedSample) ? (
                <img
                  src={api.getSampleImageUrl(selectedSample)}
                  alt="Sample Preview"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-center p-8 sm:p-12 text-slate-500 space-y-4">
                  <Activity className="w-16 h-16 sm:w-20 sm:h-20 text-slate-700 mx-auto" />
                  <div>
                    <p className="text-base sm:text-lg font-black text-slate-300">Awaiting Radiograph Input</p>
                    <p className="text-xs sm:text-sm font-semibold text-slate-500 mt-1">Select or upload a radiograph on the left to begin visual inspection</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {result && (
            <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="text-base font-black text-slate-900">
                AI Pathologies Detected:{' '}
                <span className={`px-4 py-1.5 rounded-full text-sm font-black ${
                  result.findings_count > 0 ? 'bg-amber-100 text-amber-900 border-2 border-amber-300' : 'bg-emerald-100 text-emerald-900 border-2 border-emerald-300'
                }`}>
                  {result.findings_count} Abnormality Finding{result.findings_count !== 1 ? 's' : ''}
                </span>
              </div>

              <button
                onClick={() => onViewReport({
                  report_id: `REP-${Math.floor(Math.random() * 900000 + 100000)}`,
                  patient_info: {
                    full_name: user ? user.full_name : 'Hospital Outpatient',
                    patient_id: user?.user_id || 'PAT-DEMO',
                    age: user?.age || 45,
                    gender: user?.gender || 'Male',
                    city: user?.city || 'Bangalore',
                    timestamp: new Date().toLocaleString(),
                  },
                  detection_results: result,
                  annotated_img_b64: result.annotated_image_b64,
                })}
                className="inline-flex items-center space-x-2.5 bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-700 hover:to-sky-800 text-white font-black text-sm px-6 py-3 rounded-2xl shadow-md shadow-sky-600/25 transition active:scale-95 cursor-pointer"
              >
                <FileText className="w-5 h-5 text-sky-200" />
                <span>Download Diagnostic Certificate</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Localized Findings & Doctor Recommendations Section */}
      {result && (
        <div className="space-y-8 animate-fadeIn w-full">
          {/* Localized Pathology Findings */}
          <div className="bg-white rounded-3xl p-8 sm:p-10 border-2 border-slate-200 shadow-xl space-y-6">
            <h3 className="font-heading font-black text-slate-900 text-2xl sm:text-3xl flex items-center space-x-3.5">
              <Layers className="w-8 h-8 text-sky-600" />
              <span>2. Localized AI Pathological Findings ({result.findings_count})</span>
            </h3>

            {result.detections.length === 0 ? (
              <div className="p-8 bg-emerald-50 border-2 border-emerald-200 rounded-3xl flex items-center space-x-5 text-emerald-900">
                <CheckCircle2 className="w-10 h-10 text-emerald-600 flex-shrink-0" />
                <div>
                  <div className="font-heading font-black text-xl">Clear Chest Radiograph &bull; No Target Pathologies Detected</div>
                  <div className="text-sm sm:text-base text-emerald-700 mt-1">
                    No targeted pulmonary or pleural abnormalities exceeded the {(confidence * 100).toFixed(0)}% confidence sensitivity threshold.
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {result.detections.map((f) => (
                  <div
                    key={f.detection_id}
                    className="p-7 rounded-3xl border-2 border-slate-200 hover:border-sky-400 bg-slate-50/70 hover:bg-white transition shadow-sm space-y-4"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center space-x-3">
                        <span className="w-9 h-9 bg-slate-200 text-slate-900 rounded-xl flex items-center justify-center font-black text-sm font-mono">
                          #{f.detection_id}
                        </span>
                        <span className="font-heading font-black text-2xl text-slate-900">{f.class_name}</span>
                      </div>
                      <span className={`text-xs sm:text-sm font-black px-4 py-1.5 rounded-full border ${
                        f.severity === 'Critical' ? 'badge-critical' :
                        f.severity === 'High' ? 'badge-high' :
                        f.severity === 'Moderate-High' ? 'badge-high' :
                        'badge-moderate'
                      }`}>
                        {f.severity}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm text-slate-700 pt-2">
                      <div className="bg-white p-4 rounded-2xl border border-slate-200">
                        <div className="text-slate-400 font-bold uppercase text-[11px]">Detection Confidence</div>
                        <div className="font-black text-slate-900 text-lg mt-0.5">{f.confidence_pct}</div>
                      </div>
                      <div className="bg-white p-4 rounded-2xl border border-slate-200">
                        <div className="text-slate-400 font-bold uppercase text-[11px]">Anatomical Location</div>
                        <div className="font-black text-sky-800 text-sm mt-0.5">{f.location}</div>
                      </div>
                    </div>

                    <div className="pt-2 text-sm text-slate-600 font-medium">
                      <strong className="text-slate-900 font-black">Clinical Protocol:</strong> {f.clinical_urgency}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Prescribed Specialist Recommendation Banner */}
          {result.recommendations && (
            <div className="bg-white rounded-3xl p-8 sm:p-10 border-2 border-slate-200 shadow-xl space-y-6">
              {/* Highlight Hero */}
              <div className="bg-gradient-to-r from-sky-700 via-sky-600 to-indigo-800 rounded-3xl p-8 sm:p-10 text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-xl">
                <div className="space-y-2.5">
                  <div className="text-xs sm:text-sm font-black uppercase tracking-wider text-sky-200 flex items-center space-x-2">
                    <Stethoscope className="w-5 h-5" />
                    <span>Prescribed Specialist Referral Match</span>
                  </div>
                  <h4 className="font-heading text-2xl sm:text-4xl font-black leading-tight">
                    Primary Clinical Field: {result.recommendations.primary_specialty}
                  </h4>
                  <p className="text-sm sm:text-base text-sky-100 max-w-3xl leading-relaxed">
                    {result.recommendations.clinical_summary}
                  </p>
                </div>

                <div className="bg-white/10 backdrop-blur-md px-6 py-4 rounded-2xl border border-white/20 text-right flex-shrink-0">
                  <div className="text-xs uppercase font-bold text-sky-200">Urgency Protocol</div>
                  <div className="text-lg font-black mt-1">{result.recommendations.clinical_urgency}</div>
                </div>
              </div>

              {/* Matched Specialist Cards */}
              <div>
                <h4 className="font-heading font-black text-slate-900 text-xl sm:text-2xl mb-5">
                  Top Recommended Attending Specialists:
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {(result.recommendations.doctors || []).slice(0, 6).map((doc, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-50/70 hover:bg-white p-7 rounded-3xl border-2 border-slate-200 hover:border-sky-500 shadow-sm hover:shadow-lg transition flex flex-col justify-between space-y-5"
                    >
                      <div className="space-y-3.5">
                        <div className="flex justify-between items-start">
                          <div>
                            <h5 className="font-heading font-black text-slate-900 text-lg">{doc.doctor_name}</h5>
                            <span className="text-xs sm:text-sm font-bold text-sky-700">{doc.specialization}</span>
                          </div>
                          <div className="flex items-center space-x-1.5 bg-amber-50 text-amber-900 text-xs sm:text-sm font-black px-3 py-1 rounded-xl border border-amber-200">
                            <Star className="w-4 h-4 fill-amber-500 text-amber-500" />
                            <span>{doc.rating.toFixed(1)}</span>
                          </div>
                        </div>

                        <div className="space-y-2 text-xs sm:text-sm text-slate-600">
                          <div className="flex items-center space-x-2">
                            <Building className="w-4 h-4 text-slate-400 shrink-0" />
                            <span className="truncate">{doc.hospital}, {doc.city}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                            <span>{doc.experience_years} Years Clinical Experience</span>
                          </div>
                          <div className="font-black text-slate-900 text-sm">
                            Consultation Fee: ₹{doc.fees_inr}
                          </div>
                        </div>
                      </div>

                      {/* Action Row: Schedule Consultation + Google Maps Navigation Block */}
                      <div className="pt-2 flex items-center gap-2 w-full">
                        <button
                          type="button"
                          onClick={() => onBookDoctor(doc, `AI Finding: ${result.recommendations.target_findings.join(', ')}`)}
                          className="flex-1 py-3.5 px-3 bg-sky-600 hover:bg-sky-700 text-white font-heading font-black text-xs sm:text-sm rounded-2xl shadow-md shadow-sky-600/20 transition active:scale-95 flex items-center justify-center space-x-1.5 cursor-pointer"
                        >
                          <Calendar className="w-4 h-4 shrink-0" />
                          <span className="truncate">Schedule Consultation ➔</span>
                        </button>

                        {/* Small Google Maps Navigation Block */}
                        <a
                          href={doc.maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${doc.doctor_name} ${doc.hospital} ${doc.city}`)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3.5 py-3.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 hover:text-emerald-950 font-bold text-xs rounded-2xl border border-emerald-300 shadow-sm transition active:scale-95 flex items-center space-x-1.5 cursor-pointer shrink-0"
                          title={`Navigate to ${doc.hospital} on Google Maps`}
                        >
                          <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
                          <span className="font-extrabold">Maps</span>
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
