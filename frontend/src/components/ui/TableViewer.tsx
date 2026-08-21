import React, { useState, useMemo } from 'react';
import {
  Search,
  ArrowUpDown,
  Download,
  Edit2,
  Check,
  ChevronLeft,
  ChevronRight,
  Plus,
  FileSpreadsheet
} from 'lucide-react';
import type { Transaction } from '../../types';

interface TableViewerProps {
  transactions: Transaction[];
  onUpdateTransactions?: (updated: Transaction[]) => void;
  highlightedRowIndex?: number | null;
  onExport?: (format: 'xlsx' | 'csv') => void;
}

export const TableViewer: React.FC<TableViewerProps> = ({
  transactions,
  onUpdateTransactions,
  highlightedRowIndex,
  onExport
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [selectedCell, setSelectedCell] = useState<{ row: number; colKey: string; colLetter: string } | null>({
    row: 0,
    colKey: 'Description',
    colLetter: 'C'
  });
  const [editingRowIndex, setEditingRowIndex] = useState<number | null>(null);
  const [editingRowData, setEditingRowData] = useState<Transaction | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  // Standard requested columns: Date, Description, Ledger, Debit, Credit, Balance
  const tableHeaders = useMemo(() => {
    return ['Date', 'Description', 'Ledger', 'Debit', 'Credit', 'Balance'];
  }, []);

  // Excel column letters helper
  const columnLetters: Record<string, string> = {
    'Sr No.': 'A',
    'Date': 'B',
    'Description': 'C',
    'Ledger': 'D',
    'Debit': 'E',
    'Credit': 'F',
    'Balance': 'G',
    'Validation Status': 'H'
  };

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 25;

  const filteredData = useMemo(() => {
    return transactions.filter((tx) => {
      const status = tx['Validation Status'] || 'PASS';

      if (filterStatus === 'PASS' && status !== 'PASS') return false;
      if (filterStatus === 'WARNINGS' && (status === 'PASS' || status === 'FAILED VALIDATION' || status === 'BALANCE MISMATCH')) return false;
      if (filterStatus === 'FAILED' && (status !== 'FAILED VALIDATION' && status !== 'BALANCE MISMATCH' && status !== 'MISSING DATA')) return false;

      if (!searchTerm) return true;
      const term = searchTerm.toLowerCase();
      return Object.entries(tx).some(([key, val]) => {
        if (key === 'Validation Status' || key === 'Currency') return false;
        return val !== undefined && val !== null && String(val).toLowerCase().includes(term);
      });
    });
  }, [transactions, searchTerm, filterStatus]);

  const sortedData = useMemo(() => {
    if (!sortField) return filteredData;
    return [...filteredData].sort((a, b) => {
      const valA = a[sortField] ?? '';
      const valB = b[sortField] ?? '';

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredData, sortField, sortAsc]);

  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage]);

  // Calculate quick summary metrics for Excel subtotal row and status bar
  const ledgerMetrics = useMemo(() => {
    let totalDebit = 0;
    let totalCredit = 0;
    let count = 0;
    transactions.forEach((tx) => {
      count++;
      const d = parseFloat(String(tx.Debit || 0));
      const c = parseFloat(String(tx.Credit || 0));
      if (!isNaN(d)) totalDebit += d;
      if (!isNaN(c)) totalCredit += c;
    });
    return {
      count,
      totalDebit,
      totalCredit,
      netSum: totalCredit - totalDebit
    };
  }, [transactions]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedRows(new Set(sortedData.map((_, i) => i)));
    } else {
      setSelectedRows(new Set());
    }
  };

  const toggleRowSelect = (index: number) => {
    const next = new Set(selectedRows);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setSelectedRows(next);
  };

  const startEditRow = (row: Transaction, realIndex: number) => {
    setEditingRowIndex(realIndex);
    setEditingRowData({ ...row });
  };

  const saveEditRow = () => {
    if (editingRowIndex !== null && editingRowData && onUpdateTransactions) {
      const updated = [...transactions];
      updated[editingRowIndex] = editingRowData;
      onUpdateTransactions(updated);
      setEditingRowIndex(null);
      setEditingRowData(null);
    }
  };

  // Get active cell value for formula bar
  const activeCellValue = useMemo(() => {
    if (!selectedCell) return '';
    const activeRow = sortedData[selectedCell.row];
    if (!activeRow) return '';
    if (selectedCell.colKey === 'Sr No.') return String(activeRow['Sr No.'] || selectedCell.row + 1);
    return String(activeRow[selectedCell.colKey] ?? '');
  }, [selectedCell, sortedData]);

  const activeCellCoord = selectedCell
    ? `${selectedCell.colLetter}${selectedCell.row + 3}`
    : 'A1';

  return (
    <div className="bg-white rounded-xl border border-neutral-300 shadow-md overflow-hidden flex flex-col font-sans select-none">
      {/* Streamlined Excel Formula & Action Bar */}
      <div className="bg-[#f8f9fa] border-b border-[#d2d0ce] p-2.5 flex flex-wrap items-center justify-between gap-3 shrink-0 text-xs">
        {/* Left: Formula Bar */}
        <div className="flex items-center gap-2 flex-1 min-w-[300px] max-w-xl">
          {/* Name Box (e.g. C3) */}
          <div className="w-14 px-2 py-1 bg-white border border-[#d2d0ce] rounded text-center font-mono font-bold text-neutral-800 text-xs shadow-2xs">
            {activeCellCoord}
          </div>

          {/* Function Icon */}
          <div className="flex items-center justify-center font-serif italic text-neutral-500 font-bold px-1 text-sm border-r border-[#d2d0ce] pr-2">
            fx
          </div>

          {/* Formula / Cell Content Display & Editor */}
          <div className="flex-1 bg-white border border-[#d2d0ce] rounded px-2.5 py-1 shadow-2xs">
            <input
              type="text"
              readOnly={editingRowIndex === null}
              value={editingRowIndex !== null && editingRowData && selectedCell ? (editingRowData[selectedCell.colKey] ?? '') : activeCellValue}
              onChange={(e) => {
                if (editingRowIndex !== null && selectedCell) {
                  setEditingRowData((prev) => prev ? { ...prev, [selectedCell.colKey]: e.target.value } : null);
                }
              }}
              placeholder="Click cell to view value"
              className="w-full font-mono text-xs text-neutral-900 bg-transparent focus:outline-none"
            />
          </div>
        </div>

        {/* Right: Search, Filter & Direct Excel Export Button */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-neutral-400" />
            <input
              type="text"
              placeholder="Filter sheet..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 pr-2.5 py-1 text-xs bg-white border border-[#d2d0ce] rounded-lg focus:outline-none focus:border-[#107c41] w-36 font-medium text-neutral-800 placeholder-neutral-400 shadow-2xs"
            />
          </div>

          <div className="flex items-center gap-1 bg-white border border-[#d2d0ce] rounded-lg p-0.5 text-xs shadow-2xs">
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`px-2 py-0.5 rounded font-medium text-[11px] ${filterStatus === 'ALL'
                  ? 'bg-[#107c41] text-white font-bold'
                  : 'text-neutral-600 hover:bg-neutral-100'
                }`}
            >
              All ({transactions.length})
            </button>
            <button
              onClick={() => setFilterStatus('PASS')}
              className={`px-2 py-0.5 rounded font-medium text-[11px] ${filterStatus === 'PASS'
                  ? 'bg-[#107c41] text-white font-bold'
                  : 'text-neutral-600 hover:bg-neutral-100'
                }`}
            >
              Pass
            </button>
            <button
              onClick={() => setFilterStatus('WARNINGS')}
              className={`px-2 py-0.5 rounded font-medium text-[11px] ${filterStatus === 'WARNINGS'
                  ? 'bg-amber-600 text-white font-bold'
                  : 'text-neutral-600 hover:bg-neutral-100'
                }`}
            >
              Review
            </button>
          </div>

          {onExport && (
            <button
              onClick={() => onExport('xlsx')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#107c41] text-white hover:bg-[#0e6b37] font-bold text-xs shadow-sm transition active:scale-95"
              title="Download Excel Workbook (.xlsx)"
            >
              <Download className="w-3.5 h-3.5 text-white" />
              Download Excel (.xlsx)
            </button>
          )}
        </div>
      </div>

      {/* Excel Spreadsheet Grid Table */}
      <div className="overflow-auto relative max-h-[600px] border-b border-[#e1dfdd] bg-white">
        <table className="w-full text-left border-collapse text-xs font-sans">
          {/* Top Sticky Header Section */}
          <thead className="sticky top-0 z-20 bg-[#f3f2f1] text-[#605e5c] select-none">
            {/* Top Column Letters Row (A, B, C, D, E, F, G) */}
            <tr className="border-b border-[#d2d0ce]">
              <th className="w-10 bg-[#e1dfdd] border-r border-b border-[#c8c6c4] text-center p-1 font-mono text-[10px] text-neutral-500">
                <input
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={selectedRows.size > 0 && selectedRows.size === sortedData.length}
                  className="rounded border-[#a19f9d] text-[#107c41] focus:ring-0 cursor-pointer"
                />
              </th>
              <th className="w-14 bg-[#f3f2f1] border-r border-[#d2d0ce] text-center p-1 font-mono text-[11px] font-bold text-neutral-600">
                A
              </th>
              {tableHeaders.map((header) => (
                <th
                  key={header}
                  className="bg-[#f3f2f1] border-r border-[#d2d0ce] text-center p-1 font-mono text-[11px] font-bold text-neutral-600"
                >
                  {columnLetters[header] || '-'}
                </th>
              ))}
              <th className="w-28 bg-[#f3f2f1] border-r border-[#d2d0ce] text-center p-1 font-mono text-[11px] font-bold text-neutral-600">
                {columnLetters['Validation Status'] || 'H'}
              </th>
              <th className="w-12 bg-[#f3f2f1] border-r border-[#d2d0ce] text-center p-1 font-mono text-[11px] font-bold text-neutral-600">
                Edit
              </th>
            </tr>

            {/* Subtotal Row (Row 1 above column headers): shows sub total debit and credit values */}
            <tr className="bg-[#f1f5f9] text-neutral-800 font-bold border-b border-[#cbd5e1] shadow-2xs text-[11px]">
              <th className="p-1.5 border-r border-[#cbd5e1] text-center bg-[#e2e8f0] text-neutral-500 font-mono text-[10px]">
                1
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
              {/* Above Debit: Sub Total Debit Value (RED) */}
              <th className="p-1.5 border-r border-[#cbd5e1] text-right font-mono font-bold text-red-600 bg-red-50/50">
                {ledgerMetrics.totalDebit > 0
                  ? ledgerMetrics.totalDebit.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : '-'}
              </th>
              {/* Above Credit: Sub Total Credit Value (GREEN) */}
              <th className="p-1.5 border-r border-[#cbd5e1] text-right font-mono font-bold text-emerald-600 bg-emerald-50/50">
                {ledgerMetrics.totalCredit > 0
                  ? ledgerMetrics.totalCredit.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : '-'}
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
              <th className="p-1.5 border-r border-[#cbd5e1] text-center font-mono text-neutral-400">
                -
              </th>
            </tr>

            {/* Column Titles Header Row with Filter Dropdowns */}
            <tr className="bg-[#1e293b] text-white font-bold border-b-2 border-neutral-900 shadow-2xs text-[11px]">
              <th className="p-2 border-r border-slate-600 text-center bg-slate-800 text-slate-400 font-mono text-[10px]">
                2
              </th>
              <th
                onClick={() => handleSort('Sr No.')}
                className="p-2 border-r border-slate-600 text-center cursor-pointer hover:bg-slate-700 transition whitespace-nowrap"
              >
                <div className="flex items-center justify-center gap-1">
                  <span>Sr No.</span>
                  <ArrowUpDown className="w-2.5 h-2.5 opacity-60" />
                </div>
              </th>
              {tableHeaders.map((header) => {
                const isNumeric = ['debit', 'credit', 'balance', 'qty', 'price', 'amount', 'total'].includes(header.toLowerCase());
                return (
                  <th
                    key={header}
                    onClick={() => handleSort(header)}
                    className={`p-2 border-r border-slate-600 cursor-pointer hover:bg-slate-700 transition whitespace-nowrap ${isNumeric ? 'text-right' : 'text-left'
                      }`}
                  >
                    <div className={`flex items-center gap-1 ${isNumeric ? 'justify-end' : 'justify-start'}`}>
                      <span>{header}</span>
                      <ArrowUpDown className="w-2.5 h-2.5 opacity-60" />
                    </div>
                  </th>
                );
              })}
              <th className="p-2 border-r border-slate-600 text-center whitespace-nowrap">
                Validation Status
              </th>
              <th className="p-2 border-r border-slate-600 text-center whitespace-nowrap">
                Action
              </th>
            </tr>
          </thead>

          {/* Excel Grid Body */}
          <tbody className="divide-y divide-[#e1dfdd] text-[11px] text-neutral-900 bg-white">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={tableHeaders.length + 4} className="p-12 text-center text-neutral-400 font-sans">
                  No matching transaction rows found in ledger sheet.
                </td>
              </tr>
            ) : (
              paginatedData.map((row, index) => {
                const globalIndex = (currentPage - 1) * pageSize + index;
                const isSelected = selectedRows.has(globalIndex);
                const isHighlighted = highlightedRowIndex === globalIndex;
                const status = row['Validation Status'] || 'PASS';
                const isFailed = status === 'FAILED VALIDATION' || status === 'BALANCE MISMATCH';
                const isEditing = editingRowIndex === globalIndex;
                const srNo = row['Sr No.'] || globalIndex + 1;
                const excelRowNum = globalIndex + 3; // Row 1 is subtotal, Row 2 is header

                return (
                  <tr
                    key={globalIndex}
                    id={`tx-row-${globalIndex}`}
                    className={`border-b border-[#e1dfdd] hover:bg-[#f3f9f4] transition-colors ${isHighlighted
                        ? 'bg-amber-100/90'
                        : isSelected
                          ? 'bg-[#e8f4ec]'
                          : isFailed
                            ? 'bg-rose-50/60'
                            : index % 2 === 0
                              ? 'bg-white'
                              : 'bg-[#fafafa]'
                      }`}
                  >
                    {/* Left Sticky Excel Row Number */}
                    <td className="p-1.5 text-center bg-[#f3f2f1] border-r border-[#d2d0ce] font-mono text-[11px] font-bold text-neutral-500 select-none">
                      <div className="flex items-center justify-center gap-1">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleRowSelect(globalIndex)}
                          className="rounded border-[#a19f9d] text-[#107c41] focus:ring-0"
                        />
                        <span>{excelRowNum}</span>
                      </div>
                    </td>

                    {/* Column A: Sr No. */}
                    <td
                      onClick={() => setSelectedCell({ row: globalIndex, colKey: 'Sr No.', colLetter: 'A' })}
                      className={`p-2 text-center border-r border-[#e1dfdd] font-mono font-medium relative ${selectedCell?.row === globalIndex && selectedCell?.colKey === 'Sr No.'
                          ? 'ring-2 ring-[#107c41] ring-inset bg-white z-10'
                          : ''
                        }`}
                    >
                      {srNo}
                      {selectedCell?.row === globalIndex && selectedCell?.colKey === 'Sr No.' && (
                        <div className="w-1.5 h-1.5 bg-[#107c41] absolute -bottom-0.5 -right-0.5 border border-white" />
                      )}
                    </td>

                    {/* Data Columns (B, C, D, E, F, G...) */}
                    {tableHeaders.map((header) => {
                      const val = row[header];
                      const colLetter = columnLetters[header] || 'B';
                      const isCellFocused = selectedCell?.row === globalIndex && selectedCell?.colKey === header;
                      const isDebit = header.toLowerCase() === 'debit';
                      const isCredit = header.toLowerCase() === 'credit';
                      const isBalance = header.toLowerCase() === 'balance';
                      const isLedger = header.toLowerCase() === 'ledger';
                      const isNumeric = ['debit', 'credit', 'balance', 'qty', 'price', 'amount', 'total'].includes(header.toLowerCase());
                      const isNumVal = typeof val === 'number' || (val !== undefined && val !== null && !isNaN(Number(val)) && val !== '' && !isNaN(parseFloat(val)));

                      let displayVal = String(val ?? '');
                      if (isNumVal && typeof val === 'number') {
                        displayVal = val.toLocaleString('en-IN', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        });
                      } else if (isNumVal && typeof val === 'string') {
                        const num = parseFloat(val);
                        if (!isNaN(num)) {
                          displayVal = num.toLocaleString('en-IN', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          });
                        }
                      }

                      if (header === 'Description') {
                        return (
                          <td
                            key={header}
                            onClick={() => setSelectedCell({ row: globalIndex, colKey: header, colLetter })}
                            className={`p-2 font-sans font-medium text-neutral-900 border-r border-[#e1dfdd] min-w-[260px] relative ${isCellFocused ? 'ring-2 ring-[#107c41] ring-inset bg-white z-10' : ''
                              }`}
                          >
                            {isEditing ? (
                              <textarea
                                value={editingRowData?.[header] || ''}
                                onChange={(e) =>
                                  setEditingRowData((prev) =>
                                    prev ? { ...prev, [header]: e.target.value } : null
                                  )
                                }
                                rows={2}
                                className="w-full px-1.5 py-0.5 bg-white border border-[#107c41] rounded text-xs focus:outline-none"
                              />
                            ) : (
                              val || '-'
                            )}
                            {isCellFocused && !isEditing && (
                              <div className="w-1.5 h-1.5 bg-[#107c41] absolute -bottom-0.5 -right-0.5 border border-white" />
                            )}
                          </td>
                        );
                      }

                      if (isLedger) {
                        return (
                          <td
                            key={header}
                            onClick={() => setSelectedCell({ row: globalIndex, colKey: header, colLetter })}
                            className={`p-2 text-left font-sans text-neutral-600 border-r border-[#e1dfdd] min-w-[140px] relative ${isCellFocused ? 'ring-2 ring-[#107c41] ring-inset bg-white z-10' : ''
                              }`}
                          >
                            {isEditing ? (
                              <input
                                type="text"
                                value={editingRowData?.[header] || ''}
                                placeholder="Enter Ledger Account"
                                onChange={(e) =>
                                  setEditingRowData((prev) =>
                                    prev ? { ...prev, [header]: e.target.value } : null
                                  )
                                }
                                className="px-1.5 py-0.5 bg-white border border-[#107c41] rounded text-xs w-full focus:outline-none"
                              />
                            ) : (
                              val || <span className="text-neutral-300 italic">Empty</span>
                            )}
                            {isCellFocused && !isEditing && (
                              <div className="w-1.5 h-1.5 bg-[#107c41] absolute -bottom-0.5 -right-0.5 border border-white" />
                            )}
                          </td>
                        );
                      }

                      return (
                        <td
                          key={header}
                          onClick={() => setSelectedCell({ row: globalIndex, colKey: header, colLetter })}
                          className={`p-2 whitespace-nowrap border-r border-[#e1dfdd] relative ${isNumeric || isNumVal ? 'text-right font-mono' : 'text-left'
                            } ${isCredit && isNumVal
                              ? 'text-emerald-600 font-bold bg-emerald-50/20'
                              : isDebit && isNumVal
                                ? 'text-red-600 font-bold bg-red-50/20'
                                : isBalance
                                  ? 'text-neutral-900 font-bold bg-neutral-50/40'
                                  : 'text-neutral-800'
                            } ${isCellFocused ? 'ring-2 ring-[#107c41] ring-inset bg-white z-10' : ''
                            }`}
                        >
                          {isEditing ? (
                            <input
                              type="text"
                              value={editingRowData?.[header] || ''}
                              onChange={(e) =>
                                setEditingRowData((prev) =>
                                  prev ? { ...prev, [header]: e.target.value } : null
                                )
                              }
                              className="px-1.5 py-0.5 bg-white border border-[#107c41] rounded text-xs w-full text-right focus:outline-none"
                            />
                          ) : (
                            displayVal || '-'
                          )}
                          {isCellFocused && !isEditing && (
                            <div className="w-1.5 h-1.5 bg-[#107c41] absolute -bottom-0.5 -right-0.5 border border-white" />
                          )}
                        </td>
                      );
                    })}

                    {/* Validation Status Column */}
                    <td className="p-2 text-center border-r border-[#e1dfdd] whitespace-nowrap">
                      {status === 'PASS' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                          <Check className="w-3 h-3 text-emerald-700" /> PASS
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
                          {status}
                        </span>
                      )}
                    </td>

                    {/* Edit Action Column */}
                    <td className="p-2 text-center border-r border-[#e1dfdd]">
                      {isEditing ? (
                        <button
                          onClick={saveEditRow}
                          className="p-1 bg-[#107c41] text-white rounded hover:bg-[#0e6b37]"
                          title="Save Changes"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <button
                          onClick={() => startEditRow(row, globalIndex)}
                          className="p-1 text-neutral-400 hover:text-[#107c41] rounded hover:bg-neutral-100"
                          title="Edit Row"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Excel Bottom Sheet Tab & Status Bar */}
      <div className="bg-[#f3f2f1] border-t border-[#d2d0ce] px-3 py-1.5 flex flex-wrap items-center justify-between gap-3 shrink-0 text-xs text-neutral-600 select-none">
        {/* Left: Excel Sheet Tabs */}
        <div className="flex items-center gap-1">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-white border-t-2 border-[#107c41] border-x border-[#d2d0ce] text-[#107c41] font-bold text-xs shadow-2xs rounded-t">
            <FileSpreadsheet className="w-3.5 h-3.5 text-[#107c41]" />
            <span>Sheet1 - Transactions</span>
          </div>
          <button
            className="p-1 text-neutral-500 hover:bg-neutral-200 rounded transition"
            title="Add New Worksheet"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Center: Excel Metrics Calculation Summary */}
        <div className="hidden lg:flex items-center gap-4 text-[11px] font-mono text-neutral-700 bg-white border border-[#d2d0ce] px-3 py-1 rounded">
          <span>
            <strong>Rows:</strong> {ledgerMetrics.count}
          </span>
          <span className="text-neutral-300">|</span>
          <span>
            <strong>Subtotal Debit:</strong> ₹{ledgerMetrics.totalDebit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-neutral-300">|</span>
          <span>
            <strong>Subtotal Credit:</strong> ₹{ledgerMetrics.totalCredit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-neutral-300">|</span>
          <span className="text-[#107c41] font-bold">
            <strong>Ready for Export</strong>
          </span>
        </div>

        {/* Right: Excel Pagination & Zoom Bar */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 font-medium text-[11px]">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-white border border-[#d2d0ce] disabled:opacity-40 hover:bg-neutral-100 font-semibold text-neutral-700"
            >
              <ChevronLeft className="w-3 h-3" /> Prev
            </button>
            <span className="font-mono px-1">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-white border border-[#d2d0ce] disabled:opacity-40 hover:bg-neutral-100 font-semibold text-neutral-700"
            >
              Next <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-4 w-[1px] bg-[#d2d0ce] mx-1" />

          <div className="text-[11px] font-mono font-semibold bg-white border border-[#d2d0ce] px-2 py-0.5 rounded text-neutral-700">
            100%
          </div>
        </div>
      </div>
    </div>
  );
};
