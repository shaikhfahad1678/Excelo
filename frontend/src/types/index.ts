export interface FileCard {
  id: string;
  filename: string;
  file_path: string;
  pdf_type: string;
  pages: number;
  file_size: string;
  status: 'Ready' | 'Extracting' | 'Completed' | 'Failed Validation' | 'Failed';
  extraction_method: string;
  progress: number;
  confidence_score: number;
  validation_status: 'Pending' | 'OK' | 'Warnings' | 'Errors';
  detect_msg?: string;
  uploaded_at: string;
  r2_uploaded?: boolean;
  r2_key?: string;
  cloudflare_status?: string;
  cloudflare_msg?: string;
}


export interface Transaction {
  'Sr No.'?: number;
  Date: string;
  Description: string;
  'Cheque No.'?: string;
  'Ref No.'?: string;
  Debit?: number | string;
  Credit?: number | string;
  Balance?: number | string;
  Currency?: string;
  'Validation Status'?: 'PASS' | 'LOW CONFIDENCE' | 'RECONSTRUCTED' | 'FAILED VALIDATION' | 'MISSING DATA' | 'DUPLICATE' | 'BALANCE MISMATCH' | string;
  Confidence?: string;
  [key: string]: any;
}

export interface Summary {
  total_count: number;
  pass_count: number;
  failed_count: number;
  duplicate_rows?: number;
  balance_mismatches?: number;
  opening_balance: number;
  closing_balance: number;
  total_debit: number;
  total_credit: number;
  incomplete_rate?: number;
  is_valid?: boolean;
}

export interface CandidateInfo {
  method: string;
  rows_found: number;
  pass_count?: number;
  failed_count?: number;
  is_valid?: boolean;
  score: number;
}

export interface Diagnostics {
  pdf_path: string;
  pdf_type?: string;
  attempted_methods?: string[];
  candidates: CandidateInfo[];
  selected_method: string;
  selection_reason: string;
  is_failsafe_triggered?: boolean;
}

export interface ExtractionResult {
  file_id: string;
  filename: string;
  pdf_type?: string;
  success: boolean;
  engine_used: string;
  processing_time: number;
  confidence_score: number;
  failsafe_warning?: string | null;
  transactions: Transaction[];
  summary: Summary;
  diagnostics?: Diagnostics;
  error?: string;
}




