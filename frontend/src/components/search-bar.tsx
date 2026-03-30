"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Loader2 } from "lucide-react";
import { getSuggestions } from "@/lib/api";
import { useLocale } from "@/lib/locale-context";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const { t, locale } = useLocale();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const data = await getSuggestions(q, locale);
      setSuggestions(data.suggestions);
      setShowSuggestions(true);
    } catch {
      setSuggestions([]);
    }
  }, [locale]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(query), 200);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, fetchSuggestions]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (value?: string) => {
    const q = value || query;
    if (!q.trim()) return;
    setShowSuggestions(false);
    onSearch(q.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        setQuery(suggestions[selectedIndex]);
        handleSubmit(suggestions[selectedIndex]);
      } else {
        handleSubmit();
      }
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-2xl">
      <div className="relative flex items-center">
        <Search className="absolute left-4 h-5 w-5 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelectedIndex(-1);
          }}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          onKeyDown={handleKeyDown}
          placeholder={t("search.placeholder")}
          className="h-14 w-full rounded-xl border border-border bg-card pl-12 pr-32 text-base text-foreground placeholder:text-muted-foreground placeholder:truncate focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all"
        />
        <button
          onClick={() => handleSubmit()}
          disabled={isLoading || !query.trim()}
          className="absolute right-2 h-10 shrink-0 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : t("search.button")}
        </button>
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 mt-2 w-full rounded-xl border border-border bg-card shadow-lg overflow-hidden">
          {suggestions.map((s, i) => (
            <button
              key={s}
              className={`w-full px-4 py-3 text-left text-sm transition-colors hover:bg-accent ${
                i === selectedIndex ? "bg-accent" : ""
              }`}
              onMouseDown={() => {
                setQuery(s);
                handleSubmit(s);
              }}
              onMouseEnter={() => setSelectedIndex(i)}
            >
              <Search className="inline h-3.5 w-3.5 mr-2 text-muted-foreground" />
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
