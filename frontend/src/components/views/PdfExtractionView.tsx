import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  Play,
  FileSpreadsheet,
  Activity,
  Trash2,
  TrendingDown,
  TrendingUp,
  Scale
} from 'lucide-react';
import type { FileCard, ExtractionResult, Transaction } from '../../types';
import { TableViewer } from '../ui/TableViewer';

interface PdfExtractionViewProps {
  files: FileCard[];
  onUploadFiles: (e: React.ChangeEvent<HTMLInputElement> | React.DragEvent) => void;
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
  onRemoveFile,
  onExtractFiles,
  onGenerateExport,
  results,
  isProcessing
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [engineOverrides, setEngineOverrides] = useState<Record<string, string>>({});

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
  const activeFileCard = files.find((f) => f.id === activeFileId);

  const availableEngines = [
    'Auto Multi-Engine Pipeline',
    'Kotak Bank Statement',
    'PNB Bank Statement',
    'Union Bank Statement',
    'Yes Bank Statement',
    'HDFC Bank Statement',
    'Axis Bank Statement',
    'ICICI Bank Statement',
    'IndusInd Bank Statement'
  ];

  const handleEngineChange = (fileId: string, engine: string) => {
    setEngineOverrides((prev) => ({ ...prev, [fileId]: engine }));
  };

  const handleRunExtract = () => {
    const idsToExtract = files.map((f) => f.id);
    onExtractFiles(idsToExtract, engineOverrides);
  };

  const handleExtractSingle = (fileId: string) => {
    onExtractFiles([fileId], engineOverrides);
  };

  const handleUpdateTransactions = (updatedTxs: Transaction[]) => {
    if (activeFileId && activeResult) {
      activeResult.transactions = updatedTxs;
      setSelectedFileId(activeFileId);
    }
  };

  const formatINR = (amount?: number) => {
    if (amount === undefined || amount === null || isNaN(amount)) return '₹0.00';
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-6 pb-12 max-w-[1700px] mx-auto font-sans antialiased">
      {/* Studio Top Control Header */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-neutral-900 text-white">
              Studio Workspace
            </span>
            <span className="text-xs text-neutral-400 font-medium">Automatic Bank Discrimination & Math Ledger Verification</span>
          </div>
          <h1 className="text-xl font-extrabold text-neutral-900 tracking-tight">
            Bank Statement Extraction & Audit
          </h1>
        </div>

        <div className="flex items-center gap-2.5">
          {files.length > 0 && (
            <button
              onClick={handleRunExtract}
              disabled={isProcessing}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-neutral-900 text-white font-bold text-xs hover:bg-neutral-800 active:scale-[0.98] transition disabled:opacity-50 shadow-sm"
            >
              {isProcessing ? (
                <>
                  <Activity className="w-3.5 h-3.5 animate-spin text-white" />
                  Extracting Statements...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  Process All Statements ({files.length})
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Minimalist Drag & Drop Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border border-dashed transition-all duration-200 bg-white ${
          dragActive
            ? 'border-neutral-900 bg-neutral-50/80 ring-4 ring-neutral-900/5'
            : 'border-neutral-300/80 hover:border-neutral-400'
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
        <label htmlFor="pdf-upload-input" className="cursor-pointer block p-7 text-center">
          <div className="w-10 h-10 rounded-xl bg-neutral-100 text-neutral-800 border border-neutral-200/80 flex items-center justify-center mx-auto mb-2.5 transition group-hover:scale-105">
            <UploadCloud className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-neutral-900 tracking-tight">
            Drop PDF bank statements here, or <span className="text-neutral-900 underline underline-offset-4 font-semibold hover:text-neutral-700">browse files</span>
          </h3>
        </label>
      </div>

      {/* Uploaded Documents List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-neutral-500 uppercase tracking-wider px-1">
            <span>Workspace Statements ({files.length})</span>
            <span>Click statement to inspect transactions</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {files.map((card) => {
              const isSelected = activeFileId === card.id;
              const engine = engineOverrides[card.id] || card.extraction_method || card.pdf_type || 'Auto Multi-Engine Pipeline';
              const cardResult = results[card.id];
              const isExtracted = !!cardResult && cardResult.transactions?.length > 0;

              return (
                <div
                  key={card.id}
                  onClick={() => setSelectedFileId(card.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer relative bg-white ${
                    isSelected
                      ? 'border-neutral-900 ring-2 ring-neutral-900/10 shadow-sm'
                      : 'border-neutral-200/80 hover:border-neutral-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2.5 mb-3">
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <div className="w-8 h-8 rounded-lg bg-neutral-100 text-neutral-800 flex items-center justify-center shrink-0 border border-neutral-200/60">
                        <FileText className="w-4 h-4 text-rose-500" />
                      </div>
                      <div className="truncate">
                        <div className="font-bold text-xs text-neutral-900 truncate" title={card.filename}>
                          {card.filename}
                        </div>
                        <div className="text-[11px] text-neutral-500 font-medium mt-0.5 flex items-center gap-1.5">
                          <span className="px-1.5 py-0.2 bg-neutral-100 rounded text-[10px] font-bold text-neutral-700">
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
                      className="text-neutral-400 hover:text-rose-600 p-1 rounded-lg hover:bg-neutral-100 transition"
                      title="Remove file"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Target Engine Selector */}
                  <div className="mb-3 bg-neutral-50/80 p-2 rounded-xl border border-neutral-200/60">
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-[9px] font-bold uppercase tracking-wider text-neutral-500">
                        Selected Extractor
                      </label>
                      <span className="text-[9px] bg-neutral-200 text-neutral-800 px-1.5 py-0.2 rounded font-semibold">
                        Auto-Detected
                      </span>
                    </div>
                    <select
                      value={engine}
                      onChange={(e) => handleEngineChange(card.id, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full text-xs bg-white border border-neutral-200 rounded-lg px-2 py-1 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
                    >
                      {availableEngines.map((eng) => (
                        <option key={eng} value={eng}>
                          {eng}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Status & Extract Trigger */}
                  <div className="flex items-center justify-between pt-2 border-t border-neutral-100 text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${
                        card.status === 'Extracting'
                          ? 'bg-amber-500 animate-ping'
                          : isExtracted
                          ? 'bg-emerald-500'
                          : 'bg-neutral-400'
                      }`} />
                      <span className="font-semibold text-neutral-700 text-[11px]">
                        {card.status === 'Ready' && !isExtracted ? 'Ready to Extract' : card.status}
                      </span>
                    </div>

                    {!isExtracted && card.status !== 'Extracting' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleExtractSingle(card.id);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-neutral-900 text-white text-[11px] font-bold hover:bg-neutral-800 transition"
                      >
                        Extract Now
                      </button>
                    )}

                    {isExtracted && (
                      <span className="text-[11px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200/60">
                        {cardResult.transactions.length} Rows
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Financial Statement Summary Ribbon (When Active Statement Has Extracted Data) */}
      {activeResult && activeResult.summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="p-3.5 bg-white rounded-xl border border-neutral-200/80 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">
              Opening Balance
            </div>
            <div className="text-sm font-bold font-mono text-neutral-900">
              {formatINR(activeResult.summary.opening_balance)}
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-xl border border-neutral-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">Total Debit</span>
              <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
            </div>
            <div className="text-sm font-bold font-mono text-rose-600">
              {formatINR(activeResult.summary.total_debit)}
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-xl border border-neutral-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">Total Credit</span>
              <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <div className="text-sm font-bold font-mono text-emerald-600">
              {formatINR(activeResult.summary.total_credit)}
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-xl border border-neutral-200/80 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">
              Closing Balance
            </div>
            <div className="text-sm font-bold font-mono text-neutral-900">
              {formatINR(activeResult.summary.closing_balance)}
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-xl border border-neutral-200/80 shadow-sm col-span-2 md:col-span-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">Math Status</span>
              <Scale className="w-3.5 h-3.5 text-neutral-600" />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-bold text-neutral-900">
                {activeResult.summary.pass_count} / {activeResult.summary.total_count} Verified
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Data Table Canvas */}
      {activeResult && activeResult.transactions && activeResult.transactions.length > 0 ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-neutral-900">
                Transaction Ledger ({activeResult.transactions.length} entries)
              </h2>
              <span className="text-[10px] font-mono bg-neutral-100 text-neutral-700 px-2 py-0.5 rounded-full border border-neutral-200/60 font-semibold">
                {activeResult.engine_used}
              </span>
            </div>
            <div className="text-xs text-neutral-400 font-medium">
              Document: <span className="text-neutral-700 font-semibold">{activeFileCard?.filename}</span>
            </div>
          </div>

          <TableViewer
            transactions={activeResult.transactions}
            onUpdateTransactions={handleUpdateTransactions}
            onExport={(fmt) => onGenerateExport(activeFileId ? [activeFileId] : [], fmt)}
          />
        </div>
      ) : files.length > 0 && !isProcessing ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-neutral-50 border border-neutral-200 text-neutral-400 flex items-center justify-center mx-auto">
            <FileSpreadsheet className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-neutral-900">Ready for Bank Statement Extraction</h3>
          <p className="text-xs text-neutral-400 max-w-md mx-auto">
            Click <strong>"Process All Statements"</strong> above or <strong>"Extract Now"</strong> on any statement card to extract transactions into the ledger.
          </p>
          <button
            onClick={handleRunExtract}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-neutral-900 text-white font-bold text-xs hover:bg-neutral-800 transition shadow-sm"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            Start Extraction Pipeline
          </button>
        </div>
      ) : null}
    </div>
  );
};
