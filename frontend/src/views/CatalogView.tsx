import { useEffect, useState } from "react";
import { getCatalog, assetUrl, type Product } from "../lib/api";

export default function CatalogView() {
  const [products, setProducts] = useState<Product[]>([]);
  useEffect(() => { getCatalog().then(setProducts); }, []);
  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
      <h2 className="font-serif text-3xl text-ink mb-1">Product Catalog</h2>
      <p className="text-stone mb-6">Lumen &amp; Coast resort-wear · {products.length} products</p>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        {products.map((p) => (
          <div key={p.id} className="rounded-2xl bg-panel shadow-card overflow-hidden border border-stone/10">
            <img src={assetUrl(p.image_url)} alt={p.name} className="w-full aspect-square object-cover bg-sand" />
            <div className="p-4">
              <div className="font-semibold text-ink">{p.name}</div>
              <div className="text-sm text-stone">${p.price} · {p.category}</div>
              <p className="text-xs text-stone/90 mt-2 leading-snug">{p.description}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {p.tags.map((t) => <span key={t} className="text-[10px] bg-sand text-stone px-2 py-0.5 rounded-full">{t}</span>)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
