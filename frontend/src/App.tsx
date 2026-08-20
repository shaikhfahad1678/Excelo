import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { PdfExtractionView } from './components/views/PdfExtractionView';

import type {
  FileCard,
  ExtractionResult
} from './types';

import {
  uploadFiles,
  generateSamplePdf,
  extractPdf,
  retryExtraction,
  generateExcel,
  checkHealth,
  fetchFileStatus
} from './services/api';

export function App() {
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(true);

  // Application State
  const [files, setFiles] = useState<FileCard[]>([]);
  const [results, setResults] = useState<Record<string, ExtractionResult>>({});
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const refreshData = async () => {
    const health = await checkHealth();
    setIsBackendConnected(health);
  };

  useEffect(() => {
    refreshData();
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

    const tempCards: FileCard[] = rawFiles.map((f, idx) => ({
      id: `temp_${Date.now()}_${idx}`,
      filename: f.name,
      file_path: f.name,
      pdf_type: 'Analyzing...',
      pages: 1,
      file_size: `${(f.size / (1024 * 1024)).toFixed(2)} MB`,
      status: 'Ready',
      extraction_method: 'Auto-Detecting...',
      progress: 0,
      confidence_score: 0.0,
      validation_status: 'Pending',
      detect_msg: 'Auto-detecting statement type...',
      uploaded_at: new Date().toISOString()
    }));

    setFiles((prev) => [...prev, ...tempCards]);

    try {
      const uploadedCards = await uploadFiles(rawFiles);
      setFiles((prev) => [
        ...prev.filter((f) => !f.id.startsWith('temp_')),
        ...uploadedCards
      ]);
      showToast(`Registered & auto-detected ${uploadedCards.length} statement(s).`);
    } catch (err: any) {
      setFiles((prev) => prev.filter((f) => !f.id.startsWith('temp_')));
      showToast(err.message || 'Failed to upload files', 'error');
    }
  };

  const handleLoadSample = async () => {
    try {
      const sampleCard = await generateSamplePdf();
      setFiles((prev) => [sampleCard, ...prev]);
      showToast('Loaded synthetic sample bank statement into workspace.');
    } catch (err: any) {
      showToast('Error generating sample PDF', 'error');
    }
  };

  const handleRemoveFile = (id: string) => {
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
        console.error('Progress polling failed:', e);
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
      refreshData();
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
      refreshData();
    } catch (err: any) {
      showToast(err.message || 'Retry failed', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGenerateExport = async (fileIds: string[], format: 'xlsx' | 'csv') => {
    try {
      await generateExcel(fileIds, format);
      showToast(`Exported ${format.toUpperCase()} successfully.`);
    } catch (err: any) {
      showToast('Export failed', 'error');
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#fafafa] font-sans text-neutral-900">
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-xl border transition-all animate-bounce ${
            toast.type === 'success'
              ? 'bg-neutral-900 text-white border-neutral-800'
              : 'bg-rose-600 text-white border-rose-500'
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
          onLoadSample={handleLoadSample}
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
