import React from 'react';
import { FileSpreadsheet, ShieldCheck } from 'lucide-react';

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 select-none">
      <div>
        <div className="h-16 flex items-center px-6 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-slate-900 leading-tight text-base flex items-center gap-1.5">
                EXCELO <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-1.5 py-0.5 rounded">PRO</span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">Enterprise Finance Suite</p>
            </div>
          </div>
        </div>
        <nav className="p-3">
          <div className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-blue-50 text-blue-700 font-semibold text-xs border border-blue-100">
            <FileSpreadsheet className="w-4 h-4" />
            <span>PDF Statement Studio</span>
          </div>
        </nav>
      </div>
    </aside>
  );
};
