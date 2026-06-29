import { ArrowDownRight, MessageCircle } from "lucide-react";
import { productImage } from "../api/client";
import type { Product } from "../types";

export function Hero({ products, onStylist }: { products: Product[]; onStylist: () => void }) {
  const primary = products[0];
  const secondary = products[1];
  return (
    <section className="hero-grid border-b border-ink/10">
      <div className="flex min-h-[620px] flex-col justify-between bg-[#ded9d0] p-7 lg:p-12">
        <div className="flex items-center justify-between text-[9px] uppercase tracking-[.2em] text-muted"><span>The personal edit</span><span>01 / 26</span></div>
        <div className="max-w-xl py-12">
          <p className="mb-5 font-mono text-[9px] uppercase tracking-[.22em] text-accent">Curated for real life</p>
          <h1 className="font-display text-[clamp(54px,7vw,104px)] leading-[.88] tracking-[-.055em]">Quiet pieces.<br />Clear point<br />of view.</h1>
          <p className="mt-7 max-w-full break-all text-sm leading-6 text-[#57534d] sm:max-w-md sm:break-normal">让私人顾问从 5,000 件真实商品中，按你的场景、颜色与参考图片建立专属衣橱提案。</p>
          <button onClick={onStylist} className="mt-8 inline-flex items-center gap-3 border-b border-ink pb-2 text-[11px] uppercase tracking-[.18em] transition-colors hover:border-accent hover:text-accent">
            <MessageCircle size={15} strokeWidth={1.4} /> Consult the stylist
          </button>
        </div>
        <div className="flex items-center justify-between border-t border-ink/15 pt-4 text-[10px] text-muted"><span>Text · Image · Context</span><ArrowDownRight size={16} /></div>
      </div>
      <div className="grid min-h-[620px] grid-cols-[1.25fr_.75fr] gap-px bg-ink/10">
        {[primary, secondary].map((product, index) => (
          <figure key={product?.article_id || index} className="relative overflow-hidden bg-[#ece9e3]">
            {product && <img src={productImage(product)} alt={product.prod_name} className="h-full w-full object-cover transition-transform duration-1000 hover:scale-[1.025]" />}
            {product && <figcaption className="absolute bottom-5 left-5 bg-paper/92 px-3 py-2 text-[10px] backdrop-blur-sm"><span className="font-medium">{product.prod_name}</span><span className="ml-2 text-muted">0{index + 1}</span></figcaption>}
          </figure>
        ))}
      </div>
    </section>
  );
}
