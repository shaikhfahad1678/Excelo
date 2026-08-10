import React, { useState, useMemo } from 'react';
import {
  Search,
  ArrowUpDown,
  Download,
  Filter,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Copy,
  FileCheck,
  Edit2,
  Check
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
      return (
        (tx['Sr No.'] && String(tx['Sr No.']).includes(term)) ||
        (tx.Date && tx.Date.toLowerCase().includes(term)) ||
        (tx.Description && tx.Description.toLowerCase().includes(term)) ||
        (tx['Cheque No.'] && String(tx['Cheque No.']).toLowerCase().includes(term)) ||
        (tx['Ref No.'] && String(tx['Ref No.']).toLowerCase().includes(term)) ||
        (tx.Debit && String(tx.Debit).toLowerCase().includes(term)) ||
        (tx.Credit && String(tx.Credit).toLowerCase().includes(term)) ||
        (tx.Balance && String(tx.Balance).toLowerCase().includes(term)) ||
        (status && status.toLowerCase().includes(term))
      );
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
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3 h-3 text-emerald-600" /> PASS
          </span>
        );
      case 'LOW CONFIDENCE':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" /> LOW CONFIDENCE
          </span>
        );
      case 'RECONSTRUCTED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
            <FileCheck className="w-3 h-3 text-blue-600" /> RECONSTRUCTED
          </span>
        );
      case 'DUPLICATE':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300">
            <Copy className="w-3 h-3 text-slate-500" /> DUPLICATE
          </span>
        );
      case 'BALANCE MISMATCH':
      case 'FAILED VALIDATION':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" /> {status}
          </span>
        );
      case 'MISSING DATA':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-200">
            <AlertTriangle className="w-3 h-3 text-orange-600" /> MISSING DATA
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3 h-3 text-emerald-600" /> {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search Sr No., date, description, amounts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium text-slate-800"
            />
          </div>

          <div className="flex items-center gap-1 bg-white border border-slate-300 rounded-lg p-1 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1" />
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`px-2 py-0.5 rounded font-medium ${
                filterStatus === 'ALL'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              All ({transactions.length})
            </button>
            <button
              onClick={() => setFilterStatus('PASS')}
              className={`px-2 py-0.5 rounded font-medium ${
                filterStatus === 'PASS'
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Pass
            </button>
            <button
              onClick={() => setFilterStatus('WARNINGS')}
              className={`px-2 py-0.5 rounded font-medium ${
                filterStatus === 'WARNINGS'
                  ? 'bg-amber-100 text-amber-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Reconstructed / Low Conf
            </button>
            <button
              onClick={() => setFilterStatus('FAILED')}
              className={`px-2 py-0.5 rounded font-medium ${
                filterStatus === 'FAILED'
                  ? 'bg-rose-100 text-rose-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Failed / Mismatch
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onExport && (
            <>
              <button
                onClick={() => onExport('xlsx')}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-bold text-xs transition"
              >
                <Download className="w-3.5 h-3.5" />
                Export Excel (.xlsx)
              </button>
              <button
                onClick={() => onExport('csv')}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 text-white hover:bg-slate-900 font-bold text-xs transition"
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto relative">
        <table className="w-full text-left border-collapse text-xs">
          <thead className="bg-slate-100/90 text-slate-700 font-semibold sticky top-0 z-10 border-b border-slate-200">
            <tr>
              <th className="p-3 w-10 text-center">
                <input
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={
                    selectedRows.size > 0 && selectedRows.size === sortedData.length
                  }
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th
                onClick={() => handleSort('Sr No.')}
                className="p-3 w-14 text-center cursor-pointer hover:bg-slate-200/60 whitespace-nowrap"
              >
                <div className="flex items-center justify-center gap-1">
                  Sr No.
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                onClick={() => handleSort('Date')}
                className="p-3 cursor-pointer hover:bg-slate-200/60 transition whitespace-nowrap"
              >
                <div className="flex items-center gap-1">
                  Date
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                onClick={() => handleSort('Description')}
                className="p-3 cursor-pointer hover:bg-slate-200/60 transition min-w-[220px]"
              >
                <div className="flex items-center gap-1">
                  Description
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="p-3 whitespace-nowrap">Cheque No.</th>
              <th
                onClick={() => handleSort('Debit')}
                className="p-3 cursor-pointer hover:bg-slate-200/60 transition text-right whitespace-nowrap"
              >
                <div className="flex items-center justify-end gap-1">
                  Debit
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                onClick={() => handleSort('Credit')}
                className="p-3 cursor-pointer hover:bg-slate-200/60 transition text-right whitespace-nowrap"
              >
                <div className="flex items-center justify-end gap-1">
                  Credit
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                onClick={() => handleSort('Balance')}
                className="p-3 cursor-pointer hover:bg-slate-200/60 transition text-right whitespace-nowrap"
              >
                <div className="flex items-center justify-end gap-1">
                  Balance
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="p-3 text-center whitespace-nowrap">Validation Status</th>
              <th className="p-3 text-center w-16">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-800">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={10} className="p-8 text-center text-slate-400 font-sans">
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
                        ? 'bg-amber-100/90 ring-2 ring-amber-400 z-10'
                        : isSelected
                        ? 'bg-blue-50/70'
                        : isFailed
                        ? 'bg-rose-50/60 hover:bg-rose-100/60'
                        : status === 'LOW CONFIDENCE'
                        ? 'bg-amber-50/50 hover:bg-amber-100/50'
                        : index % 2 === 0
                        ? 'bg-white hover:bg-slate-50'
                        : 'bg-slate-50/40 hover:bg-slate-100/50'
                    }`}
                  >
                    <td className="p-2.5 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleRowSelect(globalIndex)}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="p-2.5 text-slate-500 font-bold text-center font-mono">
                      {srNo}
                    </td>

                    <td className="p-2.5 whitespace-nowrap">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editingRowData?.Date || ''}
                          onChange={(e) =>
                            setEditingRowData((prev) =>
                              prev ? { ...prev, Date: e.target.value } : null
                            )
                          }
                          className="w-full px-1.5 py-0.5 bg-white border border-blue-400 rounded text-xs"
                        />
                      ) : (
                        row.Date || '-'
                      )}
                    </td>

                    <td className="p-2.5 font-sans font-medium text-slate-900 leading-snug">
                      {isEditing ? (
                        <textarea
                          value={editingRowData?.Description || ''}
                          onChange={(e) =>
                            setEditingRowData((prev) =>
                              prev ? { ...prev, Description: e.target.value } : null
                            )
                          }
                          rows={2}
                          className="w-full px-1.5 py-0.5 bg-white border border-blue-400 rounded text-xs"
                        />
                      ) : (
                        row.Description || '-'
                      )}
                    </td>

                    <td className="p-2.5 text-slate-500 whitespace-nowrap">
                      {row['Cheque No.'] || '-'}
                    </td>

                    <td className="p-2.5 text-right text-rose-700 font-semibold whitespace-nowrap">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editingRowData?.Debit || ''}
                          onChange={(e) =>
                            setEditingRowData((prev) =>
                              prev ? { ...prev, Debit: e.target.value } : null
                            )
                          }
                          className="w-20 text-right px-1 py-0.5 bg-white border border-blue-400 rounded text-xs"
                        />
                      ) : row.Debit ? (
                        Number(row.Debit).toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                        })
                      ) : (
                        '-'
                      )}
                    </td>

                    <td className="p-2.5 text-right text-emerald-700 font-semibold whitespace-nowrap">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editingRowData?.Credit || ''}
                          onChange={(e) =>
                            setEditingRowData((prev) =>
                              prev ? { ...prev, Credit: e.target.value } : null
                            )
                          }
                          className="w-20 text-right px-1 py-0.5 bg-white border border-blue-400 rounded text-xs"
                        />
                      ) : row.Credit ? (
                        Number(row.Credit).toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                        })
                      ) : (
                        '-'
                      )}
                    </td>

                    <td className="p-2.5 text-right font-bold text-slate-900 whitespace-nowrap">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editingRowData?.Balance || ''}
                          onChange={(e) =>
                            setEditingRowData((prev) =>
                              prev ? { ...prev, Balance: e.target.value } : null
                            )
                          }
                          className="w-24 text-right px-1 py-0.5 bg-white border border-blue-400 rounded text-xs"
                        />
                      ) : row.Balance ? (
                        Number(row.Balance).toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                        })
                      ) : (
                        '-'
                      )}
                    </td>

                    <td className="p-2.5 text-center font-sans whitespace-nowrap">
                      {renderStatusBadge(status)}
                    </td>

                    <td className="p-2.5 text-center font-sans">
                      {isEditing ? (
                        <button
                          onClick={saveEditRow}
                          className="p-1 bg-emerald-600 text-white rounded hover:bg-emerald-700"
                          title="Save Changes"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <button
                          onClick={() => startEditRow(row, globalIndex)}
                          className="p-1 text-slate-400 hover:text-blue-600 rounded hover:bg-slate-100"
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

      <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600 shrink-0 font-medium">
        <div>
          Showing {paginatedData.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length}{' '}
          entries
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-2.5 py-1 rounded bg-white border border-slate-300 disabled:opacity-40 hover:bg-slate-100 font-semibold"
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-2.5 py-1 rounded bg-white border border-slate-300 disabled:opacity-40 hover:bg-slate-100 font-semibold"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
