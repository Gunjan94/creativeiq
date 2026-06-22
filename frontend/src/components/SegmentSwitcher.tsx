import type { Segment } from "../lib/api";
import { SEGMENT_ACCENT } from "../theme";

interface Props {
  segments: Segment[];
  selected: string | null;
  onSelect: (id: string) => void;
  label?: string;
}

// Segment chips. When changed after a generation, the parent re-fires /generate + /predict.
export default function SegmentSwitcher({ segments, selected, onSelect, label = "Target segment" }: Props) {
  return (
    <div>
      <div className="text-xs uppercase tracking-widest text-stone mb-2">{label}</div>
      <div className="grid grid-cols-2 gap-2">
        {segments.map((s) => {
          const active = s.id === selected;
          const accent = SEGMENT_ACCENT[s.id] || "#5C8A8A";
          return (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={`text-left rounded-xl px-4 py-3 min-h-[48px] border-2 transition-all ${
                active ? "text-white shadow-card scale-[1.02]" : "bg-panel border-stone/15 text-ink hover:border-stone/40"
              }`}
              style={active ? { backgroundColor: accent, borderColor: accent } : {}}
            >
              <div className="font-semibold leading-tight">{s.name}</div>
              <div className={`text-xs ${active ? "text-white/85" : "text-stone"}`}>
                {s.channel} · {s.age_band}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
