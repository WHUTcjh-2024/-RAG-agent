import type { Product } from "../types";
import { ProductCard } from "./ProductCard";
import { useTranslation } from "../i18n";

type Props = {
  products: Product[];
  compareIds: string[];
  onCompare: (id: string) => void;
  onAdd: (id: string) => void;
  onDetail: (id: string) => void;
  total: number;
};

export function ProductGrid({ products, compareIds, onCompare, onAdd, onDetail, total }: Props) {
  const { t } = useTranslation();
  return (
    <section>
      <div className="mb-5 flex items-end justify-between border-b border-ink/10 pb-3">
        <div>
          <p className="eyebrow">{t("collection")}</p>
          <h2 className="mt-2 font-display text-[clamp(34px,4vw,54px)]">{t("essentials")}</h2>
        </div>
        <span className="font-mono text-[10px] text-muted">{total} {t("items")}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-9 md:grid-cols-3 lg:grid-cols-4 lg:gap-x-5 lg:gap-y-12">
        {products.map((product, index) => (
          <ProductCard key={product.article_id} product={product} index={index} selected={compareIds.includes(product.article_id)} onCompare={() => onCompare(product.article_id)} onAdd={() => onAdd(product.article_id)} onDetail={() => onDetail(product.article_id)} />
        ))}
      </div>
    </section>
  );
}
