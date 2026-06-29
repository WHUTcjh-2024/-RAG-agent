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
  price?: number | null;
  popularity_score?: number;
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

export interface ProductPage {
  page: number;
  page_size: number;
  total: number;
  items: Product[];
}

export interface ProductFacets {
  categories: string[];
  colors: string[];
  index_groups: string[];
  price_range: [number, number] | null;
}

export interface ProductQuery {
  page?: number;
  pageSize?: number;
  search?: string;
  category?: string;
  color?: string;
  indexGroup?: string;
  maxPrice?: number;
  sort?: "article_id" | "name" | "popular";
}
