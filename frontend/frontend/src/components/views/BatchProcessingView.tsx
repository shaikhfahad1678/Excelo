import React from 'react';
import { Play, Download } from 'lucide-react';
import type { FileCard, ExtractionResult } from '../../types';

interface BatchProcessingViewProps {
  files: FileCard[];
  onExtractAll: () => void;
  onExportAll: (format: 'xlsx' | 'csv') => void;
  isProcessing: boolean;
  results: Record<string, ExtractionResult>;
}

export const BatchProcessingView: React.FC<BatchProcessingViewProps> = ({
  files,
  onExtractAll,
  onExportAll,
  isProcessing,
  results
}) => {
  const completedCount = Object.keys(results).length;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Enterprise Batch Processing Workspace</h2>
            <p className="text-xs text-slate-500">
              Process hundreds of monthly bank statement PDFs in parallel into a single multi-sheet Excel workbook.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onExtractAll}
              disabled={files.length === 0 || isProcessing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-bold text-xs hover:bg-blue-700 disabled:opacity-50 transition"
            >
              <Play className="w-4 h-4 fill-white" />
              {isProcessing ? 'Batch Processing...' : `Process ${files.length} Files`}
            </button>
            {completedCount > 0 && (
              <button
                onClick={() => onExportAll('xlsx')}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg font-bold text-xs hover:bg-emerald-700 transition"
              >
                <Download className="w-4 h-4" />
                Consolidated Excel Export
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-xl bg-slate-50/50">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3">#</th>
                <th className="p-3">Filename</th>
                <th className="p-3">Pages</th>
                <th className="p-3">File Size</th>
                <th className="p-3">Engine Method</th>
                <th className="p-3 text-center">Status</th>
                <th className="p-3 text-right">Extracted Rows</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {files.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400 font-sans">
                    No files loaded in batch queue. Drag files into PDF Extraction workspace to queue them.
                  </td>
                </tr>
              ) : (
                files.map((file, i) => {
                  const res = results[file.id];
                  return (
                    <tr key={file.id} className="hover:bg-white transition">
                      <td className="p-3 font-sans text-slate-400">{i + 1}</td>
                      <td className="p-3 font-sans font-bold text-slate-800">{file.filename}</td>
                      <td className="p-3 text-slate-600">{file.pages}</td>
                      <td className="p-3 text-slate-600">{file.file_size}</td>
                      <td className="p-3 text-blue-600 font-sans">{file.extraction_method}</td>
                      <td className="p-3 text-center font-sans">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            res?.success
                              ? 'bg-emerald-100 text-emerald-800'
                              : isProcessing
                              ? 'bg-blue-100 text-blue-800 animate-pulse'
                              : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {res?.success ? 'Completed' : file.status}
                        </span>
                      </td>
                      <td className="p-3 text-right font-bold text-slate-900">
                        {res ? res.summary.total_count : '-'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
