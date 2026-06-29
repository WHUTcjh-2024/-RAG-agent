import type { Order, Product, Slots, ToolTrace } from "../types";

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

export async function fetchProducts(pageSize = 8): Promise<Product[]> {
  const params = new URLSearchParams({
    page: "1",
    page_size: String(pageSize),
    group: "Garment",
    index_group: "Ladieswear"
  });
  const response = await ensureOk(await fetch(`/api/products?${params}`));
  const payload = await response.json();
  return payload.items;
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

export const checkout = (sessionId: string) =>
  postJson<{ success: boolean; message: string; order: Order | null }>("/api/checkout", {
    session_id: sessionId
  });
