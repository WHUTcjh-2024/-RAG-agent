import { Menu, MessageCircle, Search, ShoppingBag } from "lucide-react";

type Props = { cartCount: number; onCart: () => void; onStylist: () => void };

export function Header({ cartCount, onCart, onStylist }: Props) {
  return (
    <>
      <div className="overflow-hidden whitespace-nowrap bg-ink px-4 py-2 text-center text-[8px] uppercase tracking-[.18em] text-white sm:text-[9px] sm:tracking-[.22em]">
        Complimentary styling · Local curated edition
      </div>
      <header className="sticky top-0 z-40 border-b border-ink/10 bg-paper/95 backdrop-blur-md">
        <div className="mx-auto grid h-[72px] max-w-[1600px] grid-cols-[1fr_auto_1fr] items-center px-5 lg:px-10">
          <nav className="hidden items-center gap-7 lg:flex">
            {['New arrivals', 'Women', 'Essentials', 'The edit'].map((item) => (
              <button key={item} className="nav-link">{item}</button>
            ))}
          </nav>
          <button className="justify-self-start p-2 lg:hidden" aria-label="菜单"><Menu size={20} strokeWidth={1.4} /></button>
          <div className="text-center">
            <div className="font-display text-[22px] tracking-[.28em]">ATELIER</div>
            <div className="mt-0.5 text-[7px] uppercase tracking-[.34em] text-muted">Objects of style</div>
          </div>
          <div className="flex items-center justify-end gap-1 sm:gap-2">
            <button className="icon-button icon-button-hidden" aria-label="搜索"><Search size={18} strokeWidth={1.4} /></button>
            <button className="icon-button icon-button-hidden" onClick={onStylist} aria-label="打开私人顾问"><MessageCircle size={18} strokeWidth={1.4} /></button>
            <button className="icon-button relative" onClick={onCart} aria-label="打开购物袋">
              <ShoppingBag size={18} strokeWidth={1.4} />
              {cartCount > 0 && <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-accent px-1 text-[9px] text-white">{cartCount}</span>}
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
