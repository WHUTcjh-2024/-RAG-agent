import { useEffect, useState } from "react";
import { GitCompareArrows } from "lucide-react";
import { addCart, checkout, compareProducts, fetchProducts, removeCart, streamChat } from "./api/client";
import { CompareDrawer, CartDrawer } from "./components/Drawers";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { ProductGrid } from "./components/ProductGrid";
import { StylistDrawer } from "./components/StylistDrawer";
import { useAppStore } from "./store/useAppStore";

export default function App() {
  const store = useAppStore();
  const [cartOpen, setCartOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [stylistOpen, setStylistOpen] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    fetchProducts(12).then(store.setProducts).catch((error) => setNotice(error.message));
  }, []);

  const submit = async (message: string, image: File | null, preview: string | null) => {
    store.addMessage({ id: crypto.randomUUID(), role: "user", content: message || "查找类似图片", imagePreview: preview || undefined });
    store.setStreaming(true);
    setNotice("");
    try {
      await streamChat(message, store.sessionId, image, {
        onMeta: ({ slots }) => store.setSlots(slots),
        onTool: store.addTrace,
        onProducts: store.setProducts,
        onComparison: store.setComparison,
        onCart: store.setCart,
        onOrder: store.setOrder,
        onMessage: store.appendAssistant,
        onError: (text) => { throw new Error(text); }
      });
    } catch (error) {
      const text = error instanceof Error ? error.message : "请求失败";
      store.appendAssistant(`暂时无法完成请求：${text}`);
      setNotice(text);
    } finally {
      store.setStreaming(false);
    }
  };

  const add = async (id: string) => {
    try {
      const result = await addCart(store.sessionId, id);
      store.setCart(result.cart);
      setNotice("已加入购物袋");
    } catch (error) { setNotice(error instanceof Error ? error.message : "加购失败"); }
  };

  const openCompare = async () => {
    if (store.compareIds.length < 2) return;
    try {
      const result = await compareProducts(store.compareIds);
      store.setComparison(result.products);
      setCompareOpen(true);
    } catch (error) { setNotice(error instanceof Error ? error.message : "对比失败"); }
  };

  const doCheckout = async () => {
    const result = await checkout(store.sessionId);
    if (result.order) { store.setOrder(result.order); store.setCart([]); }
  };

  return (
    <div className="min-h-screen bg-paper text-ink">
      <Header cartCount={store.cart.length} onStylist={() => setStylistOpen(true)} onCart={() => { store.setOrder(null); setCartOpen(true); }} />
      <main>
        <Hero products={store.products} onStylist={() => setStylistOpen(true)} />
        <section className="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-10 lg:py-24">
          <ProductGrid products={store.products} compareIds={store.compareIds} onCompare={store.toggleCompare} onAdd={add} />
        </section>
      </main>

      {store.compareIds.length >= 2 && (
        <div className="fixed bottom-5 left-1/2 z-30 flex -translate-x-1/2 items-center gap-4 bg-ink px-5 py-3 text-white shadow-xl">
          <GitCompareArrows size={16} /><span className="text-xs">已选择 {store.compareIds.length} 件</span>
          <button onClick={openCompare} className="border-l border-white/20 pl-4 text-[11px] uppercase tracking-wider text-[#f2d6d0]">开始对比</button>
          <button onClick={store.clearCompare} className="text-[11px] text-white/55">清除</button>
        </div>
      )}
      {notice && <button onClick={() => setNotice("")} className="fixed bottom-5 right-5 z-40 bg-paper px-4 py-3 text-xs shadow-xl ring-1 ring-ink/10">{notice}</button>}
      <CartDrawer open={cartOpen} cart={store.cart} order={store.order} onClose={() => setCartOpen(false)} onRemove={async (id) => { const result = await removeCart(store.sessionId, id); store.setCart(result.cart); }} onCheckout={doCheckout} />
      <CompareDrawer open={compareOpen} products={store.comparison} onClose={() => setCompareOpen(false)} />
      <StylistDrawer open={stylistOpen} onClose={() => setStylistOpen(false)} messages={store.messages} streaming={store.streaming} slots={store.slots} traces={store.traces} onSubmit={submit} />
    </div>
  );
}
