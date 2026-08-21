import axios from 'axios';
import type {
  FileCard,
  ExtractionResult,
  Transaction,
  Summary
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadFiles = async (files: File[]): Promise<FileCard[]> => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data.files;
};

export const extractPdf = async (
  fileIds: string[],
  engineOverrides?: Record<string, string>,
  engineOverride?: string
): Promise<ExtractionResult[]> => {
  const res = await api.post('/extract', {
    file_ids: fileIds,
    engine_override: engineOverride,
    engine_overrides: engineOverrides,
  });
  return res.data.results;
};

export const validateTransactions = async (
  transactions: Transaction[],
  tolerance: number = 0.05
): Promise<{ transactions: Transaction[]; summary: Summary }> => {
  const res = await api.post('/validate', { transactions, tolerance });
  return res.data;
};

export const retryExtraction = async (
  fileId: string,
  preferredEngine: string
): Promise<ExtractionResult> => {
  const res = await api.post('/retry', {
    file_id: fileId,
    preferred_engine: preferredEngine,
  });
  return res.data.result;
};

export const generateExcel = async (
  fileIds: string[],
  format: 'xlsx' | 'csv' = 'xlsx'
): Promise<{ blob: Blob; filename: string }> => {
  const res = await api.post('/generate-excel', {
    file_ids: fileIds,
    format,
  });
  const { filename } = res.data as { download_url: string; filename: string };

  const blobRes = await api.get(`/download/${encodeURIComponent(filename)}`, {
    responseType: 'blob',
  });

  return { blob: blobRes.data, filename };
};

export const checkHealth = async (): Promise<boolean> => {
  try {
    const res = await api.get('/health');
    return res.data.status === 'online';
  } catch (err) {
    return false;
  }
};

export const fetchFileStatus = async (
  fileId: string
): Promise<{ progress: number; detect_msg: string }> => {
  const res = await api.get(`/files/${fileId}/status`);
  return res.data;
};

export const deleteFile = async (fileId: string): Promise<boolean> => {
  try {
    const res = await api.delete(`/files/${fileId}`);
    return res.data.status === 'success';
  } catch (err) {
    return false;
  }
};

export const checkCloudflareStatus = async (): Promise<{
  configured: boolean;
  connected: boolean;
  status: string;
  message: string;
  bucket?: string;
}> => {
  try {
    const res = await api.get('/cloudflare/status');
    return res.data;
  } catch (err: any) {
    return {
      configured: false,
      connected: false,
      status: 'Error',
      message: err.message || 'Failed to query Cloudflare status',
    };
  }
};
