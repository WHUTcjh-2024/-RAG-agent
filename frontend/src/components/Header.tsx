import { useState } from "react";
import { Menu, MessageCircle, Search, ShoppingBag, X } from "lucide-react";

type Props = { cartCount: number; onCart: () => void; onStylist: () => void; onBrowse: (indexGroup?: string) => void };

export function Header({ cartCount, onCart, onStylist, onBrowse }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const links: [string, string | undefined][] = [["All products", undefined], ["Women", "Ladieswear"], ["Men", "Menswear"], ["Kids", "Baby/Children"]];
  return (
    <>
      <div className="overflow-hidden whitespace-nowrap bg-ink px-4 py-2 text-center text-[8px] uppercase tracking-[.18em] text-white sm:text-[9px] sm:tracking-[.22em]">
        Complimentary styling · Local curated edition
      </div>
      <header className="sticky top-0 z-40 border-b border-ink/10 bg-paper/95 backdrop-blur-md">
        <div className="mx-auto grid h-[72px] max-w-[1600px] grid-cols-[1fr_auto_1fr] items-center px-5 lg:px-10">
          <nav className="hidden items-center gap-7 lg:flex">
            {links.map(([item, group]) => (
              <button key={item} onClick={() => onBrowse(group)} className="nav-link">{item}</button>
            ))}
          </nav>
          <button onClick={() => setMenuOpen((value) => !value)} className="justify-self-start p-2 lg:hidden" aria-label="菜单">{menuOpen ? <X size={20} /> : <Menu size={20} />}</button>
          <div className="text-center">
            <div className="font-display text-[22px] tracking-[.28em]">ATELIER</div>
            <div className="mt-0.5 text-[7px] uppercase tracking-[.34em] text-muted">Objects of style</div>
          </div>
          <div className="flex items-center justify-end gap-1 sm:gap-2">
            <button onClick={() => onBrowse()} className="icon-button icon-button-hidden" aria-label="搜索"><Search size={18} strokeWidth={1.4} /></button>
            <button className="icon-button icon-button-hidden" onClick={onStylist} aria-label="打开私人顾问"><MessageCircle size={18} strokeWidth={1.4} /></button>
            <button className="icon-button relative" onClick={onCart} aria-label="打开购物袋">
              <ShoppingBag size={18} strokeWidth={1.4} />
              {cartCount > 0 && <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-accent px-1 text-[9px] text-white">{cartCount}</span>}
            </button>
          </div>
        </div>
        {menuOpen && <nav className="border-t border-ink/10 bg-paper px-5 py-4 lg:hidden">{links.map(([item, group]) => <button key={item} onClick={() => { onBrowse(group); setMenuOpen(false); }} className="block w-full border-b border-ink/10 py-3 text-left text-xs uppercase tracking-wider">{item}</button>)}</nav>}
      </header>
    </>
  );
}
