import { Search } from "lucide-react";
import type { ProductFacets, ProductQuery } from "../types";

type Props = {
  facets: ProductFacets | null;
  query: ProductQuery;
  onChange: (patch: Partial<ProductQuery>) => void;
};

export function BrowseControls({ facets, query, onChange }: Props) {
  const selectClass = "border border-ink/15 bg-paper px-3 py-2 text-xs";
  return (
    <section id="collection" className="mb-8 grid gap-3 border-y border-ink/10 py-4 md:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr]">
      <label className="flex items-center gap-2 border border-ink/15 bg-paper px-3">
        <Search size={15} className="text-muted" />
        <input
          value={query.search || ""}
          onChange={(event) => onChange({ search: event.target.value, page: 1 })}
          placeholder="搜索商品名称或描述"
          className="min-w-0 flex-1 bg-transparent py-2 text-xs outline-none"
        />
      </label>
      <select aria-label="分类" className={selectClass} value={query.category || ""} onChange={(event) => onChange({ category: event.target.value, page: 1 })}>
        <option value="">全部分类</option>
        {facets?.categories.map((item) => <option key={item}>{item}</option>)}
      </select>
      <select aria-label="颜色" className={selectClass} value={query.color || ""} onChange={(event) => onChange({ color: event.target.value, page: 1 })}>
        <option value="">全部颜色</option>
        {facets?.colors.map((item) => <option key={item}>{item}</option>)}
      </select>
      <select aria-label="系列" className={selectClass} value={query.indexGroup || ""} onChange={(event) => onChange({ indexGroup: event.target.value, page: 1 })}>
        <option value="">全部系列</option>
        {facets?.index_groups.map((item) => <option key={item}>{item}</option>)}
      </select>
      <select aria-label="排序" className={selectClass} value={query.sort || "popular"} onChange={(event) => onChange({ sort: event.target.value as ProductQuery["sort"], page: 1 })}>
        <option value="popular">热度优先</option><option value="name">名称排序</option><option value="article_id">商品编号</option>
      </select>
      <input
        aria-label="最高数据集价格"
        className={selectClass}
        type="number"
        step="0.001"
        min={facets?.price_range?.[0] || 0}
        max={facets?.price_range?.[1]}
        value={query.maxPrice ?? ""}
        onChange={(event) => onChange({ maxPrice: event.target.value ? Number(event.target.value) : undefined, page: 1 })}
        placeholder="最高数据集价格"
      />
    </section>
  );
}
