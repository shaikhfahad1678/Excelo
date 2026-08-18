import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  Play,
  FileSpreadsheet,
  Sparkles,
  Activity,
  Trash2,
  ListChecks,
  ShieldCheck,
  AlertOctagon,
  AlertTriangle
} from 'lucide-react';
import type { FileCard, ExtractionResult, Transaction } from '../../types';
import { TableViewer } from '../ui/TableViewer';

interface PdfExtractionViewProps {
  files: FileCard[];
  onUploadFiles: (e: React.ChangeEvent<HTMLInputElement> | React.DragEvent) => void;
  onLoadSample?: () => void;
  onRemoveFile: (id: string) => void;
  onExtractFiles: (fileIds: string[], engineOverrides?: Record<string, string>, engineOverride?: string) => void;
  onRetryFile: (fileId: string, preferredEngine: string) => void;
  onGenerateExport: (fileIds: string[], format: 'xlsx' | 'csv') => void;
  results: Record<string, ExtractionResult>;
  isProcessing: boolean;
}

export const PdfExtractionView: React.FC<PdfExtractionViewProps> = ({
  files,
  onUploadFiles,
  onLoadSample,
  onRemoveFile,
  onExtractFiles,
  onGenerateExport,
  results,
  isProcessing
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [highlightedRowIndex] = useState<number | null>(null);
  const [engineOverrides, setEngineOverrides] = useState<Record<string, string>>({});
  const [showDiagnosticsModal, setShowDiagnosticsModal] = useState(false);

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUploadFiles(e);
    }
  };

  // Determine active displayed file result
  const activeFileId = selectedFileId || (files.length > 0 ? files[0].id : null);
  const activeResult = activeFileId ? results[activeFileId] : null;

  const availableEngines = [
    'Auto Multi-Engine Pipeline',
    'ICICI Bank Statement',
    'Axis Bank Statement',
    'IndusInd Bank Statement',
    'HDFC Bank Statement',
    'Method 1: Spatial Bounding-Box Layout Clustering + PP-OCRv4 (Recommended #1)',
    'Method 2: OpenCV Morphological Grid Line Cleaning + Cell Isolation',
    'Method 3: Local Compact Vision Model (Florence-2-base / Qwen2-VL)',

    'PaddleOCR Engine (PP-OCRv4)',
    'TYPE 1: Native Digital PDF Pipeline',
    'TYPE 2: OCR Searchable PDF Pipeline',
    'TYPE 3: Scanned PDF OCR Pipeline'
  ];


  const handleEngineChange = (fileId: string, engine: string) => {
    setEngineOverrides((prev) => ({ ...prev, [fileId]: engine }));
  };

  const handleRunExtract = () => {
    const idsToExtract = files.map((f) => f.id);
    onExtractFiles(idsToExtract, engineOverrides);
  };


  const handleUpdateTransactions = (updatedTxs: Transaction[]) => {
    if (activeFileId && activeResult) {
      activeResult.transactions = updatedTxs;
      setSelectedFileId(activeFileId);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-[1600px] mx-auto font-sans antialiased">
      {/* Executive Minimalist Header & Control Bar */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-900 text-white tracking-wide">
              <ShieldCheck className="w-3 h-3 text-blue-400" /> Multi-Stage Extraction Pipeline
            </span>
            <span className="text-xs font-medium text-slate-400">• Strict 11-Rule Validation Engine</span>
          </div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
            PDF Bank Statement Processing Workspace
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onLoadSample}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100/80 text-slate-700 hover:bg-slate-200/80 border border-slate-200 text-xs font-semibold transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            Load Sample Statement
          </button>
          {files.length > 0 && (
            <button
              onClick={handleRunExtract}
              disabled={isProcessing}
              className="flex items-center gap-2.5 px-6 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 active:scale-[0.98] transition disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-white" />
                  Extracting Statements...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  Run Extraction Pipeline
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Sleek Drag & Drop File Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-200 ${
          dragActive
            ? 'border-blue-500 bg-blue-50/40 ring-4 ring-blue-500/10'
            : 'border-slate-300/80 hover:border-slate-400 bg-white'
        }`}
      >
        <input
          type="file"
          id="pdf-upload-input"
          multiple
          accept=".pdf"
          onChange={onUploadFiles}
          className="hidden"
        />
        <label htmlFor="pdf-upload-input" className="cursor-pointer block p-8 text-center">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center mx-auto mb-3 transition group-hover:scale-105">
            <UploadCloud className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800 tracking-tight">
            Drop PDF bank statements here, or <span className="text-blue-600 font-semibold hover:underline">browse files</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 font-medium">
            Classified automatically into Native Digital PDF, OCR Searchable PDF, or Scanned PDF
          </p>
        </label>
      </div>

      {/* Uploaded File Cards Grid */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-slate-500 uppercase tracking-wider px-1">
            <span>Uploaded Workspace Documents ({files.length})</span>
            <span>Select card to view analysis</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.map((card) => {
              const isSelected = activeFileId === card.id;
              const engine = engineOverrides[card.id] || card.extraction_method;

              return (
                <div
                  key={card.id}
                  onClick={() => setSelectedFileId(card.id)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer relative ${
                    isSelected
                      ? 'border-blue-500 bg-white ring-2 ring-blue-500/20'
                      : 'border-slate-200/90 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center shrink-0 border border-slate-200/60">
                        <FileText className="w-5 h-5 text-rose-500" />
                      </div>
                      <div className="truncate">
                        <div className="font-bold text-xs text-slate-900 truncate" title={card.filename}>
                          {card.filename}
                        </div>
                        <div className="text-[11px] text-slate-500 font-medium mt-0.5 flex items-center gap-1.5">
                          <span className="px-1.5 py-0.5 bg-slate-100 rounded text-[10px] font-bold text-slate-700">
                            {card.pdf_type}
                          </span>
                          • {card.pages} page{card.pages > 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveFile(card.id);
                      }}
                      className="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
                      title="Remove file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Engine Selector Dropdown */}
                  <div className="mb-4 bg-slate-50 p-2.5 rounded-xl border border-slate-200/60">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      Target Extraction Engine Strategy
                    </label>
                    <select
                      value={engine}
                      onChange={(e) => handleEngineChange(card.id, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    >
                      {availableEngines.map((eng) => (
                        <option key={eng} value={eng}>
                          {eng}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Progress & Confidence */}
                  <div className="space-y-2 pt-1 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs">
                      <span className={`font-bold ${card.status === 'Failed' || card.status === 'Failed Validation' ? 'text-rose-600' : 'text-slate-700'}`}>
                        {card.status}
                      </span>
                      {card.confidence_score > 0 && (
                        <span className="font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px]">
                          {card.confidence_score}% Conf
                        </span>
                      )}
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 rounded-full ${card.status === 'Failed' ? 'bg-rose-500' : 'bg-blue-600'}`}
                        style={{ width: `${card.progress}%` }}
                      />
                    </div>

                    {card.status === 'Extracting' && card.detect_msg && (
                      <p className="text-[10px] text-blue-600 font-semibold animate-pulse mt-2 p-1.5 bg-blue-50/50 rounded-lg border border-blue-100/50">
                        {card.detect_msg}
                      </p>
                    )}

                    {(card.status === 'Failed' || card.status === 'Failed Validation') && (
                      <div className="mt-2 p-2 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs font-semibold space-y-1">
                        <div className="flex items-center gap-1 text-rose-800 font-bold">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                          <span>Extraction Failure Reason</span>
                        </div>
                        <p className="text-[11px] leading-tight text-rose-600 font-medium">
                          {results[card.id]?.failsafe_warning || results[card.id]?.error || card.detect_msg || 'Engine error occurred or API Key missing.'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Live Stage Progress Indicator */}
      {isProcessing && (
        <div className="bg-slate-900 text-white p-6 rounded-2xl space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-400/40 text-blue-400 flex items-center justify-center">
              <Activity className="w-4 h-4 animate-spin" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">
                Multi-Stage Pipeline Executing...
              </h3>
              <p className="text-xs text-blue-400 font-semibold animate-pulse">
                {files.find(f => f.status === 'Extracting')?.detect_msg || 'Classifying PDF structure, running candidate engines, and enforcing 11 strict validation rules'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
            {[
              'Classify PDF Type',
              'Select Strategy',
              'Extract Tables',
              'Strict 11 Rules',
              'Composite Score',
              'Generate Sr No.',
              'Completed'
            ].map((stage, i) => (
              <div
                key={stage}
                className="p-2.5 bg-slate-800/80 border border-slate-700/60 rounded-xl text-center"
              >
                <div className="text-[10px] font-bold text-blue-400 uppercase tracking-wider mb-0.5">Stage {i + 1}</div>
                <div className="text-[11px] font-medium text-slate-200">{stage}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fail Safe Warning Banner */}
      {activeResult && activeResult.failsafe_warning && (
        <div className="bg-rose-50 border-2 border-rose-300 rounded-2xl p-5 flex items-start gap-4 text-rose-900">
          <div className="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center shrink-0">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <div className="font-extrabold text-sm uppercase tracking-wider text-rose-900">
              Fail Safe Warning — Action Required
            </div>
            <p className="text-xs font-semibold text-rose-800 mt-1">
              {activeResult.failsafe_warning}
            </p>
            <div className="text-[11px] text-rose-700 mt-1 font-medium">
              Every candidate strategy was evaluated. The current row accuracy or balance validation rate fell below the 98% threshold limit.
            </div>
          </div>
        </div>
      )}

      {/* Main Extracted Results Section */}
      {activeResult && activeResult.success && (
        <div className="space-y-6">
          {/* Summary Metric Header Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-5">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-100">
                    {activeResult.pdf_type || 'Native Digital PDF'}
                  </span>
                  <span className="text-xs text-slate-400">• Strategy Selected: {activeResult.engine_used}</span>
                </div>
                <h2 className="text-xl font-extrabold text-slate-900">
                  {activeResult.filename}
                </h2>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowDiagnosticsModal(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 text-xs font-semibold transition"
                >
                  <ListChecks className="w-4 h-4 text-blue-600" />
                  Diagnostics Report
                </button>

                <button
                  onClick={() => onGenerateExport([activeFileId!], 'xlsx')}
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-bold transition"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  Export Excel (.xlsx)
                </button>
              </div>
            </div>

            {/* Financial KPIs Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
              <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/70">
                <div className="text-[11px] font-semibold text-slate-500">Total Transactions</div>
                <div className="text-xl font-extrabold text-slate-900 mt-1">
                  {activeResult.summary.total_count}
                </div>
              </div>

              <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/70">
                <div className="text-[11px] font-semibold text-slate-500">Opening Balance</div>
                <div className="text-xl font-extrabold text-slate-900 mt-1">
                  {(activeResult.summary.opening_balance ?? 0).toLocaleString('en-US', {
                    minimumFractionDigits: 2
                  })}
                </div>
              </div>

              <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/70">
                <div className="text-[11px] font-semibold text-slate-500">Closing Balance</div>
                <div className="text-xl font-extrabold text-slate-900 mt-1">
                  {(activeResult.summary.closing_balance ?? 0).toLocaleString('en-US', {
                    minimumFractionDigits: 2
                  })}
                </div>
              </div>

              <div className="p-4 bg-rose-50/40 rounded-2xl border border-rose-100">
                <div className="text-[11px] font-semibold text-rose-700">Total Withdrawal (Dr)</div>
                <div className="text-xl font-extrabold text-rose-700 mt-1">
                  {(activeResult.summary.total_debit ?? 0).toLocaleString('en-US', {
                    minimumFractionDigits: 2
                  })}
                </div>
              </div>

              <div className="p-4 bg-emerald-50/40 rounded-2xl border border-emerald-100">
                <div className="text-[11px] font-semibold text-emerald-700">Total Deposit (Cr)</div>
                <div className="text-xl font-extrabold text-emerald-700 mt-1">
                  {(activeResult.summary.total_credit ?? 0).toLocaleString('en-US', {
                    minimumFractionDigits: 2
                  })}
                </div>
              </div>


              <div className="p-4 bg-blue-50/40 rounded-2xl border border-blue-100">
                <div className="text-[11px] font-semibold text-blue-700">Pass Rate / Time</div>
                <div className="text-xl font-extrabold text-blue-900 mt-1 flex items-baseline gap-1">
                  {activeResult.confidence_score}%
                  <span className="text-xs font-normal text-slate-500">({activeResult.processing_time}s)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Excel Table Viewer Container */}
          <div className="h-[560px] bg-white rounded-2xl border border-slate-200/80 overflow-hidden">
            <TableViewer
              transactions={activeResult.transactions}
              onUpdateTransactions={handleUpdateTransactions}
              highlightedRowIndex={highlightedRowIndex}
              onExport={(fmt) => onGenerateExport([activeFileId!], fmt)}
            />
          </div>
        </div>
      )}

      {/* Multi-Engine Diagnostics Modal */}
      {showDiagnosticsModal && activeResult?.diagnostics && (
        <div className="fixed inset-0 bg-slate-950/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-5 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <ListChecks className="w-5 h-5 text-blue-600" /> Multi-Stage Pipeline Diagnostics Report
              </h3>
              <button
                onClick={() => setShowDiagnosticsModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80 text-xs space-y-1">
              <div className="font-bold text-slate-900 flex items-center gap-2">
                <span>PDF Type: {activeResult.diagnostics.pdf_type || activeResult.pdf_type || 'Native Digital PDF'}</span>
              </div>
              <p className="text-slate-600">{activeResult.diagnostics.selection_reason}</p>
            </div>

            <div className="space-y-2.5">
              {activeResult.diagnostics.candidates.map((cand, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
                    cand.method === activeResult.diagnostics?.selected_method
                      ? 'border-blue-500 bg-blue-50/40 ring-1 ring-blue-500/20'
                      : 'border-slate-200 bg-slate-50/50'
                  }`}
                >
                  <div>
                    <div className="font-bold text-slate-900 flex items-center gap-2">
                      {cand.method}
                      {cand.method === activeResult.diagnostics?.selected_method && (
                        <span className="text-[10px] font-bold bg-blue-600 text-white px-2 py-0.5 rounded-full">
                          Selected Strategy
                        </span>
                      )}
                    </div>
                    <div className="text-slate-500 text-[11px] mt-1">
                      Rows Found: {cand.rows_found} • Pass Count: {cand.pass_count ?? cand.rows_found} • Validated: {cand.is_valid ? '100% Pass' : 'Validation Failed'}
                    </div>
                  </div>
                  <div className="text-right font-mono">
                    <div className="font-bold text-blue-700 text-sm">Score: {cand.score}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-right pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowDiagnosticsModal(false)}
                className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold text-xs hover:bg-slate-800 transition"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
