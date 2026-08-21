import React from 'react';

interface NavbarProps {
  processingCount?: number;
  isBackendConnected?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  processingCount = 0
}) => {
  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 backdrop-blur-md border-b border-neutral-200/80 px-6 py-3.5 transition-all">
      <div className="max-w-[1700px] mx-auto flex items-center justify-between gap-4">
        {/* Brand & Studio Logo */}
        <div className="flex items-center gap-3.5">
          <div className="w-8 h-8 rounded-lg bg-neutral-900 text-white flex items-center justify-center font-bold text-sm tracking-tighter shadow-sm">
            E
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-tight text-neutral-900">
                EXCELO
              </span>
              <span className="text-[10px] font-mono font-bold bg-neutral-100 text-neutral-600 px-1.5 py-0.5 rounded border border-neutral-200/60">
                v2.6
              </span>
            </div>
            <p className="text-[10px] text-neutral-400 font-medium">Bank Statement Conversion Engine</p>
          </div>
        </div>

        {/* Right Status & Meta Indicators */}
        <div className="flex items-center gap-3">
          {processingCount > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200/80 text-amber-800 text-xs font-semibold animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
              <span>Processing {processingCount} statement{processingCount > 1 ? 's' : ''}...</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-neutral-100 border border-neutral-200/80 flex items-center justify-center font-bold text-[11px] text-neutral-700">
              FA
            </div>
            <div className="hidden lg:block text-left">
              <div className="text-xs font-bold text-neutral-900 leading-tight">Auditor Mode</div>
              <div className="text-[10px] text-neutral-400 font-medium">100% Math Verification</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
