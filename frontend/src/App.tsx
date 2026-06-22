import { useState } from "react";
import StudioView from "./views/StudioView";
import CatalogView from "./views/CatalogView";
import SegmentsView from "./views/SegmentsView";
import CampaignsView from "./views/CampaignsView";
import { getMode, toggleMode, type Mode } from "./theme";

type Tab = "studio" | "catalog" | "segments" | "campaigns";

export default function App() {
  const [tab, setTab] = useState<Tab>("studio");
  const [mode, setMode] = useState<Mode>(getMode());

  const NavBtn = ({ id, label }: { id: Tab; label: string }) => (
    <button
      onClick={() => setTab(id)}
      className={`px-4 py-2 rounded-full text-sm font-medium min-h-[44px] transition-all ${
        tab === id ? "bg-ink text-offwhite" : "text-ink/70 hover:bg-ink/5"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-full">
      <header
        className="sticky top-0 z-10 backdrop-blur border-b border-stone/15"
        style={{ background: "var(--header-bg)" }}
      >
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-3 flex items-center justify-between gap-3">
          <div className="flex items-baseline gap-3">
            <span className="font-serif text-2xl tracking-wide text-teal-deep">
              Creative<span className="text-terracotta">IQ</span>
            </span>
            <span className="hidden sm:inline text-xs uppercase tracking-widest text-stone">
              Lumen &amp; Coast · Ad Studio
            </span>
          </div>
          <div className="flex items-center gap-2">
            <nav className="flex gap-1">
              <NavBtn id="studio" label="Studio" />
              <NavBtn id="catalog" label="Catalog" />
              <NavBtn id="segments" label="Segments" />
              <NavBtn id="campaigns" label="Campaigns" />
            </nav>
            <button
              onClick={() => setMode(toggleMode())}
              aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} theme`}
              title={`Switch to ${mode === "dark" ? "light" : "dark"} theme`}
              className="flex items-center justify-center rounded-full min-h-[44px] min-w-[44px] text-ink/70 hover:bg-ink/5 transition-colors"
            >
              {mode === "dark" ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>
        </div>
      </header>

      {tab === "studio" && (
        <div className="bg-gradient-to-b from-sand/60 to-offwhite">
          <div className="max-w-7xl mx-auto px-4 md:px-8 pt-8 pb-2">
            <h1 className="font-serif text-3xl md:text-4xl text-ink leading-tight">
              From brief to on-brand campaign in <span className="text-terracotta">under a minute</span>.
            </h1>
            <p className="text-stone mt-2 max-w-2xl">
              Pick a product from the catalog — or upload your own — and choose a target segment.
              CreativeIQ composes the on-brand creative, writes the copy, picks the format, and predicts
              the click-through rate from your own campaign history.
            </p>
          </div>
          <StudioView />
        </div>
      )}
      {tab === "catalog" && <CatalogView />}
      {tab === "segments" && <SegmentsView />}
      {tab === "campaigns" && <CampaignsView />}
    </div>
  );
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  );
}
