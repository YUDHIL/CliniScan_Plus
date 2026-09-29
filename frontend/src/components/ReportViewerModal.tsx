'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { X, Printer, Download, FileText, CheckCircle2 } from 'lucide-react';

interface ReportViewerModalProps {
  reportData: any | null;
  onClose: () => void;
}

export const ReportViewerModal: React.FC<ReportViewerModalProps> = ({
  reportData,
  onClose,
}) => {
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (reportData) {
      loadReport();
    }
  }, [reportData]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const html = await api.generateReportHtml(reportData);
      setHtmlContent(html);
    } catch (e) {
      console.error('Failed to generate report HTML', e);
    } finally {
      setLoading(false);
    }
  };

  if (!reportData) return null;

  const handleDownloadHtml = () => {
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Diagnostic_Report_${reportData.report_id || 'CLINISCAN'}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    const iframe = document.getElementById('report-iframe') as HTMLIFrameElement;
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm overflow-hidden">
      <div className="relative w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden">
        {/* Modal Topbar */}
        <div className="bg-gradient-to-r from-sky-800 to-sky-700 text-white px-6 py-3.5 flex justify-between items-center flex-shrink-0">
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-sky-200" />
            <h3 className="font-heading font-bold text-base">
              Diagnostic Report & Referral Pass &bull; {reportData.report_id}
            </h3>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              className="inline-flex items-center space-x-1.5 bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-3 py-1.5 rounded-lg border border-white/20 transition"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>
            <button
              onClick={handleDownloadHtml}
              className="inline-flex items-center space-x-1.5 bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download HTML</span>
            </button>
            <button
              onClick={onClose}
              className="text-sky-200 hover:text-white p-1 rounded-lg hover:bg-white/10 ml-2 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Report Content Iframe */}
        <div className="flex-1 bg-slate-100 p-2 overflow-hidden">
          {loading ? (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs font-bold">
              Generating printable diagnostic certificate...
            </div>
          ) : (
            <iframe
              id="report-iframe"
              srcDoc={htmlContent}
              title="Clinical Diagnostic Report"
              className="w-full h-full bg-white rounded-xl shadow-inner border border-slate-200"
            />
          )}
        </div>
      </div>
    </div>
  );
};
