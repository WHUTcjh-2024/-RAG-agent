import { X } from "lucide-react";
import type { Message, Slots, ToolTrace } from "../types";
import { ChatPanel } from "./ChatPanel";
import { InsightPanel } from "./InsightPanel";
import { useTranslation } from "../i18n";

type Props = { open: boolean; onClose: () => void; messages: Message[]; streaming: boolean; slots: Slots; traces: ToolTrace[]; onSubmit: (message: string, image: File | null, preview: string | null) => void };

export function StylistDrawer({ open, onClose, messages, streaming, slots, traces, onSubmit }: Props) {
  const { t } = useTranslation();
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50">
      <button onClick={onClose} className="absolute inset-0 bg-ink/30 backdrop-blur-[2px]" aria-label={t("close")} />
      <aside className="absolute right-0 top-0 h-full w-full max-w-[500px] overflow-y-auto bg-canvas shadow-2xl animate-slide-in">
        <div className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-ink/10 bg-canvas/95 px-5 backdrop-blur-md">
          <div><span className="eyebrow">{t("appointment")}</span><h2 className="mt-1 font-display text-xl">{t("stylist")}</h2></div>
          <button onClick={onClose} className="icon-button" aria-label={t("close")}><X size={18} /></button>
        </div>
        <div className="p-4"><ChatPanel messages={messages} streaming={streaming} onSubmit={onSubmit} /><InsightPanel slots={slots} traces={traces} /></div>
      </aside>
    </div>
  );
}
