import React, { useState, useEffect } from 'react';
import { Save, Check, Sliders, Shield, FileSpreadsheet, Eye } from 'lucide-react';
import type { Settings } from '../../types';

interface SettingsViewProps {
  settings: Settings;
  onSaveSettings: (updated: Settings) => void;
  isBackendConnected?: boolean;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  settings,
  onSaveSettings,
  isBackendConnected
}) => {
  const [formData, setFormData] = useState<Settings>(settings);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    setFormData(settings);
  }, [settings]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSaveSettings(formData);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-[1400px] mx-auto font-sans">
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/80 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-100 pb-5">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-lg font-extrabold text-neutral-900 tracking-tight">
                Engine Preferences & Ledger Rules
              </h2>
              {isBackendConnected !== undefined && (
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                    isBackendConnected
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200/60'
                      : 'bg-rose-50 text-rose-800 border-rose-200/60'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${isBackendConnected ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                  {isBackendConnected ? 'API Connected' : 'API Offline'}
                </span>
              )}
            </div>
            <p className="text-xs text-neutral-400 font-medium">
              Configure extraction priorities, validation thresholds, and Excel output properties.
            </p>
          </div>

          <button
            type="submit"
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-neutral-900 text-white font-bold text-xs rounded-xl hover:bg-neutral-800 transition shadow-sm"
          >
            {savedSuccess ? (
              <>
                <Check className="w-4 h-4 text-emerald-400" /> Saved Successfully
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> Save Preferences
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
          {/* Section 1: Extraction Engine Preferences */}
          <div className="space-y-4 p-5 rounded-2xl bg-neutral-50/60 border border-neutral-200/70">
            <div className="flex items-center gap-2 text-neutral-900 font-bold text-sm">
              <Sliders className="w-4 h-4 text-neutral-700" />
              <h3>Extraction Pipeline Controls</h3>
            </div>

            <div>
              <label className="font-bold text-neutral-700 block mb-1.5">Extraction Strategy Priority</label>
              <select
                value={formData.extraction_priority}
                onChange={(e) =>
                  setFormData({ ...formData, extraction_priority: e.target.value })
                }
                className="w-full bg-white border border-neutral-200 rounded-xl p-2.5 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
              >
                <option value="Accuracy First">Accuracy First (Run Multi-Engine Scoring)</option>
                <option value="Speed First">Speed First (Vector Heuristics)</option>
                <option value="Balanced">Balanced Processing</option>
              </select>
            </div>

            <div>
              <label className="font-bold text-neutral-700 block mb-1.5">
                Default Extraction Extractor
              </label>
              <select
                value={formData.preferred_engine}
                onChange={(e) =>
                  setFormData({ ...formData, preferred_engine: e.target.value })
                }
                className="w-full bg-white border border-neutral-200 rounded-xl p-2.5 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
              >
                <option value="Auto Multi-Engine Pipeline">Auto Multi-Engine Pipeline (Recommended)</option>
                <option value="Kotak Bank Statement">Kotak Bank Statement (Special Extractor)</option>
                <option value="PNB Bank Statement">PNB Bank Statement (Special Extractor)</option>
                <option value="Union Bank Statement">Union Bank Statement (Special Extractor)</option>
                <option value="Yes Bank Statement">Yes Bank Statement (Special Extractor)</option>
                <option value="HDFC Bank Statement">HDFC Bank Statement (Special Extractor)</option>
                <option value="Axis Bank Statement">Axis Bank Statement (Special Extractor)</option>
                <option value="ICICI Bank Statement">ICICI Bank Statement (Special Extractor)</option>
                <option value="IndusInd Bank Statement">IndusInd Bank Statement (Special Extractor)</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="font-bold text-neutral-700">
                  Confidence Threshold
                </label>
                <span className="font-mono font-bold text-neutral-900 bg-white px-2 py-0.5 rounded border border-neutral-200">
                  {formData.confidence_threshold}%
                </span>
              </div>
              <input
                type="range"
                min="50"
                max="100"
                value={formData.confidence_threshold}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    confidence_threshold: parseFloat(e.target.value)
                  })
                }
                className="w-full accent-neutral-900 cursor-pointer"
              />
            </div>
          </div>

          {/* Section 2: Validation & Math Rules */}
          <div className="space-y-4 p-5 rounded-2xl bg-neutral-50/60 border border-neutral-200/70">
            <div className="flex items-center gap-2 text-neutral-900 font-bold text-sm">
              <Shield className="w-4 h-4 text-neutral-700" />
              <h3>Ledger Validation & Math Checks</h3>
            </div>

            <div className="space-y-3 pt-1">
              <label className="flex items-center gap-2.5 font-semibold text-neutral-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.validation_rules.arithmetic_check}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      validation_rules: {
                        ...formData.validation_rules,
                        arithmetic_check: e.target.checked
                      }
                    })
                  }
                  className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
                />
                Verify Running Balance Equation (Opening + Credit - Debit = Balance)
              </label>

              <label className="flex items-center gap-2.5 font-semibold text-neutral-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.validation_rules.duplicate_check}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      validation_rules: {
                        ...formData.validation_rules,
                        duplicate_check: e.target.checked
                      }
                    })
                  }
                  className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
                />
                Flag Duplicate Transaction Rows
              </label>
            </div>

            <div>
              <label className="font-bold text-neutral-700 block mb-1.5">
                Balance Mismatch Tolerance (Currency Unit)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.validation_rules.tolerance}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    validation_rules: {
                      ...formData.validation_rules,
                      tolerance: parseFloat(e.target.value) || 0.05
                    }
                  })
                }
                className="w-full bg-white border border-neutral-200 rounded-xl p-2.5 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
              />
            </div>
          </div>

          {/* Section 3: Excel Output Options */}
          <div className="space-y-4 p-5 rounded-2xl bg-neutral-50/60 border border-neutral-200/70">
            <div className="flex items-center gap-2 text-neutral-900 font-bold text-sm">
              <FileSpreadsheet className="w-4 h-4 text-neutral-700" />
              <h3>Excel Workbook Customization</h3>
            </div>

            <div>
              <label className="font-bold text-neutral-700 block mb-1.5">Header Styling Theme</label>
              <select
                value={formData.excel_output.styling}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    excel_output: { ...formData.excel_output, styling: e.target.value }
                  })
                }
                className="w-full bg-white border border-neutral-200 rounded-xl p-2.5 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
              >
                <option value="Corporate Blue">Corporate Navy Header</option>
                <option value="Emerald Finance">Emerald Green Header</option>
                <option value="Classic Slate">Classic Charcoal Header</option>
              </select>
            </div>

            <label className="flex items-center gap-2.5 font-semibold text-neutral-700 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.excel_output.include_summary_sheet}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    excel_output: {
                      ...formData.excel_output,
                      include_summary_sheet: e.target.checked
                    }
                  })
                }
                className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
              />
              Generate Executive Financial Summary Sheet
            </label>
          </div>

          {/* Section 4: OCR Fallback Engine */}
          <div className="space-y-4 p-5 rounded-2xl bg-neutral-50/60 border border-neutral-200/70">
            <div className="flex items-center gap-2 text-neutral-900 font-bold text-sm">
              <Eye className="w-4 h-4 text-neutral-700" />
              <h3>OCR Fallback Settings</h3>
            </div>

            <label className="flex items-center gap-2.5 font-semibold text-neutral-700 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.ocr_options.enable_ocr_fallback}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ocr_options: {
                      ...formData.ocr_options,
                      enable_ocr_fallback: e.target.checked
                    }
                  })
                }
                className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
              />
              Enable Automatic OCR Fallback for Non-Digital Statements
            </label>

            <div>
              <label className="font-bold text-neutral-700 block mb-1.5">OCR Provider</label>
              <select
                value={formData.ocr_options.ocr_engine}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ocr_options: { ...formData.ocr_options, ocr_engine: e.target.value }
                  })
                }
                className="w-full bg-white border border-neutral-200 rounded-xl p-2.5 font-semibold text-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-900"
              >
                <option value="PaddleOCR (PP-OCRv4)">PaddleOCR (PP-OCRv4)</option>
                <option value="Tesseract OCR (v5.3)">Tesseract OCR (Native Local)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </form>
  );
};
