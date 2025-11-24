import { LucideIcon } from 'lucide-react';

interface ArchitectureCardProps {
  title: string;
  icon: LucideIcon;
  children: React.ReactNode;
}

export default function ArchitectureCard({ title, icon: Icon, children }: ArchitectureCardProps) {
  return (
    <div className="group relative p-6 bg-gray-900/50 border border-gray-800 rounded-lg hover:border-green-500/50 transition-all duration-300 hover:shadow-[0_0_20px_rgba(34,197,94,0.1)]">
      <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-100 transition-opacity">
        <Icon className="w-6 h-6 text-green-500" />
      </div>
      <div className="mb-4">
        <div className="w-10 h-10 flex items-center justify-center rounded bg-gray-800 group-hover:bg-green-900/20 transition-colors">
          <Icon className="w-5 h-5 text-gray-400 group-hover:text-green-400" />
        </div>
      </div>
      <h3 className="text-lg font-bold text-white mb-2 tracking-tight group-hover:text-green-400 transition-colors">
        {title}
      </h3>
      <p className="text-sm text-gray-400 leading-relaxed">
        {children}
      </p>
    </div>
  );
}
