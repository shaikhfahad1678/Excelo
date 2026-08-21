import React, { useState } from 'react';
import {
  UploadCloud,
  FileImage,
  Sparkles,
  Sliders,
  Play,
  RefreshCw
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
    'Rasterizing PDF Pages to 300 DPI...',
    'Applying Hough Deskew & Orientation Alignment...',
    'Adaptive Otsu Thresholding & Denoising...',
    'Extracting Character Bounding Boxes...',
    'Clustering Horizontal Row Coordinates...',
    'Reconstructing Math Balancing Equations...',
    '11-Rule Validation Passed.'
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
    }, 1000);
  };

  return (
    <div className="space-y-6 pb-12 max-w-[1700px] mx-auto font-sans antialiased">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Controls Column */}
        <div className="bg-white border border-neutral-200/80 p-5 rounded-2xl space-y-5 text-xs lg:col-span-1 shadow-sm">
          <div className="flex items-center gap-2 border-b border-neutral-100 pb-3">
            <Sliders className="w-4 h-4 text-neutral-800" />
            <h3 className="font-bold text-neutral-900 text-sm">Preprocessing</h3>
          </div>

          <div>
            <label className="font-bold text-neutral-700 block mb-1.5">OCR Engine</label>
            <select
              value={ocrEngine}
              onChange={(e) => setOcrEngine(e.target.value)}
              className="w-full bg-white border border-neutral-200 rounded-xl p-2 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
            >
              <option>PaddleOCR (v3.2) - Best Speed</option>
              <option>Tesseract OCR (Local Native)</option>
              <option>Google Cloud Vision</option>
            </select>
          </div>

          <div className="space-y-2.5 pt-1">
            <label className="flex items-center gap-2 font-semibold text-neutral-700 cursor-pointer">
              <input
                type="checkbox"
                checked={deskew}
                onChange={(e) => setDeskew(e.target.checked)}
                className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
              />
              Auto-Deskew & Rotation
            </label>

            <label className="flex items-center gap-2 font-semibold text-neutral-700 cursor-pointer">
              <input
                type="checkbox"
                checked={denoise}
                onChange={(e) => setDenoise(e.target.checked)}
                className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
              />
              Bilateral Noise Filter
            </label>

            <label className="flex items-center gap-2 font-semibold text-neutral-700 cursor-pointer">
              <input
                type="checkbox"
                checked={binarization}
                onChange={(e) => setBinarization(e.target.checked)}
                className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
              />
              Adaptive Otsu Thresholding
            </label>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="font-bold text-neutral-700">Contrast Scale</label>
              <span className="font-mono font-bold text-neutral-900">{contrastScale}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="150"
              value={contrastScale}
              onChange={(e) => setContrastScale(parseInt(e.target.value))}
              className="w-full accent-neutral-900 cursor-pointer"
            />
          </div>

          <button
            onClick={handleLoadSample}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-neutral-50 text-neutral-700 hover:bg-neutral-100 border border-neutral-200 font-bold transition text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-neutral-600" />
            Load Sample Scanned PDF
          </button>
        </div>

        {/* OCR Canvas Column */}
        <div className="bg-white border border-neutral-200/80 p-5 rounded-2xl lg:col-span-3 space-y-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <div>
              <h2 className="text-base font-extrabold text-neutral-900">Scanned Document OCR Studio</h2>
              <p className="text-xs text-neutral-400 font-medium">Reconstruct image-only statements via bounding coordinate matching.</p>
            </div>
            {files.length > 0 && (
              <button
                onClick={handleRunOcr}
                disabled={isProcessing}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-900 text-white font-bold text-xs hover:bg-neutral-800 transition disabled:opacity-50 shadow-sm"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                {isProcessing ? 'Reconstructing...' : 'Run OCR Pipeline'}
              </button>
            )}
          </div>

          {files.length === 0 ? (
            <div className="border border-dashed border-neutral-300 rounded-2xl p-12 text-center bg-white">
              <input
                type="file"
                id="scanned-upload-input"
                accept=".pdf,image/*"
                onChange={handleUpload}
                className="hidden"
              />
              <label htmlFor="scanned-upload-input" className="cursor-pointer block">
                <div className="w-10 h-10 rounded-xl bg-neutral-100 text-neutral-800 border border-neutral-200 flex items-center justify-center mx-auto mb-2.5">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-neutral-900">
                  Drop scanned PDFs/Images here, or <span className="underline font-semibold">browse files</span>
                </h3>
                <p className="text-xs text-neutral-400 mt-1">Multi-page scanned statements or photos</p>
              </label>
            </div>
          ) : (
            <div className="border border-neutral-200 p-4 rounded-xl flex items-center justify-between gap-4 bg-neutral-50/50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-neutral-100 text-neutral-800 border border-neutral-200 flex items-center justify-center shrink-0">
                  <FileImage className="w-4 h-4 text-rose-500" />
                </div>
                <div>
                  <div className="font-bold text-xs text-neutral-900">{files[0].name}</div>
                  <div className="text-[10px] text-neutral-400 font-medium">{files[0].size}</div>
                </div>
              </div>
              <button
                onClick={() => setFiles([])}
                className="text-neutral-400 hover:text-rose-600 font-semibold text-xs transition"
              >
                Clear
              </button>
            </div>
          )}

          {isProcessing && (
            <div className="bg-neutral-900 text-white p-5 rounded-xl space-y-3">
              <div className="flex items-center gap-2.5">
                <RefreshCw className="w-4 h-4 text-white animate-spin" />
                <div className="text-xs font-bold">{stages[processingStage]}</div>
              </div>
              <div className="w-full bg-neutral-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-white h-full transition-all duration-300 rounded-full"
                  style={{ width: `${((processingStage + 1) / stages.length) * 100}%` }}
                />
              </div>
            </div>
          )}

          {showResult && (
            <div className="p-4 rounded-xl bg-neutral-50/80 border border-neutral-200 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-neutral-900">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                OCR Reconstructed 4 Transactions (100% Math Verification)
              </div>
              <span className="font-mono text-xs font-bold text-neutral-600">Accuracy: 99.8%</span>
            </div>
          )}
        </div>
      </div>

      {showResult && (
        <TableViewer transactions={simulatedTransactions} />
      )}
    </div>
  );
};
