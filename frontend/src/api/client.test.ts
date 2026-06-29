import { describe, expect, it } from "vitest";
import { buildProductQuery } from "./client";

describe("buildProductQuery", () => {
  it("serializes browsing filters and pagination", () => {
    const query = new URLSearchParams(buildProductQuery({
      page: 3,
      pageSize: 24,
      search: "linen shirt",
      category: "Shirt",
      color: "White",
      indexGroup: "Ladieswear",
      maxPrice: 0.06,
      sort: "name"
    }));
    expect(Object.fromEntries(query)).toEqual({
      page: "3",
      page_size: "24",
      sort: "name",
      search: "linen shirt",
      category: "Shirt",
      color: "White",
      index_group: "Ladieswear",
      max_price: "0.06"
    });
  });

  it("uses stable defaults", () => {
    expect(Object.fromEntries(new URLSearchParams(buildProductQuery()))).toEqual({
      page: "1",
      page_size: "12",
      sort: "popular"
    });
  });
});
