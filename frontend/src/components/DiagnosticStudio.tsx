'use client';

import React, { useState, useEffect, useRef } from 'react';
import { UserSession, InferenceResult } from '../types';
import { api } from '../lib/api';
import { 
  Sparkles, 
  Upload, 
  Sliders, 
  Activity, 
  FileText, 
  CheckCircle2, 
  AlertTriangle,
  Stethoscope
} from 'lucide-react';

interface DiagnosticStudioProps {
  user: UserSession;
  activeDoctorName: string;
  onViewReport: (data: any) => void;
  samples?: Array<{ filename: string; directory: string; size_bytes: number }>;
}

export const DiagnosticStudio: React.FC<DiagnosticStudioProps> = ({
  user,
  activeDoctorName,
  onViewReport,
  samples = [],
}) => {
  const [inputMode, setInputMode] = useState<'upload' | 'sample'>('upload');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [selectedSample, setSelectedSample] = useState<string>(samples[0]?.filename || '');
  const [availableSamples, setAvailableSamples] = useState(samples);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0.15);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [error, setError] = useState<string>('');

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      setPreviewUrl(URL.createObjectURL(f));
      setResult(null);
      setError('');
    }
  };

  const handleRunStudioTriage = async () => {
    if (inputMode === 'upload' && !file) {
      setError('Please upload a patient chest radiograph.');
      return;
    }
    if (inputMode === 'sample' && !selectedSample) {
      setError('Please select a sample radiograph.');
      return;
    }

    setError('');
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
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Diagnostic scan execution failed.');
    } finally {
      setIsProcessing(false);
    }
  };


  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-slate-900 to-sky-950 rounded-2xl p-6 sm:p-8 text-white shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 bg-sky-500/20 px-3 py-1 rounded-full text-sky-300 text-xs font-bold uppercase tracking-wider mb-2 border border-sky-400/20">
            <Stethoscope className="w-4 h-4 text-sky-400" />
            <span>Physician Diagnostic Studio</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl tracking-tight">
            High-Resolution Clinical Radiograph Studio
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 mt-1">
            Attending Specialist: <strong className="text-sky-300">{activeDoctorName}</strong> ({user.specialization || 'Pulmonologist'})
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upload & Settings (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-slate-100">
            <h3 className="font-heading font-bold text-slate-900 text-base">
              Patient Radiograph Intake
            </h3>
            <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-bold">
              <button
                type="button"
                onClick={() => {
                  setInputMode('upload');
                  setResult(null);
                }}
                className={`px-3 py-1.5 rounded-lg transition ${
                  inputMode === 'upload' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-600'
                }`}
              >
                📂 Upload
              </button>
              <button
                type="button"
                onClick={() => {
                  setInputMode('sample');
                  setResult(null);
                }}
                className={`px-3 py-1.5 rounded-lg transition ${
                  inputMode === 'sample' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-600'
                }`}
              >
                🔬 Demo Samples
              </button>
            </div>
          </div>

          {inputMode === 'upload' ? (
            <div>
              <input
                ref={fileInputRef}
                type="file"
                id="studio-file-input"
                accept="image/*, .png, .jpg, .jpeg, .dicom"
                onChange={handleFileChange}
                className="hidden"
              />
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    const f = e.dataTransfer.files[0];
                    setFile(f);
                    setPreviewUrl(URL.createObjectURL(f));
                    setResult(null);
                    setError('');
                  }
                }}
                className="border-2 border-dashed border-sky-200 hover:border-sky-400 bg-sky-50/40 hover:bg-sky-50/70 rounded-2xl p-6 text-center transition cursor-pointer group"
              >
                <Upload className="w-8 h-8 text-sky-600 mx-auto mb-2 group-hover:scale-110 transition" />
                {file ? (
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-slate-800 truncate">
                      📁 {file.name}
                    </div>
                    <div className="text-[10px] text-sky-700 font-bold">
                      {(file.size / 1024).toFixed(0)} KB &bull; Click to Change File
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <div className="text-xs font-bold text-slate-800">
                      Click to Browse or Drop Patient X-ray
                    </div>
                    <span className="inline-block px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white text-[11px] font-bold rounded-lg shadow-sm">
                      Open File Explorer ➔
                    </span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-700">
                Select Test Chest Radiograph:
              </label>
              <select
                value={selectedSample}
                onChange={(e) => {
                  setSelectedSample(e.target.value);
                  setResult(null);
                  setError('');
                }}
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium text-slate-800 focus:ring-2 focus:ring-sky-500"
              >
                {availableSamples.map((s, idx) => (
                  <option key={s.filename} value={s.filename}>
                    Radiograph #{idx + 1}: {s.filename} ({(s.size_bytes / 1024).toFixed(0)} KB)
                  </option>
                ))}
              </select>
              {selectedSample && (
                <div className="p-2.5 bg-slate-100 rounded-xl flex items-center justify-between text-xs text-slate-700">
                  <span className="truncate">Active: <strong>{selectedSample}</strong></span>
                  <span className="bg-sky-100 text-sky-800 px-2 py-0.5 rounded text-[10px] font-bold">Ready</span>
                </div>
              )}
            </div>
          )}

          <div>
            <div className="flex justify-between items-center mb-1 text-xs">
              <span className="font-bold text-slate-700">Diagnostic Sensitivity Threshold</span>
              <span className="font-mono font-bold text-sky-700">{(confidence * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.70"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-600"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleRunStudioTriage}
            disabled={isProcessing || (inputMode === 'upload' && !file)}
            className="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow-md shadow-sky-500/20 transition active:scale-98 disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
          >
            {isProcessing ? (
              <>
                <Activity className="w-4 h-4 animate-spin" />
                <span>Analyzing Radiograph...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Execute Deep-Learning Triage</span>
              </>
            )}
          </button>
        </div>

        {/* Visual Inspection (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-heading font-bold text-slate-900 text-base mb-3">
              YOLO11 Radiograph Findings Inspection
            </h3>

            <div className="aspect-[4/3] bg-slate-950 rounded-xl overflow-hidden flex items-center justify-center border border-slate-800">
              {result ? (
                <img
                  src={result.annotated_image_b64}
                  alt="Detections"
                  className="w-full h-full object-contain"
                />
              ) : previewUrl ? (
                <img src={previewUrl} alt="Preview" className="w-full h-full object-contain" />
              ) : selectedSample && inputMode === 'sample' ? (
                <img
                  src={api.getSampleImageUrl(selectedSample)}
                  alt="Sample Preview"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-center text-slate-500 p-6 text-xs">
                  Upload patient radiograph or select demo sample to view annotated bounding boxes
                </div>
              )}
            </div>
          </div>


          {result && (
            <div className="mt-4 pt-3 border-t border-slate-200 flex justify-between items-center">
              <span className="text-xs font-bold text-slate-700">
                Total Pathologies: <strong className="text-sky-700">{result.findings_count}</strong>
              </span>
              <button
                onClick={() => onViewReport({
                  report_id: `DOC-RAD-${Math.floor(Math.random() * 900000 + 100000)}`,
                  patient_info: {
                    full_name: 'Clinic Outpatient',
                    patient_id: `PAT-RAD-${Math.floor(Math.random() * 900000 + 100000)}`,
                    age: 48,
                    gender: 'Clinical Case',
                    city: user.city || 'Bangalore',
                    timestamp: new Date().toLocaleString(),
                  },
                  detection_results: result,
                  referred_doctor: {
                    doctor_name: activeDoctorName,
                    specialization: user.specialization || 'Pulmonologist',
                    hospital: user.hospital || 'AIIMS Hospital',
                    city: user.city || 'Bangalore',
                    fees_inr: user.fees_inr || 800,
                    disease_expertise: user.disease_expertise || 'Specialist Review',
                  },
                  annotated_img_b64: result.annotated_image_b64,
                  doctor_notes: 'Clinical radiograph reviewed by attending specialist. Recommended physiological follow-up.',
                })}
                className="inline-flex items-center space-x-1.5 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg shadow-sm transition active:scale-95"
              >
                <FileText className="w-4 h-4" />
                <span>Generate Doctor-Signed Report</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
