import { Search } from "lucide-react";
import { useTranslation } from "../i18n";
import type { ProductFacets, ProductQuery } from "../types";

type Props = { facets: ProductFacets | null; query: ProductQuery; onChange: (patch: Partial<ProductQuery>) => void };

export function BrowseControls({ facets, query, onChange }: Props) {
  const { t } = useTranslation();
  const css = "border border-ink/15 bg-paper px-3 py-2 text-xs";
  return <section id="collection" className="mb-8 grid gap-3 border-y border-ink/10 py-4 md:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr]">
    <label className="flex items-center gap-2 border border-ink/15 bg-paper px-3"><Search size={15} className="text-muted" /><input value={query.search || ""} onChange={e => onChange({ search: e.target.value, page: 1 })} placeholder={t("searchPlaceholder")} className="min-w-0 flex-1 bg-transparent py-2 text-xs outline-none" /></label>
    <select aria-label={t("category")} className={css} value={query.category || ""} onChange={e => onChange({ category: e.target.value, page: 1 })}><option value="">{t("allCategories")}</option>{facets?.categories.map(item => <option key={item}>{item}</option>)}</select>
    <select aria-label={t("color")} className={css} value={query.color || ""} onChange={e => onChange({ color: e.target.value, page: 1 })}><option value="">{t("allColors")}</option>{facets?.colors.map(item => <option key={item}>{item}</option>)}</select>
    <select aria-label={t("collectionLabel")} className={css} value={query.indexGroup || ""} onChange={e => onChange({ indexGroup: e.target.value, page: 1 })}><option value="">{t("allCollections")}</option>{facets?.index_groups.map(item => <option key={item}>{item}</option>)}</select>
    <select aria-label={t("sort")} className={css} value={query.sort || "popular"} onChange={e => onChange({ sort: e.target.value as ProductQuery["sort"], page: 1 })}><option value="popular">{t("popular")}</option><option value="name">{t("nameSort")}</option><option value="article_id">{t("idSort")}</option></select>
    <input aria-label={t("maxPrice")} className={css} type="number" step="0.001" min={facets?.price_range?.[0] || 0} max={facets?.price_range?.[1]} value={query.maxPrice ?? ""} onChange={e => onChange({ maxPrice: e.target.value ? Number(e.target.value) : undefined, page: 1 })} placeholder={t("maxPrice")} />
  </section>;
}
