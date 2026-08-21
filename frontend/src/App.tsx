import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { PdfExtractionView } from './components/views/PdfExtractionView';
import type { FileCard, ExtractionResult } from './types';
import {
  uploadFiles,
  extractPdf,
  retryExtraction,
  generateExcel,
  checkHealth,
  fetchFileStatus,
  deleteFile
} from './services/api';

export function App() {
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(true);
  const [files, setFiles] = useState<FileCard[]>([]);
  const [results, setResults] = useState<Record<string, ExtractionResult>>({});
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const refreshHealth = async () => {
    const health = await checkHealth();
    setIsBackendConnected(health);
  };

  useEffect(() => {
    refreshHealth();
  }, []);

  const handleUploadFiles = async (
    e: React.ChangeEvent<HTMLInputElement> | React.DragEvent
  ) => {
    let rawFiles: File[] = [];
    if ('dataTransfer' in e && e.dataTransfer?.files) {
      rawFiles = Array.from(e.dataTransfer.files);
    } else if ('target' in e && (e.target as HTMLInputElement).files) {
      const input = e.target as HTMLInputElement;
      if (input.files) {
        rawFiles = Array.from(input.files);
      }
    }

    if (rawFiles.length === 0) return;

    const pdfOnly = rawFiles.filter((f) => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfOnly.length === 0) {
      showToast('Only standard PDF statement files are supported.', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      const newCards = await uploadFiles(pdfOnly);
      setFiles((prev) => {
        const existingIds = new Set(prev.map((c) => c.id));
        const filtered = newCards.filter((c) => !existingIds.has(c.id));
        return [...prev, ...filtered];
      });
      showToast(`Successfully imported ${newCards.length} PDF statement(s).`);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to upload files.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRemoveFile = async (id: string) => {
    await deleteFile(id);
    setFiles((prev) => prev.filter((f) => f.id !== id));
    setResults((prev) => {
      const updated = { ...prev };
      delete updated[id];
      return updated;
    });
    showToast('Document removed from workspace.');
  };

  const handleExtractFiles = async (
    fileIds: string[],
    engineOverrides?: Record<string, string>,
    engineOverride?: string
  ) => {
    if (fileIds.length === 0) return;
    setIsProcessing(true);

    try {
      setFiles((prev) =>
        prev.map((c) =>
          fileIds.includes(c.id) ? { ...c, status: 'Extracting', progress: 30 } : c
        )
      );

      const pollInterval = setInterval(async () => {
        for (const fid of fileIds) {
          try {
            const st = await fetchFileStatus(fid);
            setFiles((prev) =>
              prev.map((c) =>
                c.id === fid
                  ? { ...c, progress: Math.max(c.progress, st.progress), detect_msg: st.detect_msg || c.detect_msg }
                  : c
              )
            );
          } catch (e) {}
        }
      }, 800);

      const extractionOutputs = await extractPdf(fileIds, engineOverrides, engineOverride);
      clearInterval(pollInterval);

      const newResultsMap: Record<string, ExtractionResult> = {};
      extractionOutputs.forEach((res) => {
        newResultsMap[res.file_id] = res;
      });
      setResults((prev) => ({ ...prev, ...newResultsMap }));

      setFiles((prev) =>
        prev.map((c) => {
          const res = newResultsMap[c.id];
          if (!res) return c;
          return {
            ...c,
            status: res.success ? 'Completed' : 'Failed',
            progress: 100,
            confidence_score: res.confidence_score,
            validation_status: res.summary?.is_valid ? 'OK' : 'Errors',
            extraction_method: res.engine_used || c.extraction_method,
            detect_msg: res.success ? `Extracted via ${res.engine_used}` : (res.error || 'Extraction failed')
          };
        })
      );

      showToast(`Extraction complete for ${extractionOutputs.length} document(s).`);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Extraction pipeline encountered an error.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRetryFile = async (fileId: string, preferredEngine: string) => {
    setIsProcessing(true);
    try {
      const res = await retryExtraction(fileId, preferredEngine);
      setResults((prev) => ({ ...prev, [fileId]: res }));
      setFiles((prev) =>
        prev.map((c) =>
          c.id === fileId
            ? {
                ...c,
                status: res.success ? 'Completed' : 'Failed',
                confidence_score: res.confidence_score,
                validation_status: res.summary?.is_valid ? 'OK' : 'Errors',
                extraction_method: res.engine_used,
                detect_msg: res.success ? `Re-extracted via ${res.engine_used}` : res.error
              }
            : c
        )
      );
      showToast(`Statement re-extracted using ${preferredEngine}.`);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Retry failed.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGenerateExport = async (fileIds: string[], format: 'xlsx' | 'csv') => {
    if (fileIds.length === 0) {
      showToast('Please select at least one processed document to export.', 'error');
      return;
    }

    try {
      showToast(`Generating ${format.toUpperCase()} export...`);
      const { blob, filename } = await generateExcel(fileIds, format);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      showToast(`Export downloaded: ${filename}`);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Export generation failed.', 'error');
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50/50 text-slate-800 font-sans antialiased">
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-lg border text-xs font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-5 duration-200 ${
            toast.type === 'error'
              ? 'bg-rose-50 text-rose-800 border-rose-200'
              : 'bg-emerald-50 text-emerald-800 border-emerald-200'
          }`}
        >
          {toast.message}
        </div>
      )}

      <Navbar
        processingCount={isProcessing ? files.length : 0}
        isBackendConnected={isBackendConnected}
      />

      <main className="flex-1 overflow-y-auto px-6 py-8">
        <PdfExtractionView
          files={files}
          onUploadFiles={handleUploadFiles}
          onRemoveFile={handleRemoveFile}
          onExtractFiles={handleExtractFiles}
          onRetryFile={handleRetryFile}
          onGenerateExport={handleGenerateExport}
          results={results}
          isProcessing={isProcessing}
        />
      </main>
    </div>
  );
}
