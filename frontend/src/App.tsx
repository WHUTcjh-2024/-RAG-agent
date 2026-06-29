import { useEffect, useState } from "react";
import { GitCompareArrows } from "lucide-react";
import { addCart, checkout, compareProducts, fetchFacets, fetchProduct, fetchProducts, fetchSession, removeCart, streamChat } from "./api/client";
import { CompareDrawer, CartDrawer, ProductDetailDrawer } from "./components/Drawers";
import { BrowseControls } from "./components/BrowseControls";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { ProductGrid } from "./components/ProductGrid";
import { StylistDrawer } from "./components/StylistDrawer";
import { useAppStore } from "./store/useAppStore";
import type { Product, ProductFacets, ProductQuery } from "./types";
import { useTranslation } from "./i18n";

export default function App() {
  const { language, t } = useTranslation();
  const store = useAppStore();
  const [cartOpen, setCartOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [stylistOpen, setStylistOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState<ProductQuery>({ page: 1, pageSize: 12, sort: "popular" });
  const [facets, setFacets] = useState<ProductFacets | null>(null);
  const [total, setTotal] = useState(0);
  const [detail, setDetail] = useState<Product | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchFacets().then(setFacets).catch((error) => setNotice(error.message));
    fetchSession(store.sessionId).then((session) => {
      store.setCart(session.cart);
      store.setSlots(session.slots);
      store.setMessages(session.history.map((item) => ({ ...item, id: crypto.randomUUID() })));
    }).catch((error) => setNotice(error.message));
  }, []);

  useEffect(() => {
    setLoading(true);
    const timer = window.setTimeout(() => {
      fetchProducts(query)
        .then((page) => { store.setProducts(page.items); setTotal(page.total); })
        .catch((error) => setNotice(error.message))
        .finally(() => setLoading(false));
    }, query.search ? 250 : 0);
    return () => window.clearTimeout(timer);
  }, [query]);

  const browse = (indexGroup?: string) => {
    setQuery((current) => ({ ...current, indexGroup: indexGroup || "", page: 1 }));
    window.setTimeout(() => document.getElementById("collection")?.scrollIntoView({ behavior: "smooth" }), 0);
  };

  const showDetail = async (id: string) => {
    try { setDetail(await fetchProduct(id)); }
    catch (error) { setNotice(error instanceof Error ? error.message : t("detailFailed")); }
  };

  const submit = async (message: string, image: File | null, preview: string | null) => {
    store.addMessage({ id: crypto.randomUUID(), role: "user", content: message || t("similarImage"), imagePreview: preview || undefined });
    store.setStreaming(true);
    setNotice("");
    try {
      await streamChat(message, store.sessionId, image, language, {
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
      const text = error instanceof Error ? error.message : t("requestFailed");
      store.appendAssistant(`${t("unable")}${text}`);
      setNotice(text);
    } finally {
      store.setStreaming(false);
    }
  };

  const add = async (id: string) => {
    try {
      const result = await addCart(store.sessionId, id);
      store.setCart(result.cart);
      setNotice(t("added"));
    } catch (error) { setNotice(error instanceof Error ? error.message : t("addFailed")); }
  };

  const openCompare = async () => {
    if (store.compareIds.length < 2) return;
    try {
      const result = await compareProducts(store.compareIds);
      store.setComparison(result.products);
      setCompareOpen(true);
    } catch (error) { setNotice(error instanceof Error ? error.message : t("compareFailed")); }
  };

  const doCheckout = async () => {
    try {
      const result = await checkout(store.sessionId);
      if (result.order) { store.setOrder(result.order); store.setCart([]); }
      else setNotice(result.message);
    } catch (error) { setNotice(error instanceof Error ? error.message : t("checkoutFailed")); }
  };

  return (
    <div className="min-h-screen bg-paper text-ink">
      <Header cartCount={store.cart.length} onStylist={() => setStylistOpen(true)} onBrowse={browse} onCart={() => { store.setOrder(null); setCartOpen(true); }} />
      <main>
        <Hero products={store.products} total={total} onStylist={() => setStylistOpen(true)} />
        <section className="mx-auto max-w-[1600px] px-4 py-16 sm:px-6 lg:px-10 lg:py-24">
          <BrowseControls facets={facets} query={query} onChange={(patch) => setQuery((current) => ({ ...current, ...patch }))} />
          {loading && <p className="mb-4 text-xs text-muted">{t("loading")}</p>}
          <ProductGrid products={store.products} total={total} compareIds={store.compareIds} onCompare={store.toggleCompare} onAdd={add} onDetail={showDetail} />
          {total > (query.pageSize || 12) && <div className="mt-12 flex items-center justify-center gap-4 text-xs">
            <button disabled={(query.page || 1) <= 1} onClick={() => setQuery((current) => ({ ...current, page: (current.page || 1) - 1 }))} className="border border-ink/15 px-4 py-2 disabled:opacity-30">{t("previous")}</button>
            <span>{t("page", { current: query.page || 1, total: Math.ceil(total / (query.pageSize || 12)) })}</span>
            <button disabled={(query.page || 1) >= Math.ceil(total / (query.pageSize || 12))} onClick={() => setQuery((current) => ({ ...current, page: (current.page || 1) + 1 }))} className="border border-ink/15 px-4 py-2 disabled:opacity-30">{t("next")}</button>
          </div>}
        </section>
      </main>

      {store.compareIds.length >= 2 && (
        <div className="fixed bottom-5 left-1/2 z-30 flex -translate-x-1/2 items-center gap-4 bg-ink px-5 py-3 text-white shadow-xl">
          <GitCompareArrows size={16} /><span className="text-xs">{t("selected", { count: store.compareIds.length })}</span>
          <button onClick={openCompare} className="border-l border-white/20 pl-4 text-[11px] uppercase tracking-wider text-[#f2d6d0]">{t("compareStart")}</button>
          <button onClick={store.clearCompare} className="text-[11px] text-white/55">{t("clear")}</button>
        </div>
      )}
      {notice && <button onClick={() => setNotice("")} className="fixed bottom-5 right-5 z-40 bg-paper px-4 py-3 text-xs shadow-xl ring-1 ring-ink/10">{notice}</button>}
      <CartDrawer open={cartOpen} cart={store.cart} order={store.order} onClose={() => setCartOpen(false)} onRemove={async (id) => { try { const result = await removeCart(store.sessionId, id); store.setCart(result.cart); } catch (error) { setNotice(error instanceof Error ? error.message : t("removeFailed")); } }} onCheckout={doCheckout} />
      <CompareDrawer open={compareOpen} products={store.comparison} onClose={() => setCompareOpen(false)} />
      <ProductDetailDrawer open={Boolean(detail)} product={detail} onClose={() => setDetail(null)} onAdd={add} />
      <StylistDrawer open={stylistOpen} onClose={() => setStylistOpen(false)} messages={store.messages} streaming={store.streaming} slots={store.slots} traces={store.traces} onSubmit={submit} />
    </div>
  );
}
