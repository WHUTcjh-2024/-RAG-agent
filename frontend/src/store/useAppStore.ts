import { create } from "zustand";
import type { Message, Order, Product, Slots, ToolTrace } from "../types";

const sessionId =
  sessionStorage.getItem("atelier-session") || `web-${crypto.randomUUID()}`;
sessionStorage.setItem("atelier-session", sessionId);

type AppState = {
  sessionId: string;
  messages: Message[];
  products: Product[];
  traces: ToolTrace[];
  slots: Slots;
  cart: Product[];
  compareIds: string[];
  comparison: Product[];
  order: Order | null;
  streaming: boolean;
  addMessage: (message: Message) => void;
  appendAssistant: (delta: string) => void;
  setProducts: (products: Product[]) => void;
  addTrace: (trace: ToolTrace) => void;
  setSlots: (slots: Slots) => void;
  setCart: (cart: Product[]) => void;
  toggleCompare: (id: string) => void;
  setComparison: (products: Product[]) => void;
  clearCompare: () => void;
  setOrder: (order: Order | null) => void;
  setStreaming: (streaming: boolean) => void;
};

export const useAppStore = create<AppState>((set) => ({
  sessionId,
  messages: [],
  products: [],
  traces: [],
  slots: {},
  cart: [],
  compareIds: [],
  comparison: [],
  order: null,
  streaming: false,
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  appendAssistant: (delta) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages.at(-1);
      if (last?.role === "assistant") last.content += delta;
      else messages.push({ id: crypto.randomUUID(), role: "assistant", content: delta });
      return { messages };
    }),
  setProducts: (products) => set({ products }),
  addTrace: (trace) => set((state) => ({ traces: [...state.traces, trace].slice(-8) })),
  setSlots: (slots) => set({ slots }),
  setCart: (cart) => set({ cart }),
  toggleCompare: (id) =>
    set((state) => ({
      compareIds: state.compareIds.includes(id)
        ? state.compareIds.filter((item) => item !== id)
        : state.compareIds.length < 3
          ? [...state.compareIds, id]
          : state.compareIds
    })),
  setComparison: (comparison) => set({ comparison }),
  clearCompare: () => set({ compareIds: [], comparison: [] }),
  setOrder: (order) => set({ order }),
  setStreaming: (streaming) => set({ streaming })
}));
