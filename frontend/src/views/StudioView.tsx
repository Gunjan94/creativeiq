import { useEffect, useRef, useState } from "react";
import {
  getCatalog, getSegments, generate, predict,
  type Product, type Segment, type Copy, type Prediction,
} from "../lib/api";
import GeneratePanel, { type StudioMode } from "../components/GeneratePanel";
import CreativeCard from "../components/CreativeCard";
import BeforeAfterPanel from "../components/BeforeAfterPanel";

export default function StudioView() {
  const [products, setProducts] = useState<Product[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [product, setProduct] = useState<string | null>(null);
  const [segment, setSegment] = useState<string | null>(null);

  // Upload mode
  const [mode, setMode] = useState<StudioMode>("catalog");
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedName, setUploadedName] = useState("");
  const [uploadedCategory, setUploadedCategory] = useState("tops");

  const [generating, setGenerating] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [copy, setCopy] = useState<Copy | null>(null);
  const [liveImageUrl, setLiveImageUrl] = useState<string | null>(null);   // net-new (live Bedrock)
  const [productImageUrl, setProductImageUrl] = useState<string | null>(null); // composition base from backend
  const [format, setFormat] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [brandTokens, setBrandTokens] = useState<string[]>([]);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [hasGenerated, setHasGenerated] = useState(false);

  const runId = useRef(0);

  useEffect(() => {
    getCatalog().then((c) => {
      setProducts(c);
      setProduct((prev) => prev ?? (c.find((p) => p.id === "linen-resort-shirt")?.id || c[0]?.id || null));
    });
    getSegments().then((s) => {
      setSegments(s);
      setSegment((prev) => prev ?? (s.find((x) => x.id === "genz-instagram")?.id || s[0]?.id || null));
    });
  }, []);

  const selectedSegmentObj = segments.find((s) => s.id === segment) || null;
  // The composition base: a live net-new image if produced, else the product/upload photo.
  const baseImageUrl =
    liveImageUrl ||
    (mode === "upload" ? uploadedImage : productImageUrl) ||
    (mode === "catalog" ? products.find((p) => p.id === product)?.image_url || null : null);

  async function runGenerate(sid: string) {
    const myRun = ++runId.current;
    setGenerating(true);
    setHasGenerated(true);
    setStreamingText("");
    setCopy(null);
    setLiveImageUrl(null);

    predict({ segment_id: sid }).then((pr) => {
      if (myRun === runId.current) setPrediction(pr);
    });

    const body =
      mode === "upload"
        ? { segment_id: sid, product_name: uploadedName || "Your product", category: uploadedCategory, image_url: uploadedImage || undefined }
        : { segment_id: sid, product_id: product! };

    await generate(body, {
      onMeta: (m) => {
        if (myRun !== runId.current) return;
        setFormat(m.format);
        setBrandTokens(m.brand_tokens_applied || []);
        setSource(m.source);
        if (m.product_image_url) setProductImageUrl(m.product_image_url);
        if (m.prediction) setPrediction(m.prediction);
      },
      onDelta: (t) => { if (myRun === runId.current) setStreamingText((s) => s + t); },
      onCopy: (c) => { if (myRun === runId.current) setCopy(c); },
      onImage: (url, src) => {
        if (myRun !== runId.current) return;
        if (url) setLiveImageUrl(url);
        if (src) setSource(src);
      },
      onDone: (d) => {
        if (myRun !== runId.current) return;
        setSource(d.source);
        setElapsedMs(d.elapsed_ms);
        setGenerating(false);
      },
      onError: () => { if (myRun === runId.current) setGenerating(false); },
    });
  }

  function handleGenerate() {
    if (!segment) return;
    if (mode === "catalog" && !product) return;
    if (mode === "upload" && !uploadedImage) return;
    runGenerate(segment);
  }

  // Live retarget: switching segment AFTER a generation re-fires immediately.
  function handleSegment(sid: string) {
    setSegment(sid);
    const ready = mode === "catalog" ? !!product : !!uploadedImage;
    if (hasGenerated && ready) runGenerate(sid);
  }

  function handleUploadFile(dataUrl: string, fileName: string) {
    setMode("upload");
    setUploadedImage(dataUrl);
    if (!uploadedName) setUploadedName(fileName || "Your product");
    // Reset prior creative so the new product reads clean.
    setCopy(null); setStreamingText(""); setLiveImageUrl(null); setSource(null);
  }

  function clearUpload() {
    setMode("catalog");
    setUploadedImage(null);
    setUploadedName("");
    setCopy(null); setStreamingText(""); setLiveImageUrl(null); setSource(null);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(320px,400px)_1fr] gap-6 items-start">
        <GeneratePanel
          products={products}
          segments={segments}
          mode={mode}
          selectedProduct={product}
          selectedSegment={segment}
          uploadedImage={uploadedImage}
          uploadedName={uploadedName}
          uploadedCategory={uploadedCategory}
          onProduct={setProduct}
          onSegment={handleSegment}
          onUploadFile={handleUploadFile}
          onUploadedName={setUploadedName}
          onUploadedCategory={setUploadedCategory}
          onClearUpload={clearUpload}
          onGenerate={handleGenerate}
          generating={generating}
        />
        <CreativeCard
          baseImageUrl={baseImageUrl}
          segmentId={segment}
          segmentName={selectedSegmentObj?.name}
          channel={selectedSegmentObj?.channel}
          streamingText={streamingText}
          copy={copy}
          format={format}
          prediction={prediction}
          generating={generating}
          source={source}
          brandTokens={brandTokens}
        />
      </div>
      <div className="mt-8">
        <BeforeAfterPanel elapsedMs={elapsedMs} />
      </div>
    </div>
  );
}
