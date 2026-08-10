# Excelo PRO — Enterprise Bank Statement Processing Suite

> **Automated PDF extraction, multi-engine scoring, arithmetic balance validation, and formatted Excel workbook generation.**

---

## Architecture

```
excelo/
├── backend/                  # Python FastAPI REST API
│   ├── api/
│   │   ├── main.py           # FastAPI application & REST endpoints
│   │   └── controller.py     # Legacy processing controller
│   ├── services/
│   │   └── statement_service.py  # Core orchestration service
│   ├── extractors/
│   │   ├── pipeline.py       # Multi-engine scoring pipeline
│   │   ├── candidate_extractors.py
│   │   ├── header_mapper.py
│   │   ├── normalizer.py
│   │   └── spatial_extractor.py
│   ├── validators/
│   │   └── bank_validator.py # Running balance arithmetic verification
│   ├── excel/
│   │   └── writer.py         # OpenPyXL workbook & CSV generator
│   ├── models/
│   │   └── transaction.py    # Transaction data model
│   ├── ocr/
│   │   └── engine.py         # OCR fallback stub (future expansion)
│   └── utils/
│       ├── logger.py
│       ├── pdf_detector.py
│       └── sample_generator.py
├── frontend/                 # React + TypeScript + Vite + TailwindCSS
│   ├── src/
│   │   ├── App.tsx           # Root application with state management
│   │   ├── components/
│   │   │   ├── layout/       # Sidebar, Navbar
│   │   │   ├── ui/           # TableViewer (Excel-like data grid)
│   │   │   └── views/        # Dashboard, PdfExtraction, Batch,
│   │   │                     # History, Logs, Settings, About
│   │   ├── services/api.ts   # Axios REST API client
│   │   └── types/index.ts    # TypeScript interfaces
│   └── vite.config.ts        # Vite + Tailwind + API proxy
├── main.py                   # FastAPI server entrypoint
└── requirements.txt
```

## Tech Stack

| Layer      | Technology                                                                 |
|------------|----------------------------------------------------------------------------|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, Lucide Icons, Axios             |
| **Backend**  | Python, FastAPI, Uvicorn                                                 |
| **Engines**  | Camelot (Lattice/Stream), pdfplumber (Tables/Spatial), Tabula            |
| **Output**   | OpenPyXL Excel workbooks, CSV export                                     |
| **Validation** | Arithmetic running balance verification with configurable tolerance    |

## REST API Endpoints

| Method | Endpoint             | Description                              |
|--------|----------------------|------------------------------------------|
| GET    | `/api/health`        | Backend health & engine status           |
| POST   | `/api/upload`        | Upload single or multiple PDF files      |
| POST   | `/api/sample`        | Generate synthetic sample bank statement |
| POST   | `/api/extract`       | Run multi-engine extraction pipeline     |
| POST   | `/api/validate`      | Re-validate transaction rows             |
| POST   | `/api/retry`         | Retry with a specific engine             |
| POST   | `/api/generate-excel`| Generate Excel/CSV export                |
| GET    | `/api/download/{fn}` | Download exported file                   |
| GET    | `/api/history`       | Extraction session history               |
| GET    | `/api/logs`          | System execution & audit logs            |
| GET    | `/api/settings`      | Current engine configuration             |
| POST   | `/api/settings`      | Update engine configuration              |

## Quick Start

### 1. Backend

```bash
pip install -r requirements.txt
python main.py
# Server starts on http://127.0.0.1:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Dev server starts on http://localhost:3000
```

### 3. Open the app

Navigate to **http://localhost:3000** in your browser.

## Design

- Light enterprise finance theme inspired by Stripe, QuickBooks, and Microsoft 365
- Clean white/light-gray backgrounds with soft blue accents
- Professional sidebar + navbar layout with real-time backend status
- Excel-like data table with sorting, filtering, search, pagination, and inline editing
- Validation panel with clickable error rows for jump-to-row navigation
- Multi-engine diagnostic report modal
- Toast notifications, progress indicators, and smooth transitions
