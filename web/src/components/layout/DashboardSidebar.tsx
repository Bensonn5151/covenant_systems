"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import { Shield, ShieldCheck } from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Compliance Analysis", icon: Shield },
];

export default function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-56 bg-[#0a0a0a] border-r border-gray-800 flex flex-col z-40">
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-2 text-green-500 font-mono text-sm font-bold">
          <ShieldCheck className="w-4 h-4" />
          Covenant Systems
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-green-500/10 text-green-400 border border-green-500/20"
                  : "text-gray-400 hover:text-white hover:bg-gray-800/50"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800 flex items-center justify-between">
        <div className="text-xs text-gray-600 font-mono">v0.4.0</div>
        <UserButton
          appearance={{
            elements: {
              avatarBox: "w-7 h-7",
            },
          }}
        />
      </div>
    </aside>
  );
}
