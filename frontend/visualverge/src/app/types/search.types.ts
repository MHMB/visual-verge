export interface PriceFilter {
  min_price: number;
  max_price: number;
  currency: string;
}

export interface SearchFilters {
  price: PriceFilter;
  region: string[];
  sizes: string[];
  color_names: string[];
  gender_name: string[];
  category_name: string[];
  brand_name: string[];
}

export interface SearchRequest {
  text_query: string;
  filters: SearchFilters;
  limit: number;
}
