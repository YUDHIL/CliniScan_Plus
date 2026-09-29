'use client';

import React, { useState, useEffect } from 'react';
import { ScanRecord, UserSession } from '../types';
import { api } from '../lib/api';
import { 
  FileText, 
  Download, 
  Calendar, 
  Eye, 
  Activity, 
  CheckCircle2,
  FolderOpen
} from 'lucide-react';

interface ScanHistoryProps {
  user: UserSession;
  onViewReport: (data: any) => void;
}

export const ScanHistory: React.FC<ScanHistoryProps> = ({
  user,
  onViewReport,
}) => {
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    loadUserScans();
  }, [user]);

  const loadUserScans = async () => {
    setLoading(true);
    try {
      const res = await api.getScans(user.username);
      setScans(res.scans || []);
    } catch (e) {
      console.error('Failed to load user scan history', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex justify-between items-center">
        <div>
          <h2 className="font-heading font-extrabold text-2xl text-slate-900 tracking-tight">
            Diagnostic Scan Vault & History
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Archived chest radiograph scans, localized AI findings, and official clinical certificates.
          </p>
        </div>
        <div className="bg-sky-50 text-sky-700 px-3.5 py-1.5 rounded-xl border border-sky-200 text-xs font-bold">
          Total Scans: {scans.length}
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-slate-500 text-xs font-bold">Loading archived scans...</div>
      ) : scans.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
          <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <h4 className="font-heading font-bold text-base text-slate-700">No Scan Records on File</h4>
          <p className="text-xs text-slate-500 mt-1">
            Upload and scan a chest radiograph to generate your first diagnostic triage certificate.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {scans.map((s) => (
            <div
              key={s.scan_id}
              className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-sky-300 shadow-sm transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-900 text-base">Radiograph Scan #{s.scan_id}</span>
                  <span className="text-xs text-slate-400 font-medium">📅 {s.timestamp?.slice(0, 16)}</span>
                </div>

                <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                  <span className="text-xs font-bold text-slate-600 mr-1">Detections ({s.findings_count}):</span>
                  {s.findings && s.findings.length > 0 ? (
                    s.findings.map((f, i) => (
                      <span
                        key={i}
                        className="bg-red-50 text-red-700 border border-red-200 text-[11px] font-bold px-2.5 py-0.5 rounded-md"
                      >
                        {f.class_name} ({f.confidence_pct})
                      </span>
                    ))
                  ) : (
                    <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold px-2.5 py-0.5 rounded-md">
                      Normal Radiograph (Clear)
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onViewReport({
                    report_id: s.scan_id,
                    patient_info: {
                      full_name: s.patient_name || user.full_name,
                      patient_id: s.patient_id || user.user_id || `PAT-${user.username.toUpperCase()}`,
                      age: s.age || user.age || 45,
                      gender: s.gender || user.gender || 'Male',
                      city: s.city || user.city || 'Bangalore',
                      timestamp: s.timestamp,
                    },
                    detection_results: { detections: s.findings, model_version: 'CliniScan-YOLO11-v1' },
                    annotated_img_b64: s.image_b64,
                  })}
                  className="inline-flex items-center space-x-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-sm transition active:scale-95"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View Diagnostic Certificate</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
