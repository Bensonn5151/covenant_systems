"use client";

import { TypeAnimation } from 'react-type-animation';
import { Terminal as TerminalIcon } from 'lucide-react';

export default function Terminal() {
  return (
    <div className="w-full max-w-3xl mx-auto overflow-hidden bg-black border border-gray-800 rounded-lg shadow-2xl shadow-green-900/20 font-mono text-sm md:text-base">
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-4 h-4 text-gray-500" />
          <span className="text-xs text-gray-500">covenant_ai_core — -zsh — 80x24</span>
        </div>
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/50" />
          <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
        </div>
      </div>

      {/* Terminal Body */}
      <div className="p-6 min-h-[200px] text-green-500">
        <TypeAnimation
          sequence={[
            '> CovenantAI initializing...',
            1000,
            '> CovenantAI initializing...\n> Connecting to Global Regulatory Feeds... [ONLINE]',
            800,
            '> CovenantAI initializing...\n> Connecting to Global Regulatory Feeds... [ONLINE]\n> Verifying Data Integrity Checksum... [PASSED]',
            800,
            '> CovenantAI initializing...\n> Connecting to Global Regulatory Feeds... [ONLINE]\n> Verifying Data Integrity Checksum... [PASSED]\n> Mapping Logic v3.0 Loaded... [OK]',
            800,
            '> CovenantAI initializing...\n> Connecting to Global Regulatory Feeds... [ONLINE]\n> Verifying Data Integrity Checksum... [PASSED]\n> Mapping Logic v3.0 Loaded... [OK]\n> SYSTEM: READY FOR ORCHESTRATION',
            1000
          ]}
          wrapper="span"
          cursor={true}
          repeat={0}
          style={{ whiteSpace: 'pre-line', display: 'block' }}
        />
      </div>
    </div>
  );
}
