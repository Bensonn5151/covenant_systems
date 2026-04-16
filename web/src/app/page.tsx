import Link from 'next/link';
import {
  ShieldCheck,
  Upload,
  Brain,
  BarChart3,
  CheckCircle,
  ArrowRight,
  Scale,
  Zap,
  Eye,
  Lock,
} from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-[#050505] text-gray-300 selection:bg-green-500/30 selection:text-green-200">

      {/* Background Grid */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-[0.15]" />
      </div>

      {/* Nav */}
      <nav className="relative z-20 flex items-center justify-between px-6 lg:px-8 py-4 border-b border-gray-900">
        <Link href="/" className="flex items-center gap-2 text-white font-bold hover:text-green-400 transition-colors">
          <ShieldCheck className="w-5 h-5 text-green-500" />
          <span>Covenant Systems</span>
        </Link>
        <div className="flex items-center gap-2 sm:gap-6">
          <Link href="/sign-in" className="text-sm text-gray-400 hover:text-white transition-colors">
            Sign in
          </Link>
          <Link href="/sign-up" className="px-4 py-2 bg-green-500 text-black text-sm font-mono font-bold rounded hover:bg-green-400 transition-colors">
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-mono mb-8">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          9 regulations | 129 obligations | LLM-powered analysis
        </div>

        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tighter text-white mb-6 max-w-4xl mx-auto leading-[1.05]">
          Find compliance gaps in your policies.{' '}
          <span className="text-green-500">Before regulators do.</span>
        </h1>

        <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
          Upload your privacy policy. Our AI reads it against 9 Canadian privacy regulations and tells you exactly where you&apos;re exposed — with evidence and reasoning for every obligation.
        </p>

        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-2 px-6 py-3.5 bg-green-500 text-black font-mono font-bold text-sm rounded-lg hover:bg-green-400 transition-all"
          >
            Analyze a policy <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/sign-up"
            className="inline-flex items-center gap-2 px-6 py-3.5 border border-gray-700 text-gray-300 font-mono text-sm rounded-lg hover:border-gray-500 hover:text-white transition-all"
          >
            Create free account
          </Link>
        </div>

        <div className="mt-16 text-xs text-gray-600 font-mono">
          Open source
        </div>
      </section>

      {/* How It Works */}
      <section className="relative z-10 py-20 border-y border-gray-900 bg-black/40">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <span className="text-xs text-green-500 font-mono uppercase tracking-wider">How it works</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              Three steps to compliance clarity
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Step
              num="01"
              icon={Upload}
              title="Upload your policy"
              desc="Drop a PDF or text file of your company's privacy policy. We parse it into structured sections automatically."
            />
            <Step
              num="02"
              icon={Brain}
              title="AI reads both documents"
              desc="Our LLM reads every obligation in 9 regulations alongside your policy and determines: covered, partial, or gap — with reasoning."
            />
            <Step
              num="03"
              icon={BarChart3}
              title="See your risk heatmap"
              desc="A visual grid shows your exposure across 8 operational areas and 9 regulations. Click any cell to see exactly which obligations are unmet."
            />
          </div>
        </div>
      </section>

      {/* Demo Stats */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <DemoCard
            company="Apex Financial Group"
            score={62.5}
            color="amber"
            label="Partial coverage"
            note="Strong on data use and retention, gaps in breach notification and accountability"
          />
          <DemoCard
            company="NorthStar Banking"
            score={18.3}
            color="red"
            label="Significant gaps"
            note="Missing consent mechanisms, weak on cross-border data disclosure"
          />
          <DemoCard
            company="QuickLend Inc."
            score={1.6}
            color="red"
            label="Critical exposure"
            note="Policy addresses almost none of the 61 PIPEDA obligations"
          />
        </div>
        <p className="text-center text-xs text-gray-600 font-mono mt-6">
          Real results from LLM analysis of 3 sample policies against 9 Canadian privacy regulations
        </p>
      </section>

      {/* Tech */}
      <section className="relative z-10 py-20 border-y border-gray-900 bg-black/40">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <span className="text-xs text-green-500 font-mono uppercase tracking-wider">Built on real infrastructure</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              Not another AI wrapper
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Feature
              icon={Scale}
              title="9 regulations ingested"
              desc="PIPEDA, Privacy Act, 2 SOR regulations, and 5 OPC guidance documents — 509 sections classified"
            />
            <Feature
              icon={Brain}
              title="LLM-powered reasoning"
              desc="Every verdict comes with evidence: which policy clause was matched, and why the LLM considers it covered or not"
            />
            <Feature
              icon={Eye}
              title="Risk heatmap"
              desc="8 operational areas x 9 regulations. Color-coded by residual risk. Click any cell to drill into the gaps"
            />
            <Feature
              icon={Lock}
              title="Auditable"
              desc="Every gap cites the regulation section. Every match quotes the policy clause. No black-box scores"
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-24 px-6 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Stop guessing about compliance.
        </h2>
        <p className="text-gray-400 mb-8 max-w-xl mx-auto">
          Get an honest, evidence-backed breakdown of where your policy stands against Canadian privacy law.
        </p>
        <Link
          href="/dashboard"
          className="group inline-flex items-center gap-2 px-8 py-4 bg-green-500 text-black font-mono font-bold rounded-lg hover:bg-green-400 transition-all"
        >
          Run your first analysis
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-900 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-gray-600 text-xs font-mono">
            <ShieldCheck className="w-4 h-4 text-green-500" />
            Covenant Systems © 2026
          </div>
          <div className="flex gap-6 text-xs text-gray-600 font-mono">
            <Link href="/dashboard" className="hover:text-green-500 transition-colors">Dashboard</Link>
            <Link href="/sign-in" className="hover:text-green-500 transition-colors">Sign in</Link>
            <a href="https://github.com/Bensonn5151/covenant_systems" target="_blank" rel="noreferrer" className="hover:text-green-500 transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </main>
  );
}

function Step({ num, icon: Icon, title, desc }: { num: string; icon: typeof Upload; title: string; desc: string }) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6 hover:border-green-500/30 transition-colors">
      <div className="flex items-center justify-between mb-5">
        <div className="w-10 h-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center">
          <Icon className="w-5 h-5 text-green-400" />
        </div>
        <span className="text-xs font-mono text-gray-700">{num}</span>
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
    </div>
  );
}

function DemoCard({ company, score, color, label, note }: { company: string; score: number; color: 'green' | 'amber' | 'red'; label: string; note: string }) {
  const colors = {
    green: 'text-green-400 border-green-500/30 bg-green-500/5',
    amber: 'text-amber-400 border-amber-500/30 bg-amber-500/5',
    red: 'text-red-400 border-red-500/30 bg-red-500/5',
  };
  return (
    <div className={`rounded-xl p-6 border ${colors[color]}`}>
      <div className="text-xs font-mono uppercase opacity-70 mb-2">{label}</div>
      <div className="flex items-baseline gap-2 mb-3">
        <span className={`text-4xl font-bold ${colors[color].split(' ')[0]}`}>{score}%</span>
        <span className="text-xs text-gray-500">coverage</span>
      </div>
      <div className="text-sm font-medium text-white mb-1">{company}</div>
      <div className="text-xs text-gray-500">{note}</div>
    </div>
  );
}

function Feature({ icon: Icon, title, desc }: { icon: typeof Upload; title: string; desc: string }) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-5">
      <Icon className="w-5 h-5 text-green-500 mb-3" />
      <h3 className="text-sm font-bold text-white mb-1">{title}</h3>
      <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
    </div>
  );
}
