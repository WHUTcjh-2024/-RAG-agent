import type { Order, Product, ProductFacets, ProductPage, ProductQuery, Slots, ToolTrace } from "../types";

export const productImage = (product: Product): string => {
  if (product.image_url) return product.image_url;
  const path = (product.image_path || "").replaceAll("\\", "/");
  return path ? `/media/${path.replace(/^images\//, "")}` : "";
};

async function ensureOk(response: Response): Promise<Response> {
  if (response.ok) return response;
  let detail = `请求失败 (${response.status})`;
  try {
    const payload = await response.json();
    detail = payload.detail || detail;
  } catch {
    // Keep the HTTP fallback message.
  }
  throw new Error(detail);
}

export function buildProductQuery(query: ProductQuery = {}): string {
  const params = new URLSearchParams({
    page: String(query.page || 1),
    page_size: String(query.pageSize || 12),
    sort: query.sort || "popular"
  });
  if (query.search) params.set("search", query.search);
  if (query.category) params.set("category", query.category);
  if (query.color) params.set("color", query.color);
  if (query.indexGroup) params.set("index_group", query.indexGroup);
  if (typeof query.maxPrice === "number") params.set("max_price", String(query.maxPrice));
  return params.toString();
}

export async function fetchProducts(query: ProductQuery = {}): Promise<ProductPage> {
  const params = buildProductQuery(query);
  const response = await ensureOk(await fetch(`/api/products?${params}`));
  return response.json();
}

export async function fetchProduct(id: string): Promise<Product> {
  return (await ensureOk(await fetch(`/api/products/${encodeURIComponent(id)}`))).json();
}

export async function fetchFacets(): Promise<ProductFacets> {
  return (await ensureOk(await fetch("/api/products/facets"))).json();
}

type StreamHandlers = {
  onMeta: (payload: { session_id: string; intent: string; slots: Slots }) => void;
  onTool: (payload: ToolTrace) => void;
  onProducts: (products: Product[]) => void;
  onComparison: (products: Product[]) => void;
  onCart: (products: Product[]) => void;
  onOrder: (order: Order) => void;
  onMessage: (delta: string) => void;
  onError: (message: string) => void;
};

export async function streamChat(
  message: string,
  sessionId: string,
  image: File | null,
  handlers: StreamHandlers
): Promise<void> {
  const form = new FormData();
  form.append("message", message);
  form.append("session_id", sessionId);
  if (image) form.append("file", image);
  const response = await ensureOk(
    await fetch("/api/chat/stream", { method: "POST", body: form })
  );
  if (!response.body) throw new Error("浏览器不支持流式响应");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      let event = "message";
      let data = "{}";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      const payload = JSON.parse(data);
      if (event === "meta") handlers.onMeta(payload);
      if (event === "tool") handlers.onTool(payload);
      if (event === "products") handlers.onProducts(payload.items);
      if (event === "comparison") handlers.onComparison(payload.items);
      if (event === "cart") handlers.onCart(payload.items);
      if (event === "order") handlers.onOrder(payload);
      if (event === "message") handlers.onMessage(payload.delta || "");
      if (event === "error") handlers.onError(payload.message || "处理失败");
    }
    if (done) break;
  }
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await ensureOk(
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })
  );
  return response.json();
}

export const compareProducts = (productIds: string[]) =>
  postJson<{ products: Product[] }>("/api/compare", { product_ids: productIds });

export const addCart = (sessionId: string, productId: string) =>
  postJson<{ cart: Product[] }>("/api/cart/add", {
    session_id: sessionId,
    product_id: productId
  });

export const removeCart = (sessionId: string, productId: string) =>
  postJson<{ cart: Product[] }>("/api/cart/remove", {
    session_id: sessionId,
    product_id: productId
  });

export const fetchSession = (sessionId: string) =>
  postJson<{ session_id: string; slots: Slots; cart: Product[]; history: { role: "user" | "assistant"; content: string }[] }>("/api/session", {
    session_id: sessionId
  });

export const checkout = (sessionId: string) =>
  postJson<{ success: boolean; message: string; order: Order | null }>("/api/checkout", {
    session_id: sessionId
  });
