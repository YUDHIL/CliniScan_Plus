'use client';

import React from 'react';
import { 
  Activity, 
  Layers, 
  Cpu, 
  Database, 
  ShieldAlert, 
  CheckCircle2, 
  BarChart3,
  Flame,
  Award
} from 'lucide-react';

interface ModelInsightsProps {
  targetClasses: string[];
  severityMapping: Record<string, { severity: string; urgency: string }>;
  storageMode: string;
}

export const ModelInsights: React.FC<ModelInsightsProps> = ({
  targetClasses = [],
  severityMapping = {},
  storageMode,
}) => {
  const pathologyDetails: Record<string, string> = {
    'Atelectasis': 'Partial or complete collapse of lung segments / alveoli',
    'ILD': 'Interstitial Lung Disease; diffuse parenchymal pulmonary scarring',
    'Pulmonary fibrosis': 'Chronic, irreversible fibrotic parenchymal tissue remodeling',
    'Pneumothorax': 'Pathological air leakage into pleural cavity causing lung collapse',
    'Pleural effusion': 'Pathological fluid accumulation within the pleural space',
    'Pleural thickening': 'Fibrotic thickening/calcification of the pleural membrane',
    'Consolidation': 'Alveolar filling with inflammatory exudate/pus (pneumonic process)',
    'Lung Opacity': 'Non-specific parenchymal radiographic density increase',
    'Nodule/Mass': 'Focal pulmonary lesions (<3cm nodule, >3cm mass / neoplasm)',
    'Infiltration': 'Ill-defined parenchymal density infiltration and inflammatory haziness'
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-sky-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 bg-sky-500/20 px-3 py-1 rounded-full text-sky-300 text-xs font-bold uppercase tracking-wider mb-2 border border-sky-400/20">
            <Cpu className="w-4 h-4 text-sky-400" />
            <span>Ultralytics YOLO11 Deep Learning</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl tracking-tight">
            AI Model Architecture & Clinical Research Insights
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 mt-1">
            Production-grade chest radiograph object detection and triage engine trained on the VinBigData dataset.
          </p>
        </div>
      </div>

      {/* 4 Architecture Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Detection Engine</div>
          <div className="font-heading text-xl font-extrabold text-slate-900 mt-1">YOLO11 Nano</div>
          <div className="text-[11px] text-sky-600 font-semibold mt-0.5">Ultralytics Medical Fine-Tuning</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Target Pathologies</div>
          <div className="font-heading text-xl font-extrabold text-sky-600 mt-1">10 Classes</div>
          <div className="text-[11px] text-slate-500 font-semibold mt-0.5">Localized & Diffuse Findings</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Dataset Split</div>
          <div className="font-heading text-xl font-extrabold text-slate-900 mt-1">70% / 15% / 15%</div>
          <div className="text-[11px] text-emerald-600 font-semibold mt-0.5">Train / Val / Test Ratio</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Persistence Engine</div>
          <div className="font-heading text-xl font-extrabold text-slate-900 mt-1">MongoDB Store</div>
          <div className="text-[11px] text-slate-500 font-semibold mt-0.5">{storageMode}</div>
        </div>
      </div>

      {/* 10 Pathologies Table */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <h3 className="font-heading font-bold text-slate-900 text-lg mb-4 flex items-center space-x-2">
          <Layers className="w-5 h-5 text-sky-600" />
          <span>Supported 10 Target Pulmonary & Pleural Pathologies</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-900 uppercase font-bold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4"># ID</th>
                <th className="py-3 px-4">Pathology Class</th>
                <th className="py-3 px-4">Clinical Description</th>
                <th className="py-3 px-4">Severity & Urgency</th>
                <th className="py-3 px-4">Primary Specialty</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {targetClasses.map((cls, idx) => {
                const meta = severityMapping[cls] || { severity: 'Moderate', urgency: 'Clinical Review' };
                const isCritical = meta.severity === 'Critical';
                const isHigh = meta.severity === 'High' || meta.severity === 'Moderate-High';

                return (
                  <tr key={cls} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-400">{idx}</td>
                    <td className="py-3 px-4 font-heading font-bold text-slate-900 text-sm">{cls}</td>
                    <td className="py-3 px-4 text-slate-600">{pathologyDetails[cls] || 'Pulmonary parenchymal abnormality'}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                        isCritical ? 'bg-red-100 text-red-700 border-red-200' :
                        isHigh ? 'bg-orange-100 text-orange-700 border-orange-200' :
                        'bg-amber-100 text-amber-700 border-amber-200'
                      }`}>
                        {meta.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-sky-700">
                      {cls === 'Nodule/Mass' ? 'Pulmonary Oncologist' : 'Pulmonologist'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Clinical Disclaimer Alert */}
      <div className="p-5 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-amber-900 text-xs">
        <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="font-bold text-amber-950">Medical Decision Support Disclaimer:</strong>
          <p className="mt-1 text-amber-800 leading-relaxed">
            CliniScan+ is an investigational AI-assisted clinical decision support system designed for triage and workflow acceleration. All bounding-box localizations, findings, and specialist recommendations must be independently confirmed by a certified radiologist or licensed physician prior to medical intervention.
          </p>
        </div>
      </div>
    </div>
  );
};
