import { Check, GitCompareArrows, Plus } from "lucide-react";
import { productImage } from "../api/client";
import type { Product } from "../types";

type Props = {
  product: Product;
  index: number;
  selected: boolean;
  onCompare: () => void;
  onAdd: () => void;
  onDetail: () => void;
};

export function ProductCard({ product, index, selected, onCompare, onAdd, onDetail }: Props) {
  return (
    <article className="product-card group animate-reveal" style={{ animationDelay: `${Math.min(index, 8) * 45}ms` }}>
      <div className="relative aspect-[3/4] overflow-hidden bg-[#e8e4dc]">
        <button onClick={onDetail} className="h-full w-full" aria-label={`查看 ${product.prod_name} 详情`}><img src={productImage(product)} alt={product.prod_name} loading="lazy" className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.035]" /></button>
        <span className="absolute left-3 top-3 bg-paper/90 px-2 py-1 font-mono text-[9px] tracking-wider backdrop-blur-sm">
          {String(index + 1).padStart(2, "0")}
        </span>
        {typeof product.score === "number" && (
          <span className="absolute bottom-3 left-3 bg-ink/85 px-2 py-1 text-[9px] tracking-wider text-white">
            MATCH {Math.round(product.score * 100)}%
          </span>
        )}
        <div className="absolute bottom-3 right-3 flex gap-2 opacity-100 transition-all duration-300 md:translate-y-2 md:opacity-0 md:group-hover:translate-y-0 md:group-hover:opacity-100">
          <button className="grid h-9 w-9 place-items-center bg-paper text-ink hover:bg-ink hover:text-white" onClick={onCompare} aria-label="加入对比">
            {selected ? <Check size={15} /> : <GitCompareArrows size={15} />}
          </button>
          <button className="grid h-9 w-9 place-items-center bg-accent text-white hover:bg-accent-dark" onClick={onAdd} aria-label="加入购物袋">
            <Plus size={16} />
          </button>
        </div>
      </div>
      <div className="pt-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <button onClick={onDetail} className="block max-w-full truncate text-left text-sm font-medium hover:text-accent">{product.prod_name}</button>
            <p className="mt-1 text-xs text-muted">{product.product_type_name} · {product.colour_group_name}</p>
          </div>
          <button onClick={onAdd} className="mt-0.5 text-muted transition-colors hover:text-accent"><Plus size={16} /></button>
        </div>
        {product.reason && <p className="mt-2 line-clamp-2 text-xs leading-5 text-muted">{product.reason}</p>}
        {product.price_info && <p className="mt-2 font-mono text-[10px] text-muted">DATA PRICE {product.price_info.amount.toFixed(4)} · {product.price_info.currency}</p>}
      </div>
    </article>
  );
}
