export interface Internship {
  id: string;
  title: string;
  company: string;
  location: string;
  date_posted: string;
  url: string;
  source: string;
  description: string;
  salary?: string;
  duration?: string;
  remote?: boolean;
}

export interface SearchRequest {
  query: string;
  location?: string;
  remote_only?: boolean;
  date_filter?: "24h" | "7d" | "30d" | "all";
  page?: number;
}

export interface SearchResponse {
  results: Internship[];
  total: number;
  query: string;
  duration_ms: number;
}

export interface SuggestionResponse {
  suggestions: string[];
}
