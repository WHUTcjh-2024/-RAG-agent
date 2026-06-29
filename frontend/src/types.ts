export interface Product {
  article_id: string;
  prod_name: string;
  product_type_name?: string;
  product_group_name?: string;
  colour_group_name?: string;
  garment_group_name?: string;
  detail_desc?: string;
  image_path?: string;
  image_url?: string;
  score?: number;
  reason?: string;
  text_score?: number;
  image_score?: number;
}

export interface ToolTrace {
  tool: string;
  input: Record<string, unknown>;
  summary: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  imagePreview?: string;
}

export interface Order {
  order_id: string;
  status: string;
  items: Product[];
}

export type Slots = Record<string, string | number | string[]>;
