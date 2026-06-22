// Typed fetch wrappers + SSE reader for CreativeIQ.
// Base: VITE_API_BASE if set (deployed API Gateway), else "/api" (Vite dev proxy -> local FastAPI).

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) || "/api";

// Asset base: images returned as "/data/..." are served by the same backend.
// In dev the Vite proxy forwards /data; against a deployed API set VITE_ASSET_BASE.
const ASSET_BASE = (import.meta.env.VITE_ASSET_BASE as string | undefined) || "";

export function assetUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return ASSET_BASE + path;
}

export interface Product {
  id: string; name: string; category: string; price: number;
  description: string; image_url: string; tags: string[];
}

export interface Segment {
  id: string; name: string; channel: string; age_band: string;
  tone: string; top_format: string; blurb: string;
  avg_ctr: number; avg_ctr_pct: string; n_campaigns: number;
}

export interface Copy { headline: string; body: string; cta: string; }

export interface Prediction {
  predicted_ctr: number; predicted_ctr_pct: string; confidence: string;
  based_on_n_campaigns: number; segment_avg_ctr_pct: string;
  lift_vs_segment_avg_pct: string;
  factors: Record<string, { value: string; factor: number; n: number }>;
}

export async function getCatalog(): Promise<Product[]> {
  const r = await fetch(`${API_BASE}/catalog`);
  return r.json();
}

export async function getSegments(): Promise<Segment[]> {
  const r = await fetch(`${API_BASE}/segments`);
  return r.json();
}

export interface Campaign {
  campaign_id: string; date: string; product_id: string; segment_id: string;
  channel: string; format: string; image_style: string; copy_tone: string;
  impressions: number; clicks: number; ctr: number; ctr_pct: string;
  top_performer: boolean;
}

export interface CampaignStats {
  total_campaigns: number; shown: number; book_avg_ctr: number;
  book_avg_ctr_pct: string; total_impressions: number; total_clicks: number;
  date_range: string;
}

export interface CampaignsResponse { campaigns: Campaign[]; stats: CampaignStats; }

export async function getCampaigns(limit = 60): Promise<CampaignsResponse> {
  const r = await fetch(`${API_BASE}/campaigns?limit=${limit}`);
  return r.json();
}

export interface AnalyticsCell { format: string; n: number; ctr: number | null; ctr_pct: string; }
export interface AnalyticsRow {
  segment_id: string; segment_name: string; channel: string;
  segment_ctr: number; segment_ctr_pct: string; n: number; cells: AnalyticsCell[];
}
export interface Analytics {
  formats: string[];
  matrix: AnalyticsRow[];
  book_avg_ctr: number; book_avg_ctr_pct: string;
  total_campaigns: number;
  best_combo: { segment_name: string; format: string; ctr_pct: string; ctr: number } | null;
}

export async function getAnalytics(): Promise<Analytics> {
  const r = await fetch(`${API_BASE}/analytics`);
  return r.json();
}

export interface ComparableCampaign {
  campaign_id: string; date: string; product_id: string; format: string;
  image_style: string; copy_tone: string; impressions: number; ctr: number; ctr_pct: string;
}
export interface Comparable {
  segment_id: string; matched_count: number; segment_count: number; avg_ctr_pct: string;
  filters_applied: { field: string; value: string }[];
  campaigns: ComparableCampaign[];
}

export async function getComparable(params: {
  segment_id: string; format?: string; image_style?: string; copy_tone?: string;
}): Promise<Comparable> {
  const q = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v != null) as [string, string][]
  );
  const r = await fetch(`${API_BASE}/comparable?${q.toString()}`);
  return r.json();
}

export async function predict(body: {
  segment_id: string; format?: string; image_style?: string; copy_tone?: string;
}): Promise<Prediction> {
  const r = await fetch(`${API_BASE}/predict`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  return r.json();
}

export interface GenerateCallbacks {
  onMeta?: (m: any) => void;
  onDelta?: (text: string) => void;
  onCopy?: (c: Copy) => void;
  onImage?: (url: string, source?: string) => void;
  onDone?: (d: { source: string; elapsed_ms: number; exact_cache_hit: boolean }) => void;
  onError?: (e: string) => void;
}

export interface GenerateBody {
  segment_id: string;
  product_id?: string;          // catalog product
  product_name?: string;        // uploaded product
  category?: string;            // uploaded product
  description?: string;
  image_url?: string;           // uploaded image (data URL) — for parity / live path
}

// Streams /generate via SSE-over-fetch (ReadableStream parsing).
export async function generate(
  body: GenerateBody,
  cb: GenerateCallbacks
): Promise<void> {
  const resp = await fetch(`${API_BASE}/generate`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!resp.body) { cb.onError?.("no stream body"); return; }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const chunks = buf.split("\n\n");
    buf = chunks.pop() || "";
    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      let parsed: any;
      try { parsed = JSON.parse(data); } catch { continue; }
      switch (event) {
        case "meta": cb.onMeta?.(parsed); break;
        case "delta": cb.onDelta?.(parsed.text); break;
        case "copy": cb.onCopy?.(parsed.copy); break;
        case "image": cb.onImage?.(parsed.image_url, parsed.source); break;
        case "done": cb.onDone?.(parsed); break;
        case "error": cb.onError?.(parsed.error); break;
      }
    }
  }
}
