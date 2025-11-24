'use client';

import {
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  FileText,
  Shield,
  Calendar,
  ArrowUpRight,
  Bell
} from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-[#050505] text-gray-300">
      {/* Navigation Bar */}
      <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="font-mono font-bold text-lg text-green-500">covenant<span className="text-white">AI</span></div>
            </div>

            {/* Nav Items */}
            <div className="hidden md:flex items-center gap-6 text-sm font-medium">
              <a href="#" className="text-green-500 border-b-2 border-green-500 pb-0.5">Overview</a>
              <a href="#" className="text-gray-400 hover:text-white transition">Regulatory Library</a>
              <a href="#" className="text-gray-400 hover:text-white transition">Mappings</a>
              <a href="#" className="text-gray-400 hover:text-white transition">Findings</a>
              <a href="#" className="text-gray-400 hover:text-white transition">Insights</a>
              <a href="#" className="text-gray-400 hover:text-white transition">Reports</a>
              <a href="#" className="text-gray-400 hover:text-white transition">Risk</a>
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-4">
              <button className="relative p-2 hover:bg-gray-800 rounded-lg transition">
                <Bell className="w-5 h-5 text-gray-400" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold">
                  SK
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Compliance Overview</h1>
          <p className="text-gray-400">Real-time compliance intelligence for Square Listings</p>
        </div>

        {/* Compliance Health Score - Hero */}
        <div className="mb-8 bg-gradient-to-br from-gray-900 to-gray-900/50 border border-gray-800 rounded-2xl p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="text-sm font-mono text-gray-500 mb-1">COMPLIANCE HEALTH SCORE</div>
              <div className="flex items-baseline gap-3">
                <span className="text-6xl font-bold text-white">95.2<span className="text-3xl text-gray-500">%</span></span>
                <div className="flex items-center gap-1 text-green-500 font-mono text-sm">
                  <TrendingUp className="w-4 h-4" />
                  <span>+2.3%</span>
                </div>
              </div>
              <p className="text-gray-400 text-sm mt-2">from last month</p>
            </div>

            {/* Score Visualization */}
            <div className="relative w-40 h-40">
              <svg className="transform -rotate-90 w-40 h-40">
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="transparent"
                  className="text-gray-800"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 70}`}
                  strokeDashoffset={`${2 * Math.PI * 70 * (1 - 0.952)}`}
                  className="text-green-500"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <CheckCircle2 className="w-12 h-12 text-green-500" />
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-black/30 rounded-lg p-4 border border-gray-800">
              <div className="text-2xl font-bold text-white mb-1">247</div>
              <div className="text-xs text-gray-400">Regulations Tracked</div>
            </div>
            <div className="bg-black/30 rounded-lg p-4 border border-gray-800">
              <div className="text-2xl font-bold text-amber-500 mb-1">8</div>
              <div className="text-xs text-gray-400">Open Findings</div>
            </div>
            <div className="bg-black/30 rounded-lg p-4 border border-gray-800">
              <div className="text-2xl font-bold text-white mb-1">12</div>
              <div className="text-xs text-gray-400">Reg Updates (Q4)</div>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

          {/* Priority Actions */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                Priority Actions
              </h2>
              <span className="text-xs font-mono text-gray-500">2 HIGH PRIORITY</span>
            </div>

            <div className="space-y-4">
              {/* High Priority Item 1 */}
              <div className="bg-black/40 border-l-4 border-red-500 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-mono rounded">HIGH</span>
                    <span className="text-xs text-gray-500">PCMLTFA §9.6</span>
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-white mb-2">
                  Update AML risk assessment program
                </h3>
                <p className="text-xs text-gray-400 mb-3">
                  Missing documentation requirements for risk assessments
                </p>
                <button className="text-xs font-mono text-green-500 hover:text-green-400 transition flex items-center gap-1">
                  View Details <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>

              {/* High Priority Item 2 */}
              <div className="bg-black/40 border-l-4 border-red-500 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-mono rounded">HIGH</span>
                    <span className="text-xs text-gray-500">OSFI B-13</span>
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-white mb-2">
                  Add cyber expertise to board
                </h3>
                <p className="text-xs text-gray-400 mb-3">
                  New requirement for board-level cybersecurity expertise
                </p>
                <button className="text-xs font-mono text-green-500 hover:text-green-400 transition flex items-center gap-1">
                  View Details <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>

              {/* View All Link */}
              <button className="w-full text-center text-sm text-gray-400 hover:text-white transition py-2 border border-gray-800 rounded-lg hover:border-gray-700">
                View All Findings →
              </button>
            </div>
          </div>

          {/* Recent Regulatory Updates */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-500" />
                Recent Regulatory Changes
              </h2>
            </div>

            <div className="space-y-4">
              {/* Update 1 */}
              <div className="pb-4 border-b border-gray-800">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-gray-500">NOV 15, 2025</span>
                      <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-mono rounded">HIGH IMPACT</span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mb-1">
                      OSFI B-13 Updated
                    </h3>
                    <p className="text-xs text-gray-400">
                      Technology & Cybersecurity Risk Management
                    </p>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-500 flex-shrink-0 ml-2" />
                </div>
              </div>

              {/* Update 2 */}
              <div className="pb-4 border-b border-gray-800">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-gray-500">NOV 10, 2025</span>
                      <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs font-mono rounded">MED IMPACT</span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mb-1">
                      PIPEDA Amendment
                    </h3>
                    <p className="text-xs text-gray-400">
                      Data Breach Notification Requirements
                    </p>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-500 flex-shrink-0 ml-2" />
                </div>
              </div>

              {/* Update 3 */}
              <div className="pb-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-gray-500">NOV 3, 2025</span>
                      <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs font-mono rounded">LOW IMPACT</span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mb-1">
                      Bank Act Clarification
                    </h3>
                    <p className="text-xs text-gray-400">
                      Capital Requirements - No Action Required
                    </p>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-500 flex-shrink-0 ml-2" />
                </div>
              </div>

              {/* View All Link */}
              <button className="w-full text-center text-sm text-gray-400 hover:text-white transition py-2 border border-gray-800 rounded-lg hover:border-gray-700">
                View All Updates →
              </button>
            </div>
          </div>
        </div>

        {/* Compliance by Domain */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-green-500" />
              Compliance by Domain
            </h2>
            <button className="text-xs font-mono text-gray-400 hover:text-white transition">
              View Details →
            </button>
          </div>

          <div className="space-y-4">
            {[
              { name: 'Anti-Money Laundering', percentage: 98, status: 'excellent' },
              { name: 'Know Your Customer', percentage: 92, status: 'good' },
              { name: 'Privacy & Data Protection', percentage: 97, status: 'excellent' },
              { name: 'Cybersecurity', percentage: 73, status: 'warning' },
              { name: 'Capital Requirements', percentage: 100, status: 'excellent' },
              { name: 'Consumer Protection', percentage: 89, status: 'good' },
            ].map((domain) => (
              <div key={domain.name}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-300">{domain.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono text-white">{domain.percentage}%</span>
                    {domain.status === 'excellent' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                    {domain.status === 'good' && <CheckCircle2 className="w-4 h-4 text-blue-500" />}
                    {domain.status === 'warning' && <AlertCircle className="w-4 h-4 text-amber-500" />}
                  </div>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      domain.status === 'excellent' ? 'bg-green-500' :
                      domain.status === 'good' ? 'bg-blue-500' :
                      'bg-amber-500'
                    }`}
                    style={{ width: `${domain.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="bg-gradient-to-r from-green-900/20 to-green-800/10 border border-green-900/50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white mb-1">Ready to improve your compliance posture?</h3>
              <p className="text-sm text-gray-400">Generate an executive report or explore detailed findings</p>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition border border-gray-700">
                View Findings
              </button>
              <button className="px-4 py-2 bg-green-500 hover:bg-green-400 text-black rounded-lg text-sm font-bold transition flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Generate Report
              </button>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}