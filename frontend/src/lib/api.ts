import { SearchResponse, SuggestionResponse } from "@/types/internship";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export async function getSuggestions(query: string, locale: string = "en"): Promise<SuggestionResponse> {
  const res = await fetch(`${API_BASE}/api/suggestions?q=${encodeURIComponent(query)}&locale=${locale}`);
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  return res.json();
}

export async function searchInternships(params: {
  query: string;
  location?: string;
  remote_only?: boolean;
  date_filter?: string;
  page?: number;
}): Promise<SearchResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("query", params.query);
  if (params.location) searchParams.set("location", params.location);
  if (params.remote_only) searchParams.set("remote_only", "true");
  if (params.date_filter) searchParams.set("date_filter", params.date_filter);
  if (params.page) searchParams.set("page", String(params.page));

  const res = await fetch(`${API_BASE}/api/search?${searchParams.toString()}`);
  if (!res.ok) throw new Error("Failed to search internships");
  return res.json();
}
