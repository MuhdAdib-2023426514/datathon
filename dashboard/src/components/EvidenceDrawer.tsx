import React from 'react';
import { 
  X, 
  ShieldCheck, 
  AlertTriangle, 
  Activity, 
  Database, 
  CheckCircle2,
  FileSpreadsheet
} from 'lucide-react';

export interface EvidenceItem {
  id?: string;
  recommendationTitle: string;
  actionType: string;
  targetCorridorOrState: string;
  observation: string;
  supportingMetrics: { label: string; value: string; context?: string }[];
  modelEvidence: {
    modelName: string;
    specification: string;
    finding: string;
    keyCoefficients?: string;
  };
  source: string;
  status: 'Official 2025 (p)' | 'Official (r)' | 'Derived Proxy' | 'Model Calibrated' | 'Scenario Assumption';
  confidence: 'High' | 'Very High' | 'Medium';
  limitations: string[];
}

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceItem | null;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  evidence,
}) => {
  if (!isOpen || !evidence) return null;

  const statusBadgeClasses: Record<string, string> = {
    'Official 2025 (p)': 'bg-blue-100 text-blue-800 border-blue-200',
    'Official (r)': 'bg-emerald-100 text-emerald-800 border-emerald-200',
    'Derived Proxy': 'bg-purple-100 text-purple-800 border-purple-200',
    'Model Calibrated': 'bg-indigo-100 text-indigo-800 border-indigo-200',
    'Scenario Assumption': 'bg-amber-100 text-amber-800 border-amber-200',
  };

  const confidenceBadgeClasses: Record<string, string> = {
    'Very High': 'bg-emerald-50 text-emerald-800 border-emerald-300',
    'High': 'bg-indigo-50 text-indigo-800 border-indigo-300',
    'Medium': 'bg-amber-50 text-amber-800 border-amber-300',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
          {/* Header */}
          <div className="p-6 bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-purple-500/30 text-purple-200 border border-purple-400/40">
                  Decision Evidence Brief
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusBadgeClasses[evidence.status] || 'bg-slate-100 text-slate-700'}`}>
                  {evidence.status}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white leading-snug">
                Why is this recommended?
              </h2>
              <p className="text-xs text-purple-200">
                {evidence.targetCorridorOrState} · {evidence.actionType}
              </p>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-white/10 text-purple-200 hover:text-white hover:bg-white/20 transition-all cursor-pointer"
              title="Close evidence drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 text-slate-800">
            {/* Recommendation Title Box */}
            <div className="p-4 rounded-xl bg-purple-50/70 border border-purple-200/80 space-y-1">
              <span className="text-[11px] font-bold text-purple-900 uppercase tracking-wider block">
                Policy Recommendation:
              </span>
              <h3 className="text-sm font-extrabold text-slate-900 leading-snug">
                {evidence.recommendationTitle}
              </h3>
            </div>

            {/* Observation Card */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>1. Core Empirical Observation</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                {evidence.observation}
              </p>
            </div>

            {/* Supporting Metrics */}
            <div className="space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
                <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
                <span>2. Supporting Empirical Metrics</span>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                {evidence.supportingMetrics.map((m, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1">
                    <span className="text-[10px] font-medium text-slate-500 block truncate">{m.label}</span>
                    <div className="text-sm font-bold font-mono text-purple-900">{m.value}</div>
                    {m.context && (
                      <span className="text-[10px] text-slate-600 block leading-tight">{m.context}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Model Evidence */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
                <Activity className="w-4 h-4 text-purple-600" />
                <span>3. Econometric & Scientific Model Evidence</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <span className="font-bold text-slate-900">{evidence.modelEvidence.modelName}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono font-medium">
                    {evidence.modelEvidence.specification}
                  </span>
                </div>
                <p className="text-slate-700 leading-relaxed">
                  {evidence.modelEvidence.finding}
                </p>
                {evidence.modelEvidence.keyCoefficients && (
                  <div className="p-2 rounded bg-white border border-slate-200 font-mono text-[11px] text-indigo-900">
                    {evidence.modelEvidence.keyCoefficients}
                  </div>
                )}
              </div>
            </div>

            {/* Confidence & Provenance */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Authoritative Source
                </span>
                <div className="text-xs font-semibold text-slate-900 flex items-center gap-1.5 mt-1">
                  <Database className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{evidence.source}</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Confidence Rating
                </span>
                <div className="mt-1">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${confidenceBadgeClasses[evidence.confidence] || 'bg-slate-100 text-slate-700'}`}>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {evidence.confidence} Confidence
                  </span>
                </div>
              </div>
            </div>

            {/* Analytical Caveats & Limitations */}
            <div className="space-y-2 pt-1 border-t border-slate-200">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-800 uppercase tracking-wider">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Analytical Caveats & Limitations</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-600 list-disc list-inside bg-amber-50/50 p-3.5 rounded-xl border border-amber-200/60">
                {evidence.limitations.map((lim, idx) => (
                  <li key={idx} className="leading-relaxed">{lim}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
            <span className="text-[11px] text-slate-500 italic">
              * Official research prototype decision-support output.
            </span>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition-all cursor-pointer"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
