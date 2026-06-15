"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShieldCheck, LayoutDashboard, FileSearch, AlertTriangle,
  FileText, Clock, Upload, LogOut, User, Bell,
  ArrowRightLeft, Monitor, FileSpreadsheet, ChevronRight, Settings
} from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useEffect } from "react";

const navGroups = [
  {
    label: "Analysis",
    items: [
      { href: "/dashboard",             label: "Overview",           icon: LayoutDashboard },
      { href: "/dashboard/analyzer",    label: "Policy Analyzer",    icon: FileSearch },
      { href: "/dashboard/cis",         label: "CIS Scanner",        icon: FileSpreadsheet },
      { href: "/dashboard/auditor",     label: "Rejection Auditor",  icon: AlertTriangle },
    ],
  },
  {
    label: "Action",
    items: [
      { href: "/dashboard/appeals",     label: "Appeal Drafter",     icon: FileText },
      { href: "/dashboard/portability", label: "Portability Advisor",icon: ArrowRightLeft },
      { href: "/dashboard/e-jagriti",   label: "e-Jagriti Guide",    icon: Monitor },
    ],
  },
  {
    label: "Tracking",
    items: [
      { href: "/dashboard/timeline",    label: "Timeline Tracker",   icon: Clock },
      { href: "/dashboard/documents",   label: "My Documents",       icon: Upload },
    ],
  },
  {
    label: "Account",
    items: [
      { href: "/dashboard/settings",    label: "Settings",           icon: Settings },
    ],
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login");
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  const handleLogout = () => { logout(); router.push("/auth/login"); };
  const allItems = navGroups.flatMap((g) => g.items);
  const currentPage = allItems.find(
    (n) => pathname === n.href || (n.href !== "/dashboard" && pathname.startsWith(n.href))
  );

  return (
    <div className="min-h-screen flex" style={{background:"var(--surface)"}}>
      {/* Sidebar */}
      <aside className="w-60 flex flex-col fixed h-full z-40 border-r"
        style={{background:"var(--surface-1)",borderColor:"var(--surface-4)"}}>
        {/* Logo */}
        <div className="h-16 flex items-center gap-2.5 px-4 border-b"
          style={{borderColor:"var(--surface-4)"}}>
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{background:"linear-gradient(135deg,#7C3AED,#4F46E5)"}}>
            <ShieldCheck size={14} className="text-white" />
          </div>
          <span className="font-bold text-sm" style={{color:"var(--text-primary)"}}>RedoClaim</span>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 py-4 px-3 space-y-5 overflow-y-auto">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="text-xs font-semibold px-3 mb-1.5 tracking-widest uppercase"
                style={{color:"var(--text-tertiary)"}}>
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map(({ href, label, icon: Icon }) => {
                  const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
                  return (
                    <Link key={href} href={href}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150"
                      style={active ? {
                        background:"rgba(139,92,246,0.15)",
                        color:"#C4B5FD",
                        border:"1px solid rgba(139,92,246,0.2)",
                      } : {
                        color:"var(--text-secondary)",
                        border:"1px solid transparent",
                      }}
                      onMouseEnter={(e) => {
                        if (!active) {
                          (e.currentTarget as HTMLElement).style.background = "var(--surface-2)";
                          (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!active) {
                          (e.currentTarget as HTMLElement).style.background = "transparent";
                          (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                        }
                      }}>
                      <Icon size={15} />
                      <span>{label}</span>
                      {active && <ChevronRight size={12} className="ml-auto opacity-60" />}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-3 border-t space-y-1" style={{borderColor:"var(--surface-4)"}}>
          <a href="/disclaimer"
            className="flex items-center gap-2 w-full px-3 py-2 text-xs rounded-lg transition-colors"
            style={{color:"#FCD34D",background:"rgba(251,191,36,0.07)",border:"1px solid rgba(251,191,36,0.15)"}}>
            ⚠️ AI Disclaimer
          </a>

          {/* User avatar — click to go to settings */}
          <Link href="/dashboard/settings"
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg mt-2 transition-all"
            style={{background:"var(--surface-2)"}}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.1)";
              (e.currentTarget as HTMLElement).style.border = "1px solid rgba(139,92,246,0.2)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = "var(--surface-2)";
              (e.currentTarget as HTMLElement).style.border = "1px solid transparent";
            }}
            title="Go to Settings">
            <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
              style={{background:"rgba(139,92,246,0.2)"}}>
              <User size={13} style={{color:"#A78BFA"}} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate" style={{color:"var(--text-primary)"}}>{user?.full_name}</p>
              <p className="text-xs truncate" style={{color:"var(--text-tertiary)"}}>{user?.email}</p>
            </div>
            <Settings size={12} style={{color:"var(--text-tertiary)"}} className="shrink-0" />
          </Link>

          <button onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs rounded-lg transition-colors"
            style={{color:"var(--text-secondary)"}}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "#F87171"; (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.08)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
            <LogOut size={13} /> Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 ml-60">
        {/* Top bar */}
        <header className="h-16 flex items-center justify-between px-6 sticky top-0 z-30 border-b backdrop-blur-xl"
          style={{background:"rgba(10,10,15,0.9)",borderColor:"var(--surface-4)"}}>
          <div>
            <h1 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>
              {currentPage?.label || "Dashboard"}
            </h1>
            <p className="text-xs" style={{color:"var(--text-tertiary)"}}>
              IRDAI Master Circular 2024 • All AI runs locally
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button className="relative w-9 h-9 flex items-center justify-center rounded-lg transition"
              style={{border:"1px solid var(--surface-5)"}}
              onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.background = "var(--surface-2)"}
              onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.background = "transparent"}>
              <Bell size={15} style={{color:"var(--text-secondary)"}} />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full" style={{background:"#F87171"}} />
            </button>
            <Link href="/dashboard/auditor" className="btn-primary text-xs px-3 py-2">
              + Audit Claim
            </Link>
          </div>
        </header>

        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}