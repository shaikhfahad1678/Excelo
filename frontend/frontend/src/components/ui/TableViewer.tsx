import React, { useState, useMemo } from 'react';
import {
  Search,
  ArrowUpDown,
  Download,
  Edit2,
  Check,
  ChevronLeft,
  ChevronRight
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
  const [editingRowIndex, setEditingRowIndex] = useState<number | null>(null);
  const [editingRowData, setEditingRowData] = useState<Transaction | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  // Dynamically calculate column headers from data keys
  const tableHeaders = useMemo(() => {
    if (transactions.length === 0) return [];
    
    const keys = new Set<string>();
    transactions.forEach((tx) => {
      Object.keys(tx).forEach((k) => {
        if (
          k !== 'Currency' && 
          k !== 'Validation Status' && 
          k !== 'Sr No.' && 
          k !== 'Sr. No.' && 
          k !== 'Sr No' && 
          k !== 'S.No.' && 
          k !== 'S.No' && 
          k !== 'Confidence' &&
          k !== 'Validation Details'
        ) {
          keys.add(k);
        }
      });
    });

    const stdKeys = ['Date', 'Description', 'Cheque No.', 'Ref No.', 'Debit', 'Credit', 'Balance'];
    const isStandard = Array.from(keys).every((k) => stdKeys.includes(k));

    if (isStandard) {
      return stdKeys.filter((k) => keys.has(k) || k === 'Cheque No.' || k === 'Ref No.');
    }
    
    return Array.from(keys);
  }, [transactions]);

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

  const renderStatusBadge = (status: string = 'PASS') => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200/60 font-sans">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> PASS
          </span>
        );
      case 'LOW CONFIDENCE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200/60 font-sans">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> REVIEW
          </span>
        );
      case 'BALANCE MISMATCH':
      case 'FAILED VALIDATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200/60 font-sans">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> MISMATCH
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-neutral-100 text-neutral-700 border border-neutral-200/60 font-sans">
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-400" /> {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden flex flex-col">
      {/* Search & Filter Toolbar */}
      <div className="p-3.5 border-b border-neutral-200/80 bg-neutral-50/50 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2.5 flex-1 min-w-[280px]">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-neutral-400" />
            <input
              type="text"
              placeholder="Filter Sr No., date, narration, amount..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-neutral-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-neutral-900 font-medium text-neutral-800 placeholder-neutral-400"
            />
          </div>

          <div className="flex items-center gap-1 bg-neutral-100/80 p-0.5 rounded-xl border border-neutral-200/60 text-xs">
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`px-2.5 py-1 rounded-lg font-semibold text-[11px] transition ${
                filterStatus === 'ALL'
                  ? 'bg-white text-neutral-900 shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-900'
              }`}
            >
              All ({transactions.length})
            </button>
            <button
              onClick={() => setFilterStatus('PASS')}
              className={`px-2.5 py-1 rounded-lg font-semibold text-[11px] transition ${
                filterStatus === 'PASS'
                  ? 'bg-white text-emerald-800 shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-900'
              }`}
            >
              Pass
            </button>
            <button
              onClick={() => setFilterStatus('WARNINGS')}
              className={`px-2.5 py-1 rounded-lg font-semibold text-[11px] transition ${
                filterStatus === 'WARNINGS'
                  ? 'bg-white text-amber-800 shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-900'
              }`}
            >
              Warnings
            </button>
            <button
              onClick={() => setFilterStatus('FAILED')}
              className={`px-2.5 py-1 rounded-lg font-semibold text-[11px] transition ${
                filterStatus === 'FAILED'
                  ? 'bg-white text-rose-800 shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-900'
              }`}
            >
              Failed
            </button>
          </div>
        </div>

        {/* Minimalist Export Action Buttons */}
        {onExport && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onExport('xlsx')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-neutral-900 text-white hover:bg-neutral-800 font-bold text-xs transition shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              Download Excel (.xlsx)
            </button>
            <button
              onClick={() => onExport('csv')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-neutral-200 text-neutral-700 hover:bg-neutral-50 font-bold text-xs transition"
            >
              <Download className="w-3.5 h-3.5" />
              CSV
            </button>
          </div>
        )}
      </div>

      {/* Ledger Table */}
      <div className="overflow-x-auto relative">
        <table className="w-full text-left border-collapse text-xs">
          <thead className="bg-neutral-50 text-neutral-600 font-semibold border-b border-neutral-200 sticky top-0 z-10">
            <tr>
              <th className="p-3 w-10 text-center">
                <input
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={
                    selectedRows.size > 0 && selectedRows.size === sortedData.length
                  }
                  className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
                />
              </th>
              <th
                onClick={() => handleSort('Sr No.')}
                className="p-3 w-14 text-center cursor-pointer hover:bg-neutral-100/70 whitespace-nowrap"
              >
                <div className="flex items-center justify-center gap-1">
                  #
                  <ArrowUpDown className="w-3 h-3 text-neutral-400" />
                </div>
              </th>
              {tableHeaders.map((header) => {
                const isNumeric = ['debit', 'credit', 'balance', 'qty', 'price', 'amount', 'total'].includes(header.toLowerCase());
                return (
                  <th
                    key={header}
                    onClick={() => handleSort(header)}
                    className={`p-3 cursor-pointer hover:bg-neutral-100/70 transition whitespace-nowrap ${
                      isNumeric ? 'text-right' : 'text-left'
                    }`}
                  >
                    <div className={`flex items-center gap-1 ${isNumeric ? 'justify-end' : 'justify-start'}`}>
                      {header}
                      <ArrowUpDown className="w-3 h-3 text-neutral-400" />
                    </div>
                  </th>
                );
              })}
              <th className="p-3 text-center whitespace-nowrap">Audit Status</th>
              <th className="p-3 text-center w-12">Edit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100 font-mono text-[11px] text-neutral-800">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={12} className="p-10 text-center text-neutral-400 font-sans">
                  No matching transaction rows found.
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

                return (
                  <tr
                    key={globalIndex}
                    id={`tx-row-${globalIndex}`}
                    className={`transition-colors ${
                      isHighlighted
                        ? 'bg-amber-50 ring-1 ring-amber-300'
                        : isSelected
                        ? 'bg-neutral-100/80'
                        : isFailed
                        ? 'bg-rose-50/50 hover:bg-rose-50'
                        : index % 2 === 0
                        ? 'bg-white hover:bg-neutral-50/70'
                        : 'bg-neutral-50/30 hover:bg-neutral-50/70'
                    }`}
                  >
                    <td className="p-2.5 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleRowSelect(globalIndex)}
                        className="rounded border-neutral-300 text-neutral-900 focus:ring-0"
                      />
                    </td>
                    <td className="p-2.5 text-neutral-400 text-center font-mono font-medium">
                      {srNo}
                    </td>

                    {tableHeaders.map((header) => {
                      const val = row[header];
                      const isDebit = header.toLowerCase() === 'debit';
                      const isCredit = header.toLowerCase() === 'credit';
                      const isBalance = header.toLowerCase() === 'balance';
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
                          <td key={header} className="p-2.5 font-sans font-medium text-neutral-900 leading-relaxed min-w-[240px]">
                            {isEditing ? (
                              <textarea
                                value={editingRowData?.[header] || ''}
                                onChange={(e) =>
                                  setEditingRowData((prev) =>
                                    prev ? { ...prev, [header]: e.target.value } : null
                                  )
                                }
                                rows={2}
                                className="w-full px-2 py-1 bg-white border border-neutral-300 rounded-lg text-xs"
                              />
                            ) : (
                              val || '-'
                            )}
                          </td>
                        );
                      }

                      return (
                        <td
                          key={header}
                          className={`p-2.5 whitespace-nowrap ${
                            isNumeric || isNumVal
                              ? 'text-right font-mono'
                              : 'text-left'
                          } ${
                            isCredit && isNumVal
                              ? 'text-emerald-600 font-semibold'
                              : isDebit && isNumVal
                              ? 'text-neutral-900 font-medium'
                              : isBalance
                              ? 'text-neutral-900 font-bold'
                              : 'text-neutral-700'
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
                              className="px-2 py-1 bg-white border border-neutral-300 rounded-lg text-xs w-full text-right"
                            />
                          ) : (
                            displayVal || '-'
                          )}
                        </td>
                      );
                    })}
                    <td className="p-2.5 text-center whitespace-nowrap">
                      {renderStatusBadge(status)}
                    </td>

                    <td className="p-2.5 text-center font-sans">
                      {isEditing ? (
                        <button
                          onClick={saveEditRow}
                          className="p-1 bg-neutral-900 text-white rounded hover:bg-neutral-800"
                          title="Save Changes"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <button
                          onClick={() => startEditRow(row, globalIndex)}
                          className="p-1 text-neutral-400 hover:text-neutral-900 rounded hover:bg-neutral-100"
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

      {/* Minimalist Pagination Bar */}
      <div className="p-3 border-t border-neutral-200/80 bg-neutral-50/50 flex items-center justify-between text-xs text-neutral-500 shrink-0 font-medium">
        <div>
          Showing {paginatedData.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length}{' '}
          entries
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-neutral-200 disabled:opacity-40 hover:bg-neutral-100 font-semibold text-neutral-700"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Prev
          </button>
          <span className="font-mono text-neutral-700">
            {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-neutral-200 disabled:opacity-40 hover:bg-neutral-100 font-semibold text-neutral-700"
          >
            Next <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
