import React from 'react';
import {
  FileSpreadsheet,
  Layers,
  Settings as SettingsIcon,
  ShieldCheck,
  Scan
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab
}) => {
  const navItems = [
    { id: 'extraction', label: 'PDF Extraction', icon: FileSpreadsheet },
    { id: 'scanned', label: 'Scanned OCR Workspace', icon: Scan },
    { id: 'batch', label: 'Batch Processing', icon: Layers },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Logo & Brand Header */}
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

        {/* Navigation Menu */}
        <nav className="p-3 space-y-1 mt-2">
          <div className="px-3 pb-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Main Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200/60'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};
