import React, { useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';

import { PdfExtractionView } from './components/views/PdfExtractionView';
import type {
  FileCard,
  ExtractionResult
} from './types';

import {
  uploadFiles,
  extractPdf,
  retryExtraction,
  generateExcel,
  fetchFileStatus,
  deleteFile
} from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('extraction');

  // Application State
  const [files, setFiles] = useState<FileCard[]>([]);
  const [results, setResults] = useState<Record<string, ExtractionResult>>({});
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

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

    // Create optimistic temporary cards for instantaneous zero-latency UI feedback
    const tempCards: FileCard[] = rawFiles.map((f, idx) => ({
      id: `temp_${Date.now()}_${idx}`,
      filename: f.name,
      file_path: f.name,
      pdf_type: 'Analyzing...',
      pages: 1,
      file_size: `${(f.size / (1024 * 1024)).toFixed(2)} MB`,
      status: 'Ready',
      extraction_method: 'Auto Multi-Engine Pipeline',
      progress: 0,
      confidence_score: 0.0,
      validation_status: 'Pending',
      detect_msg: 'Registering document...',
      uploaded_at: new Date().toISOString()
    }));

    setFiles((prev) => [...prev, ...tempCards]);

    try {
      const uploadedCards = await uploadFiles(rawFiles);
      setFiles((prev) => [
        ...prev.filter((f) => !f.id.startsWith('temp_')),
        ...uploadedCards
      ]);
      showToast(`Registered ${uploadedCards.length} PDF statement(s).`);
    } catch (err: any) {
      setFiles((prev) => prev.filter((f) => !f.id.startsWith('temp_')));
      showToast(err.message || 'Failed to upload files', 'error');
    }
  };


  const handleRemoveFile = (id: string) => {
    deleteFile(id);
    setFiles((prev) => prev.filter((f) => f.id !== id));
    setResults((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const handleExtractFiles = async (
    fileIds: string[],
    engineOverrides?: Record<string, string>,
    engineOverride?: string
  ) => {
    if (fileIds.length === 0) return;
    setIsProcessing(true);

    setFiles((prev) =>
      prev.map((f) =>
        fileIds.includes(f.id) ? { ...f, status: 'Extracting', progress: 40 } : f
      )
    );

    // Dynamic status polling every 800ms to show live processing logs
    const pollInterval = setInterval(async () => {
      try {
        const statuses = await Promise.all(
          fileIds.map(async (id) => {
            const status = await fetchFileStatus(id);
            return { id, ...status };
          })
        );
        setFiles((prev) =>
          prev.map((f) => {
            const polled = statuses.find((s) => s.id === f.id);
            if (polled) {
              return {
                ...f,
                progress: polled.progress || f.progress,
                detect_msg: polled.detect_msg
              };
            }
            return f;
          })
        );
      } catch (e) {
        console.error("Progress polling failed:", e);
      }
    }, 800);


    try {
      const extractionResults = await extractPdf(fileIds, engineOverrides, engineOverride);

      const newResultsMap: Record<string, ExtractionResult> = {};

      extractionResults.forEach((res) => {
        newResultsMap[res.file_id] = res;
      });

      setResults((prev) => ({ ...prev, ...newResultsMap }));

      setFiles((prev) =>
        prev.map((f) => {
          const res = newResultsMap[f.id];
          if (res) {
            return {
              ...f,
              status: res.success ? 'Completed' : 'Failed',
              progress: 100,
              confidence_score: res.confidence_score,
              extraction_method: res.engine_used,
              validation_status:
                res.summary.failed_count === 0 ? 'OK' : 'Warnings'
            };
          }
          return f;
        })
      );

      showToast(`Extraction complete for ${extractionResults.length} statement(s).`);
    } catch (err: any) {
      showToast(err.message || 'Extraction execution failed', 'error');
      setFiles((prev) =>
        prev.map((f) =>
          fileIds.includes(f.id) ? { ...f, status: 'Failed', progress: 100 } : f
        )
      );
    } finally {
      clearInterval(pollInterval);
      setIsProcessing(false);
    }
  };

  const handleRetryFile = async (fileId: string, preferredEngine: string) => {
    setIsProcessing(true);
    try {
      const result = await retryExtraction(fileId, preferredEngine);
      setResults((prev) => ({ ...prev, [fileId]: result }));
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: 'Completed',
                progress: 100,
                confidence_score: result.confidence_score,
                extraction_method: result.engine_used
              }
            : f
        )
      );
      showToast(`Re-extracted ${result.filename} using ${preferredEngine}.`);
    } catch (err: any) {
      showToast(err.message || 'Retry failed', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGenerateExport = async (fileIds: string[], format: 'xlsx' | 'csv') => {
    try {
      const { blob, filename } = await generateExcel(fileIds, format);
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(blobUrl);
      showToast(`Exported ${filename} successfully!`);
    } catch (err: any) {
      showToast(err.message || 'Failed to generate export file', 'error');
    }
  };



  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900">
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl border text-xs font-bold transition-all ${
            toast.type === 'success'
              ? 'bg-emerald-600 text-white border-emerald-500'
              : 'bg-rose-600 text-white border-rose-500'
          }`}
        >
          {toast.message}
        </div>
      )}

      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar
          activeTab={activeTab}
          processingCount={isProcessing ? files.length : 0}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
          {activeTab === 'extraction' && (
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
          )}



        </main>
      </div>
    </div>
  );
}
