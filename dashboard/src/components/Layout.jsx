import { FolderTree, Menu } from "lucide-react";
import { useState } from "react";
import { navItems } from "../App.jsx";
import Sidebar from "./Sidebar.jsx";

export default function Layout({ activePage, setActivePage, children }) {
  const [open, setOpen] = useState(false);
  const active = navItems.find((item) => item.id === activePage);
  return (
    <div className="min-h-screen soft-grid">
      <Sidebar activePage={activePage} setActivePage={setActivePage} open={open} setOpen={setOpen} />
      <main className="report-canvas lg:pl-80">
        <header className="sticky top-0 z-30 border-b border-[#e5ded2] bg-[#f8f5ef]/90 backdrop-blur-xl">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            <button
              className="grid h-10 w-10 place-items-center rounded-md border border-[#e5ded2] bg-white lg:hidden"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={19} />
            </button>
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-[#744210]">Online Retail II Customer Analytics</p>
              <h1 className="text-lg font-semibold text-[#172033]">{active?.label}</h1>
            </div>
            <div className="hidden items-center gap-2 rounded-md border border-[#e5ded2] bg-[#fffaf0] px-3 py-2 text-sm text-[#744210] md:flex">
              <FolderTree size={16} />
              <span>Offline artifact review</span>
            </div>
          </div>
        </header>
        <div className="px-4 py-6 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}
