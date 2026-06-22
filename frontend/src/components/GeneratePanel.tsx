import { useRef } from "react";
import { assetUrl, type Product, type Segment } from "../lib/api";
import SegmentSwitcher from "./SegmentSwitcher";

export type StudioMode = "catalog" | "upload";

interface Props {
  products: Product[];
  segments: Segment[];
  mode: StudioMode;
  selectedProduct: string | null;
  selectedSegment: string | null;
  uploadedImage: string | null;
  uploadedName: string;
  uploadedCategory: string;
  onProduct: (id: string) => void;
  onSegment: (id: string) => void;
  onUploadFile: (dataUrl: string, fileName: string) => void;
  onUploadedName: (name: string) => void;
  onUploadedCategory: (cat: string) => void;
  onClearUpload: () => void;
  onGenerate: () => void;
  generating: boolean;
}

const CATEGORIES = ["tops", "bottoms", "dresses", "footwear", "bags", "accessories", "swim"];

export default function GeneratePanel(p: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  function handleFile(file?: File) {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const guessName = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ").trim();
      p.onUploadFile(dataUrl, guessName);
    };
    reader.readAsDataURL(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    handleFile(e.dataTransfer.files?.[0]);
  }

  const canGenerate =
    !!p.selectedSegment &&
    (p.mode === "catalog" ? !!p.selectedProduct : !!p.uploadedImage) &&
    !p.generating;

  return (
    <div className="rounded-3xl bg-panel/70 backdrop-blur border border-stone/10 p-6 flex flex-col gap-6 shadow-card">
      {/* Product source */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs uppercase tracking-widest text-stone">Product</div>
          {p.mode === "upload" && (
            <button onClick={p.onClearUpload} className="text-xs text-terracotta hover:underline">
              ← Back to catalog
            </button>
          )}
        </div>

        {p.mode === "catalog" ? (
          <div className="grid grid-cols-2 gap-2 max-h-[300px] overflow-y-auto pr-1">
            {/* Upload tile (click OR drag-and-drop) */}
            <button
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="text-left rounded-xl px-3 py-3 min-h-[64px] border-2 border-dashed border-teal/50 bg-teal/5 text-teal-deep hover:border-teal hover:bg-teal/10 transition-all flex flex-col items-center justify-center gap-1"
            >
              <UploadIcon />
              <div className="font-semibold text-xs leading-tight text-center">Upload your product</div>
              <div className="text-[10px] text-teal-deep/70 text-center">click or drop an image</div>
            </button>

            {p.products.map((prod) => {
              const active = prod.id === p.selectedProduct;
              return (
                <button
                  key={prod.id}
                  onClick={() => p.onProduct(prod.id)}
                  className={`text-left rounded-xl overflow-hidden border-2 transition-all ${
                    active ? "border-teal-deep shadow-card scale-[1.02]" : "border-stone/15 hover:border-stone/40"
                  }`}
                >
                  <div className="aspect-[4/3] bg-sand overflow-hidden">
                    <img src={assetUrl(prod.image_url)} alt={prod.name} className="w-full h-full object-cover" />
                  </div>
                  <div className={`px-2.5 py-2 ${active ? "bg-teal-deep text-white" : "bg-panel text-ink"}`}>
                    <div className="font-semibold text-xs leading-tight truncate">{prod.name}</div>
                    <div className={`text-[11px] ${active ? "text-white/80" : "text-stone"}`}>${prod.price} · {prod.category}</div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          /* Upload mode: preview + name + category */
          <div className="flex flex-col gap-3">
            <div className="rounded-xl overflow-hidden border-2 border-teal/40 bg-sand aspect-[4/3]">
              {p.uploadedImage && <img src={p.uploadedImage} alt="Uploaded product" className="w-full h-full object-cover" />}
            </div>
            <button onClick={() => fileRef.current?.click()} className="text-xs text-teal-deep hover:underline self-start">
              Replace image
            </button>
            <label className="text-xs uppercase tracking-widest text-stone">Product name</label>
            <input
              value={p.uploadedName}
              onChange={(e) => p.onUploadedName(e.target.value)}
              placeholder="e.g. Aurora Wrap Dress"
              className="rounded-xl border-2 border-stone/15 bg-panel px-3 py-2.5 min-h-[44px] text-ink focus:border-teal outline-none"
            />
            <label className="text-xs uppercase tracking-widest text-stone">Category</label>
            <div className="flex flex-wrap gap-1.5">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  onClick={() => p.onUploadedCategory(c)}
                  className={`text-xs px-3 py-1.5 rounded-full border min-h-[36px] capitalize ${
                    p.uploadedCategory === c ? "bg-teal-deep text-white border-teal-deep" : "bg-panel border-stone/20 text-stone hover:border-stone/40"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      <SegmentSwitcher segments={p.segments} selected={p.selectedSegment} onSelect={p.onSegment} />

      <button
        onClick={p.onGenerate}
        disabled={!canGenerate}
        className="w-full bg-terracotta text-offwhite font-bold text-lg py-4 rounded-2xl min-h-[56px] shadow-card disabled:opacity-40 transition-all active:scale-[0.98]"
      >
        {p.generating ? "Generating…" : "Generate creative"}
      </button>
      <p className="text-xs text-stone text-center -mt-3">
        Switch the segment after generating to retarget live.
      </p>
    </div>
  );
}

function UploadIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
    </svg>
  );
}
