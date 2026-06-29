import { CheckCircle2, ChevronRight } from "lucide-react";
import type { Slots, ToolTrace } from "../types";
import { useTranslation } from "../i18n";

export function InsightPanel({ slots, traces }: { slots: Slots; traces: ToolTrace[] }) {
  const { language, t } = useTranslation();
  const labels: Record<string, string> = language === "zh" ? { color: "颜色", category: "品类", style: "风格", scenario: "场景", budget: "预算", avoid: "排除" } : { color: "Color", category: "Category", style: "Style", scenario: "Occasion", budget: "Budget", avoid: "Exclude" };
  return (
    <aside className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-1">
      <div className="border-t border-ink/20 pt-4">
        <p className="eyebrow">{t("currentBrief")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.keys(slots).length ? Object.entries(slots).map(([key, value]) => (
            <span key={key} className="border border-ink/10 bg-paper px-2.5 py-1.5 text-[11px]">
              <span className="text-muted">{labels[key] || key}</span> · {Array.isArray(value) ? value.join(" / ") : String(value)}
            </span>
          )) : <p className="text-xs leading-5 text-muted">{t("preferenceHint")}</p>}
        </div>
      </div>
      <div className="border-t border-ink/20 pt-4">
        <p className="eyebrow">{t("trace")}</p>
        <div className="mt-3 space-y-2">
          {traces.length ? traces.slice(-4).map((trace, index) => (
            <div key={`${trace.tool}-${index}`} className="flex items-center gap-2 text-[11px]">
              <CheckCircle2 size={13} className="text-[#56705c]" />
              <span className="min-w-0 flex-1 truncate">{trace.tool}</span>
              <ChevronRight size={12} className="text-muted" />
            </div>
          )) : <p className="text-xs leading-5 text-muted">{t("traceHint")}</p>}
        </div>
      </div>
    </aside>
  );
}
