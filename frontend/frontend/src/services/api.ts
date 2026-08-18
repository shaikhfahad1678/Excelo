import axios from 'axios';
import type {
  FileCard,
  ExtractionResult,
  ProcessLog,
  HistoryItem,
  Settings,
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

export const generateSamplePdf = async (): Promise<FileCard> => {
  const res = await api.post('/sample');
  return res.data.file;
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
): Promise<{ download_url: string; filename: string }> => {
  const res = await api.post('/generate-excel', {
    file_ids: fileIds,
    format,
  });
  return res.data;
};

export const fetchLogs = async (): Promise<ProcessLog[]> => {
  const res = await api.get('/logs');
  return res.data.logs;
};

export const fetchHistory = async (): Promise<HistoryItem[]> => {
  const res = await api.get('/history');
  return res.data.history;
};

export const fetchSettings = async (): Promise<Settings> => {
  const res = await api.get('/settings');
  return res.data.settings;
};

export const updateSettings = async (settings: Settings): Promise<Settings> => {
  const res = await api.post('/settings', settings);
  return res.data.settings;
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

