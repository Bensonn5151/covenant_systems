import Terminal from '@/components/Terminal';
import ArchitectureCard from '@/components/ArchitectureCard';
import CTAForm from '@/components/CTAForm';
import { Database, Cpu, Network, ShieldCheck, Lock } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col bg-[#050505] text-gray-300 selection:bg-green-500/30 selection:text-green-200">

      {/* Background Grid Effect */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-[0.15]" />
      </div>

      {/* Hero Section */}
      <section className="relative z-10 flex flex-col items-center justify-center pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full text-center">
        <div className="mb-12 w-full">
          <Terminal />
        </div>

        <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-white mb-6 max-w-4xl mx-auto">
          Covenant Systems: The <span className="text-green-500">Operating System</span> for Regulation.
        </h1>

        <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
          Turn static regulatory noise into dynamic, auditable action.
        </p>

        <button className="group relative inline-flex items-center justify-center px-8 py-4 font-mono font-bold text-black transition-all duration-200 bg-green-500 rounded hover:bg-green-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 ring-offset-black">
          <span className="absolute inset-0 w-full h-full -mt-1 rounded opacity-30 bg-gradient-to-b from-transparent via-transparent to-black"></span>
          <span className="relative">EXECUTE_ACCESS()</span>
        </button>
      </section>

      {/* Architecture Section */}
      <section className="relative z-10 py-24 bg-black/50 border-y border-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Built for Scale. Engineered for Trust.
            </h2>
            <div className="h-1 w-20 bg-green-500 mx-auto rounded-full" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <ArchitectureCard title="Ingestion" icon={Database}>
              Automated pipelines ingest high-volume, multi-format regulatory data streams. Auditability from the source.
            </ArchitectureCard>

            <ArchitectureCard title="Intelligence Engine" icon={Cpu}>
              Proprietary mapping logic connects external requirements to internal controls, policies, and evidence nodes.
            </ArchitectureCard>

            <ArchitectureCard title="Orchestration" icon={Network}>
              Trigger automated workflows for documentation, escalation, and evidence gathering using auditable compliance flows.
            </ArchitectureCard>
          </div>
        </div>
      </section>

      {/* Enterprise Assurance Section */}
      <section className="relative z-10 py-24 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full">
        <div className="bg-gray-900/30 border border-gray-800 rounded-2xl p-8 md:p-12">
          <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-3 text-green-500 mb-2">
              <ShieldCheck className="w-6 h-6" />
              <span className="font-mono text-sm font-bold tracking-wider uppercase">System Integrity</span>
            </div>
            <h2 className="text-3xl font-bold text-white">
              Built for Regulatory Complexity
            </h2>
            <p className="text-gray-400 leading-relaxed text-lg">
              We've moved beyond keyword search and AI wrappers. Covenant Systems uses <span className="text-green-400 font-semibold">GraphRAG architecture</span>—combining Knowledge Graphs with LLMs to understand regulatory relationships, trace compliance impacts across jurisdictions, and surface hidden dependencies that traditional systems miss.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
              <div className="flex flex-col gap-1 p-3 bg-gray-900/50 border border-gray-800 rounded">
                <div className="flex items-center gap-2 text-sm text-green-500 font-mono font-bold">
                  <Network className="w-4 h-4" />
                  <span>Graph-Native Intelligence</span>
                </div>
                <span className="text-xs text-gray-500">Maps 10,000+ regulatory relationships</span>
              </div>
              <div className="flex flex-col gap-1 p-3 bg-gray-900/50 border border-gray-800 rounded">
                <div className="flex items-center gap-2 text-sm text-green-500 font-mono font-bold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Citation-Required Reasoning</span>
                </div>
                <span className="text-xs text-gray-500">Every answer traceable to source documents</span>
              </div>
              <div className="flex flex-col gap-1 p-3 bg-gray-900/50 border border-gray-800 rounded">
                <div className="flex items-center gap-2 text-sm text-green-500 font-mono font-bold">
                  <Lock className="w-4 h-4" />
                  <span>Zero Hallucination Tolerance</span>
                </div>
                <span className="text-xs text-gray-500">Confidence scoring on all AI outputs</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <footer className="relative z-10 py-20 border-t border-gray-900 bg-black">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-8">
            Join the Command Line.
          </h2>
          <CTAForm />
          <div className="mt-12 text-xs text-gray-600 font-mono">
            <p>© 2025 Covenant Systems. All systems operational.</p>
          </div>
        </div>
      </footer>
    </main>
  );
}
