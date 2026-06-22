import { assetUrl, type Copy } from "../lib/api";
import { FORMAT_ASPECT, FORMAT_LABEL, SEGMENT_ACCENT } from "../theme";

/**
 * AdCreative — renders the finished ad.
 *
 * Two layouts:
 *  • GENERATED (source "generated"/"live"): the AI image is produced at the ad's
 *    aspect ratio, so it fills the frame edge-to-edge. We overlay a brand-tinted
 *    scrim + headline/body/CTA + channel chrome — a real social/display ad.
 *  • PREVIEW (source "preview", compose-over-photo fallback): the real product
 *    photo is shown IN FULL (object-contain over a blurred fill) in its own region
 *    with copy in a separate brand panel — so a portrait is never cropped through
 *    the face/legs.
 */
interface Props {
  baseImageUrl: string | null;
  segmentId: string | null;
  channel?: string;
  format: string | null;
  copy: Copy | null;
  streamingText: string;
  generating: boolean;
  source: string | null;      // "live" | "generated" | "preview"
  brandName: string;
}

const HORIZONTAL = new Set(["email_hero", "display_banner"]);

export default function AdCreative(p: Props) {
  const aspect = p.format ? FORMAT_ASPECT[p.format] || "1 / 1" : "1 / 1";
  const accent = p.segmentId ? SEGMENT_ACCENT[p.segmentId] || "#5C8A8A" : "#5C8A8A";
  const isEmail = p.format === "email_hero";
  const isInstagram = (p.channel || "").toLowerCase() === "instagram";
  const showTyping = p.generating && !p.copy;
  const generated = p.source === "generated" || p.source === "live";

  if (!p.baseImageUrl) {
    return (
      <div
        className="relative w-full rounded-2xl overflow-hidden bg-sand flex items-center justify-center border border-stone/10"
        style={{ aspectRatio: aspect, maxHeight: "62vh" }}
      >
        <div className="text-stone text-center px-8">
          <div className="text-2xl font-serif mb-2">Your creative will appear here</div>
          <div className="text-sm">Pick a product and a segment — or upload your own — then Generate.</div>
        </div>
      </div>
    );
  }

  const src = assetUrl(p.baseImageUrl);
  const wordmark = (
    <div className="absolute top-3 left-4 text-offwhite font-serif tracking-[0.18em] text-xs md:text-sm drop-shadow-[0_1px_3px_rgba(0,0,0,0.6)] z-10">
      {p.brandName.toUpperCase()}
    </div>
  );
  const badge = p.format && (
    <span className="absolute top-3 right-3 bg-black/40 text-offwhite text-[10px] uppercase tracking-wider px-2 py-1 rounded-full backdrop-blur z-10">
      {FORMAT_LABEL[p.format] || p.format}
    </span>
  );

  // ---- GENERATED: full-bleed AI image + scrim + overlaid copy ----
  if (generated) {
    return (
      <div
        className="relative w-full rounded-2xl overflow-hidden shadow-card bg-ink"
        style={{ aspectRatio: aspect, maxHeight: "62vh" }}
      >
        <img key={src} src={src} alt="Generated ad creative" className="absolute inset-0 w-full h-full object-cover animate-fade-in" />
        <div
          className="absolute inset-0"
          style={{ background: `linear-gradient(to top, ${accent}F2 0%, ${accent}80 28%, rgba(0,0,0,0.10) 55%, rgba(0,0,0,0) 100%)` }}
        />
        {wordmark}
        {badge}
        {isInstagram && p.copy && (
          <div className="absolute top-12 right-4 flex items-center gap-3 text-offwhite drop-shadow-[0_1px_3px_rgba(0,0,0,0.6)] z-10">
            <HeartIcon /><CommentIcon /><ShareIcon />
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 p-5 md:p-6 text-offwhite">
          {isEmail && (p.copy || showTyping) && (
            <div className="inline-block bg-offwhite/95 text-ink text-[11px] font-semibold px-2.5 py-1 rounded mb-2">✉ Subject</div>
          )}
          {showTyping ? (
            <p className="font-serif text-2xl leading-snug whitespace-pre-wrap drop-shadow cursor-blink">{p.streamingText}</p>
          ) : p.copy ? (
            <div className="animate-fade-in">
              <h3 className="font-serif font-bold leading-tight drop-shadow text-2xl md:text-3xl">{p.copy.headline}</h3>
              <p className="opacity-95 mt-2 leading-snug drop-shadow max-w-xl text-sm md:text-base">{p.copy.body}</p>
              <button className="mt-3 font-semibold bg-offwhite px-5 py-2.5 rounded-full shadow min-h-[44px] text-sm active:scale-95 transition-transform" style={{ color: accent }}>
                {p.copy.cta} →
              </button>
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  // ---- PREVIEW: split-panel, full photo (no crop) + copy panel ----
  const horizontal = p.format ? HORIZONTAL.has(p.format) : false;
  return (
    <div
      className={`relative w-full rounded-2xl overflow-hidden shadow-card flex ${horizontal ? "flex-row" : "flex-col"}`}
      style={{ aspectRatio: aspect, maxHeight: "62vh" }}
    >
      <div className={`relative overflow-hidden bg-sand ${horizontal ? "h-full" : "w-full"}`} style={horizontal ? { flexBasis: "52%" } : { flexBasis: "58%" }}>
        <img src={src} aria-hidden className="absolute inset-0 w-full h-full object-cover scale-125 blur-2xl opacity-60" />
        <img key={src} src={src} alt="Product" className="relative w-full h-full object-contain animate-fade-in" />
        {wordmark}{badge}
      </div>
      <div className="relative flex flex-col justify-center text-offwhite flex-1" style={{ background: accent, flexBasis: horizontal ? "48%" : "42%" }}>
        <div className="p-5 md:p-6">
          {isEmail && (p.copy || showTyping) && (
            <div className="inline-block bg-offwhite/95 text-ink text-[11px] font-semibold px-2.5 py-1 rounded mb-2">✉ Subject</div>
          )}
          {showTyping ? (
            <p className="font-serif text-xl leading-snug whitespace-pre-wrap">{p.streamingText}</p>
          ) : p.copy ? (
            <div className="animate-fade-in">
              <h3 className="font-serif font-bold leading-tight text-2xl md:text-3xl">{p.copy.headline}</h3>
              <p className="opacity-90 mt-2 leading-snug text-sm md:text-base">{p.copy.body}</p>
              <button className="mt-4 font-semibold bg-offwhite px-5 py-2.5 rounded-full shadow min-h-[44px] text-sm active:scale-95 transition-transform" style={{ color: accent }}>
                {p.copy.cta} →
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function HeartIcon() {
  return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z" /></svg>);
}
function CommentIcon() {
  return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9 9 0 0 1-3.9-.9L3 20l1-3.9A8.4 8.4 0 1 1 21 11.5z" /></svg>);
}
function ShareIcon() {
  return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" /></svg>);
}
