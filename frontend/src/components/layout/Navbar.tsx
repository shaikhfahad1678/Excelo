import React from 'react';
import { RefreshCw } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  processingCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  processingCount = 0
}) => {
  const getTitle = () => {
    switch (activeTab) {
      case 'extraction':
        return 'PDF Bank Statement Extraction Workspace';
      default:
        return 'Excelo Financial Software';
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">
          {getTitle()}
        </h1>

        {processingCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-xs font-medium animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            Processing {processingCount} statement{processingCount > 1 ? 's' : ''}...
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5 pl-1">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs">
            FA
          </div>
          <div className="text-left hidden sm:block">
            <div className="text-xs font-semibold text-slate-800 leading-tight">Financial Auditor</div>
            <div className="text-[10px] text-slate-400 font-medium">Enterprise Admin</div>
          </div>
        </div>
      </div>
    </header>
  );
};
