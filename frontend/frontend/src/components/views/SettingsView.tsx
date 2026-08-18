import React, { useState, useEffect } from 'react';
import { Save, Check, CheckCircle2, AlertCircle } from 'lucide-react';
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
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-base font-bold text-slate-900">Engine Configuration & Rule Settings</h2>
              {isBackendConnected !== undefined && (
                <div
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
                    isBackendConnected
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}
                >
                  {isBackendConnected ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      REST API Connected
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                      Backend Offline
                    </>
                  )}
                </div>
              )}
            </div>
            <p className="text-xs text-slate-500">
              Customize PDF parsing priority, arithmetic validation tolerances, Excel formatting, and OCR fallbacks.
            </p>
          </div>
          <button
            type="submit"
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white font-bold text-xs rounded-lg hover:bg-blue-700 transition"
          >
            {savedSuccess ? (
              <>
                <Check className="w-4 h-4" /> Settings Saved!
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> Save Configuration
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* Section 1: Extraction & Engine */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm">Extraction Pipeline Settings</h3>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Extraction Priority</label>
              <select
                value={formData.extraction_priority}
                onChange={(e) =>
                  setFormData({ ...formData, extraction_priority: e.target.value })
                }
                className="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium"
              >
                <option value="Accuracy First">Accuracy First (Run All Engines & Score)</option>
                <option value="Speed First">Speed First (Use Fast Vector Heuristics)</option>
                <option value="Balanced">Balanced Mode</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Preferred Extraction Engine
              </label>
              <select
                value={formData.preferred_engine}
                onChange={(e) =>
                  setFormData({ ...formData, preferred_engine: e.target.value })
                }
                className="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium"
              >
                <option value="Auto Multi-Engine Pipeline">Auto Multi-Engine Pipeline (Recommended)</option>
                <option value="HDFC Bank Statement">HDFC Bank Statement (Special Extractor)</option>
                <option value="Axis Bank Statement">Axis Bank Statement (Special Extractor)</option>
                <option value="ICICI Bank Statement">ICICI Bank Statement (Special Extractor)</option>
                <option value="IndusInd Bank Statement">IndusInd Bank Statement (Special Extractor)</option>

              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Minimum Confidence Threshold: {formData.confidence_threshold}%
              </label>
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
                className="w-full accent-blue-600"
              />
            </div>
          </div>

          {/* Section 2: Validation Rules */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm">Validation & Reconciliation Rules</h3>

            <div className="space-y-2">
              <label className="flex items-center gap-2 font-semibold text-slate-700">
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
                  className="rounded border-slate-300 text-blue-600"
                />
                Enable Running Balance Arithmetic Verification
              </label>

              <label className="flex items-center gap-2 font-semibold text-slate-700">
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
                  className="rounded border-slate-300 text-blue-600"
                />
                Flag Duplicate Transaction Rows
              </label>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
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
                className="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium"
              />
            </div>
          </div>

          {/* Section 3: Excel Output Settings */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm">Excel & Workbook Output</h3>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Excel Color Theme</label>
              <select
                value={formData.excel_output.styling}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    excel_output: { ...formData.excel_output, styling: e.target.value }
                  })
                }
                className="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium"
              >
                <option value="Corporate Blue">Corporate Navy Blue Header</option>
                <option value="Emerald Finance">Emerald Green Header</option>
                <option value="Classic Slate">Classic Dark Slate</option>
              </select>
            </div>

            <label className="flex items-center gap-2 font-semibold text-slate-700">
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
                className="rounded border-slate-300 text-blue-600"
              />
              Generate Executive Summary Worksheet
            </label>
          </div>

          {/* Section 4: OCR & DeepSeek AI Options */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm">DeepSeek AI & OCR Options</h3>

            <label className="flex items-center gap-2 font-semibold text-slate-700">
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
                className="rounded border-slate-300 text-blue-600"
              />
              Enable Automatic OCR Fallback for Scanned PDF Statements
            </label>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">OCR Engine Provider</label>
              <select
                value={formData.ocr_options.ocr_engine}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ocr_options: { ...formData.ocr_options, ocr_engine: e.target.value }
                  })
                }
                className="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium"
              >
                <option value="PaddleOCR (PP-OCRv4)">PaddleOCR (PP-OCRv4 Deep Learning)</option>
                <option value="Tesseract OCR (v5.3)">Tesseract OCR (Local Native)</option>
                <option value="AWS Textract API">AWS Textract API (Cloud)</option>
                <option value="Google Vision OCR">Google Cloud Vision OCR</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </form>
  );
};
