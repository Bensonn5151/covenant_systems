import DashboardSidebar from "@/components/layout/DashboardSidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#050505] text-gray-300">
      <DashboardSidebar />
      <main className="ml-56 p-6">
        {children}
      </main>
    </div>
  );
}
