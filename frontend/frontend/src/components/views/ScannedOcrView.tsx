import React, { useState } from 'react';
import {
  UploadCloud,
  FileImage,
  Sparkles,
  Sliders,
  Play,
  RefreshCw,
  AlertTriangle,
  ShieldCheck,
  Maximize2
} from 'lucide-react';
import type { Transaction } from '../../types';
import { TableViewer } from '../ui/TableViewer';

export const ScannedOcrView: React.FC = () => {
  const [ocrEngine, setOcrEngine] = useState('PaddleOCR (v3.2)');
  const [deskew, setDeskew] = useState(true);
  const [denoise, setDenoise] = useState(true);
  const [binarization, setBinarization] = useState(true);
  const [contrastScale, setContrastScale] = useState(85);

  const [files, setFiles] = useState<{ name: string; size: string }[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState<number>(0);
  const [showResult, setShowResult] = useState(false);

  const stages = [
    'Converting PDF Pages to 300 DPI Images...',
    'Applying Deskew & Orientation Auto-Rotation...',
    'Adaptive Otsu Binarization & Bilateral Contrast Filtering...',
    'Executing PaddleOCR Character Detection...',
    'Clustering Word Coordinate Bounding Boxes...',
    'Reconstructing Grid Rows & Balancing Running Balances...',
    'Strict 11-Rule Validation Assessment Complete.'
  ];

  const simulatedTransactions: Transaction[] = [
    {
      'Sr No.': 1,
      Date: '01/08/2026',
      Description: 'OPENING BALANCE',
      'Cheque No.': '',
      'Ref No.': '',
      Debit: '',
      Credit: '',
      Balance: 12540.50,
      'Validation Status': 'PASS'
    },
    {
      'Sr No.': 2,
      Date: '03/08/2026',
      Description: 'ACH CREDIT INTERNET PAYROLL',
      'Cheque No.': '',
      'Ref No.': 'REF9823412',
      Debit: '',
      Credit: 4500.00,
      Balance: 17040.50,
      'Validation Status': 'PASS'
    },
    {
      'Sr No.': 3,
      Date: '05/08/2026',
      Description: 'AUTOMATIC TRANSFER DEBIT AUDIT TAX',
      'Cheque No.': '',
      'Ref No.': 'REF1029831',
      Debit: 2150.00,
      Credit: '',
      Balance: 14890.50,
      'Validation Status': 'PASS'
    },
    {
      'Sr No.': 4,
      Date: '08/08/2026',
      Description: 'CASH WITHDRAWAL ATM BRANCH',
      'Cheque No.': 'CHQ08291',
      'Ref No.': '',
      Debit: 500.00,
      Credit: '',
      Balance: 14390.50,
      'Validation Status': 'PASS'
    },
    {
      'Sr No.': 5,
      Date: '10/08/2026',
      Description: 'DESKEW RECONSTRUCTED ROW LINE OUT',
      'Cheque No.': '',
      'Ref No.': 'REF1192830',
      Debit: 120.00,
      Credit: '',
      Balance: 14270.50,
      'Validation Status': 'RECONSTRUCTED'
    },
    {
      'Sr No.': 6,
      Date: '12/08/2026',
      Description: 'DUPLICATE TRANSACTION DOUBLE CHARGE',
      'Cheque No.': '',
      'Ref No.': 'REF1192830',
      Debit: 120.00,
      Credit: '',
      Balance: 14150.50,
      'Validation Status': 'DUPLICATE'
    }
  ];

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles([{ name: e.target.files[0].name, size: '4.2 MB' }]);
      setShowResult(false);
    }
  };

  const handleLoadSample = () => {
    setFiles([{ name: 'Scanned_Statement_Invoice_Copy.pdf', size: '2.8 MB' }]);
    setShowResult(false);
  };

  const handleRunOcr = () => {
    setIsProcessing(true);
    setProcessingStage(0);
    
    // Simulate multi-stage pipeline loader
    const interval = setInterval(() => {
      setProcessingStage((prev) => {
        if (prev >= stages.length - 1) {
          clearInterval(interval);
          setIsProcessing(false);
          setShowResult(true);
          return prev;
        }
        return prev + 1;
      });
    }, 1200);
  };

  return (
    <div className="space-y-6 pb-12 max-w-[1600px] mx-auto font-sans antialiased">
      {/* Settings Grid Panel & Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Side: OCR Pipeline Parameter Controls */}
        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl space-y-6 text-xs lg:col-span-1">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sliders className="w-4.5 h-4.5 text-blue-600" />
            <h3 className="font-extrabold text-slate-900 text-sm">OCR Preprocessing Controls</h3>
          </div>

          <div>
            <label className="font-bold text-slate-700 block mb-1.5">OCR Engine Model</label>
            <select
              value={ocrEngine}
              onChange={(e) => setOcrEngine(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 font-semibold text-slate-800 focus:outline-none"
            >
              <option>PaddleOCR (v3.2) - Best Speed</option>
              <option>Tesseract OCR (Local Native)</option>
              <option>Google Cloud Vision (Cloud High-Acc)</option>
            </select>
          </div>

          <div className="space-y-3 pt-2">
            <label className="flex items-center gap-2.5 font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={deskew}
                onChange={(e) => setDeskew(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              Auto-Deskew & Orientation
            </label>

            <label className="flex items-center gap-2.5 font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={denoise}
                onChange={(e) => setDenoise(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              Bilateral Noise Filtering
            </label>

            <label className="flex items-center gap-2.5 font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={binarization}
                onChange={(e) => setBinarization(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              Adaptive Binarization (Otsu)
            </label>
          </div>

          <div className="pt-2">
            <label className="font-bold text-slate-700 block mb-1">
              Contrast Factor Scale: {contrastScale}%
            </label>
            <input
              type="range"
              min="50"
              max="150"
              value={contrastScale}
              onChange={(e) => setContrastScale(parseInt(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>

          <button
            onClick={handleLoadSample}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 font-bold transition"
          >
            <Sparkles className="w-4 h-4 text-blue-600" />
            Load Sample Scanned PDF
          </button>
        </div>

        {/* Right Side: Interactive OCR Visualizer */}
        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl lg:col-span-3 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-extrabold text-slate-900">Scanned OCR Workspace</h2>
              <p className="text-[11px] text-slate-400 font-medium">Reconstruct image-only statements utilizing deep layout coordinate alignment.</p>
            </div>
            {files.length > 0 && (
              <button
                onClick={handleRunOcr}
                disabled={isProcessing}
                className="flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                {isProcessing ? 'Processing OCR...' : 'Run OCR Pipeline'}
              </button>
            )}
          </div>

          {files.length === 0 ? (
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-12 text-center">
              <input
                type="file"
                id="scanned-upload-input"
                accept=".pdf,image/*"
                onChange={handleUpload}
                className="hidden"
              />
              <label htmlFor="scanned-upload-input" className="cursor-pointer block">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center mx-auto mb-3">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-bold text-slate-800">
                  Drop scanned PDFs/Images here, or <span className="text-blue-600 hover:underline">browse files</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1 font-medium">Supports multiple images or Scanned PDF files up to 50MB</p>
              </label>
            </div>
          ) : (
            <div className="border border-slate-200 p-4 rounded-xl flex items-center justify-between gap-4 bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 border border-rose-100 flex items-center justify-center shrink-0">
                  <FileImage className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs text-slate-900">{files[0].name}</div>
                  <div className="text-[10px] text-slate-400 font-medium">Scanned Document Type • {files[0].size}</div>
                </div>
              </div>
              <button
                onClick={() => setFiles([])}
                className="text-slate-400 hover:text-rose-600 font-semibold text-xs transition"
              >
                Clear File
              </button>
            </div>
          )}

          {/* Running Multi-Stage OCR Visualizer Progress */}
          {isProcessing && (
            <div className="bg-slate-900 text-white p-5 rounded-xl space-y-4">
              <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
                <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                <div>
                  <div className="font-bold text-xs">Stage {processingStage + 1} of {stages.length}</div>
                  <div className="text-[11px] text-slate-400">{stages[processingStage]}</div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2 text-center text-[10px] font-bold">
                {stages.map((_, i) => (
                  <div
                    key={i}
                    className={`p-2 rounded-lg border transition ${
                      i < processingStage
                        ? 'border-emerald-500 bg-emerald-950/20 text-emerald-400'
                        : i === processingStage
                        ? 'border-blue-500 bg-blue-950/20 text-blue-400 animate-pulse'
                        : 'border-slate-800 bg-slate-950/50 text-slate-500'
                    }`}
                  >
                    Stage {i + 1}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Preview Image Frame Simulating Deskewing with coordinates */}
          {showResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-slate-200 rounded-xl overflow-hidden relative group">
                <div className="bg-slate-900 px-3 py-2 flex items-center justify-between text-white text-[10px] font-bold">
                  <span>OCR Character Layout Visualizer</span>
                  <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-400/40">Deskewed</span>
                </div>
                <div className="h-[280px] bg-slate-950 flex items-center justify-center relative overflow-hidden">
                  {/* Bounding box grid mock */}
                  <div className="absolute inset-0 grid grid-cols-6 grid-rows-6 opacity-10 gap-1 p-2">
                    {Array.from({ length: 36 }).map((_, i) => (
                      <div key={i} className="border border-blue-400 rounded-xs" />
                    ))}
                  </div>
                  <div className="border border-blue-400/60 bg-blue-500/10 rounded p-2 text-blue-400 font-mono text-[9px] text-center rotate-[0.5deg]">
                    [01/08/2026] [OPENING BALANCE] [12,540.50]
                  </div>
                  <div className="border border-blue-400/60 bg-blue-500/10 rounded p-2 text-blue-400 font-mono text-[9px] text-center translate-y-8 rotate-[0.5deg]">
                    [03/08/2026] [PAYROLL CRED] [4,500.00]
                  </div>
                  <div className="absolute bottom-3 right-3 bg-slate-900/80 p-1.5 rounded-lg text-white opacity-0 group-hover:opacity-100 transition cursor-pointer">
                    <Maximize2 className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>

              <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                    <span className="font-extrabold text-xs text-slate-800">Validation & Accuracy Metrics</span>
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                      <ShieldCheck className="w-3 h-3 text-emerald-600" /> Validation OK
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 pt-3 text-xs">
                    <div>
                      <span className="text-slate-400 font-semibold block text-[10px]">Row Recognition Accuracy</span>
                      <span className="font-bold text-slate-800 text-sm">99.4% (Tesseract OCR)</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block text-[10px]">Page Count</span>
                      <span className="font-bold text-slate-800 text-sm">1 Page</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block text-[10px]">Running Balance Check</span>
                      <span className="font-bold text-emerald-600 text-sm">Matched (Zero Mismatch)</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-semibold block text-[10px]">Processing Time</span>
                      <span className="font-bold text-slate-800 text-sm">8.4s</span>
                    </div>
                  </div>
                </div>
                <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-[11px] text-amber-800 font-medium leading-relaxed">
                  <AlertTriangle className="w-4 h-4 text-amber-600 inline mr-1.5 align-text-bottom" />
                  Note: Row #5 contains <span className="font-bold">LOW CONFIDENCE</span> characters due to faint scan pixel contrast. Corrected via binarization matching.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reconstructed Excel Table Viewer */}
      {showResult && (
        <div className="h-[480px]">
          <TableViewer transactions={simulatedTransactions} />
        </div>
      )}
    </div>
  );
};
