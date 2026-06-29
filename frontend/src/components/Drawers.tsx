import { CheckCircle2, Minus, ShoppingBag, X } from "lucide-react";
import { productImage } from "../api/client";
import type { Order, Product } from "../types";
import { useTranslation } from "../i18n";

function Shell({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: React.ReactNode }) {
  const { t } = useTranslation();
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50">
      <button className="absolute inset-0 bg-ink/35 backdrop-blur-[2px]" onClick={onClose} aria-label={t("close")} />
      <div className="absolute right-0 top-0 flex h-full w-full max-w-xl flex-col bg-paper shadow-2xl animate-slide-in">
        <div className="flex h-16 items-center justify-between border-b border-ink/10 px-6">
          <h2 className="font-display text-2xl">{title}</h2>
          <button className="icon-button" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="scrollbar-thin flex-1 overflow-y-auto p-6">{children}</div>
      </div>
    </div>
  );
}

export function CartDrawer({ open, cart, order, onClose, onRemove, onCheckout }: { open: boolean; cart: Product[]; order: Order | null; onClose: () => void; onRemove: (id: string) => void; onCheckout: () => void }) {
  const { t } = useTranslation();
  return (
    <Shell open={open} title={t("cart")} onClose={onClose}>
      {order ? (
        <div className="grid h-full place-items-center text-center">
          <div>
            <CheckCircle2 size={44} strokeWidth={1.2} className="mx-auto text-[#56705c]" />
            <h3 className="mt-5 font-display text-3xl">{t("orderConfirmed")}</h3>
            <p className="mt-2 text-sm text-muted">{order.order_id}</p>
            <p className="mt-6 text-xs leading-5 text-muted">{t("demoOrder")}</p>
          </div>
        </div>
      ) : cart.length ? (
        <div className="flex h-full flex-col">
          <div className="flex-1 space-y-4">
            {cart.map((product) => (
              <div key={product.article_id} className="flex gap-4 border-b border-ink/10 pb-4">
                <img src={productImage(product)} className="h-28 w-24 bg-canvas object-cover" alt={product.prod_name} />
                <div className="min-w-0 flex-1 py-1">
                  <h3 className="text-sm font-medium">{product.prod_name}</h3>
                  <p className="mt-1 text-xs text-muted">{product.product_type_name} · {product.colour_group_name}</p>
                  <button onClick={() => onRemove(product.article_id)} className="mt-8 flex items-center gap-1 text-[11px] text-muted hover:text-accent"><Minus size={12} /> {t("remove")}</button>
                </div>
              </div>
            ))}
          </div>
          <button onClick={onCheckout} className="mt-6 w-full bg-ink px-5 py-4 text-xs uppercase tracking-[0.2em] text-white hover:bg-accent">{t("checkout")}</button>
        </div>
      ) : (
        <div className="grid h-full place-items-center text-center text-muted">
          <div><ShoppingBag size={36} strokeWidth={1.2} className="mx-auto" /><p className="mt-4 text-sm">{t("emptyCart")}</p></div>
        </div>
      )}
    </Shell>
  );
}

export function CompareDrawer({ open, products, onClose }: { open: boolean; products: Product[]; onClose: () => void }) {
  const { t } = useTranslation();
  return (
    <Shell open={open} title={t("compare")} onClose={onClose}>
      <div className="grid grid-cols-2 gap-4">
        {products.map((product) => (
          <div key={product.article_id}>
            <img src={productImage(product)} className="aspect-[3/4] w-full bg-canvas object-cover" alt={product.prod_name} />
            <h3 className="mt-3 text-sm font-medium">{product.prod_name}</h3>
            <dl className="mt-4 space-y-3 border-t border-ink/10 pt-3 text-xs">
              {[[t("category"), product.product_type_name], [t("color"), product.colour_group_name], [t("group"), product.garment_group_name]].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-3"><dt className="text-muted">{label}</dt><dd className="text-right">{value || '—'}</dd></div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </Shell>
  );
}

export function ProductDetailDrawer({ open, product, onClose, onAdd }: { open: boolean; product: Product | null; onClose: () => void; onAdd: (id: string) => void }) {
  const { t } = useTranslation();
  return (
    <Shell open={open} title={t("detail")} onClose={onClose}>
      {product && <div>
        <img src={productImage(product)} className="aspect-[3/4] w-full bg-canvas object-cover" alt={product.prod_name} />
        <p className="mt-5 font-mono text-[10px] text-muted">{product.article_id}</p>
        <h3 className="mt-2 font-display text-3xl">{product.prod_name}</h3>
        <p className="mt-3 text-xs text-muted">{product.product_type_name} · {product.colour_group_name} · {product.garment_group_name}</p>
        <p className="mt-6 text-sm leading-7">{product.detail_desc || t("noDescription")}</p>
        <dl className="mt-5 space-y-2 border-t border-ink/10 pt-4 text-xs">
          <div className="flex justify-between"><dt className="text-muted">SKU</dt><dd>{product.sku || product.article_id}</dd></div>
          <div className="flex justify-between"><dt className="text-muted">{t("inventory")}</dt><dd>{product.inventory_status === "unknown" ? t("unavailable") : product.inventory_status}</dd></div>
          <div className="flex justify-between"><dt className="text-muted">{t("sizes")}</dt><dd>{product.available_sizes?.length ? product.available_sizes.join(" / ") : t("unavailable")}</dd></div>
          {product.price_info && <div className="flex justify-between"><dt className="text-muted">{t("datasetPrice")}</dt><dd>{product.price_info.amount.toFixed(6)} {product.price_info.currency}</dd></div>}
        </dl>
        <button onClick={() => onAdd(product.article_id)} className="mt-8 w-full bg-accent px-5 py-4 text-xs uppercase tracking-[0.2em] text-white">{t("addCart")}</button>
      </div>}
    </Shell>
  );
}
