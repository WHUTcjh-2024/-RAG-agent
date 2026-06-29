import { CheckCircle2, ChevronRight } from "lucide-react";
import type { Slots, ToolTrace } from "../types";

const labels: Record<string, string> = { color: "颜色", category: "品类", style: "风格", scenario: "场景", budget: "预算", avoid: "排除" };

export function InsightPanel({ slots, traces }: { slots: Slots; traces: ToolTrace[] }) {
  return (
    <aside className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-1">
      <div className="border-t border-ink/20 pt-4">
        <p className="eyebrow">Current brief</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.keys(slots).length ? Object.entries(slots).map(([key, value]) => (
            <span key={key} className="border border-ink/10 bg-paper px-2.5 py-1.5 text-[11px]">
              <span className="text-muted">{labels[key] || key}</span> · {Array.isArray(value) ? value.join(" / ") : String(value)}
            </span>
          )) : <p className="text-xs leading-5 text-muted">你的偏好会随对话逐步形成。</p>}
        </div>
      </div>
      <div className="border-t border-ink/20 pt-4">
        <p className="eyebrow">Service trace</p>
        <div className="mt-3 space-y-2">
          {traces.length ? traces.slice(-4).map((trace, index) => (
            <div key={`${trace.tool}-${index}`} className="flex items-center gap-2 text-[11px]">
              <CheckCircle2 size={13} className="text-[#56705c]" />
              <span className="min-w-0 flex-1 truncate">{trace.tool}</span>
              <ChevronRight size={12} className="text-muted" />
            </div>
          )) : <p className="text-xs leading-5 text-muted">检索和工具调用将在这里透明展示。</p>}
        </div>
      </div>
    </aside>
  );
}
