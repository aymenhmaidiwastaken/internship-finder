"use client";

import { useState, useCallback } from "react";
import { SearchBar } from "@/components/search-bar";
import { Filters } from "@/components/filters";
import { InternshipCard } from "@/components/internship-card";
import { ResultsSkeleton } from "@/components/results-skeleton";
import { LanguageSwitcher } from "@/components/language-switcher";
import { searchInternships } from "@/lib/api";
import { useLocale } from "@/lib/locale-context";
import { Internship } from "@/types/internship";
import { SearchX } from "lucide-react";

export default function Home() {
  const { t } = useLocale();
  const [results, setResults] = useState<Internship[]>([]);
  const [total, setTotal] = useState(0);
  const [durationMs, setDurationMs] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState("");

  const [location, setLocation] = useState("");
  const [dateFilter, setDateFilter] = useState("all");
  const [remoteOnly, setRemoteOnly] = useState(false);

  const handleSearch = useCallback(
    async (query: string) => {
      setIsLoading(true);
      setError(null);
      setCurrentQuery(query);
      setHasSearched(true);
      try {
        const data = await searchInternships({
          query,
          location: location || undefined,
          remote_only: remoteOnly || undefined,
          date_filter: dateFilter !== "all" ? dateFilter : undefined,
        });
        setResults(data.results);
        setTotal(data.total);
        setDurationMs(data.duration_ms);
      } catch {
        setError(t("error.fetch"));
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    [location, dateFilter, remoteOnly, t]
  );

  return (
    <div className="flex flex-col flex-1">
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
          <span className="text-lg font-semibold tracking-tight">
            {t("app.title")}
          </span>
          <LanguageSwitcher />
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-5xl px-6">
        <section
          className={`flex flex-col items-center transition-all duration-500 ${
            hasSearched ? "pt-8 pb-6" : "pt-32 pb-16"
          }`}
        >
          {!hasSearched && (
            <div className="text-center mb-8 space-y-2">
              <h1 className="text-4xl font-bold tracking-tight">
                {t("hero.heading")}
              </h1>
              <p className="text-muted-foreground text-lg">
                {t("hero.subheading")}
              </p>
            </div>
          )}

          <SearchBar onSearch={handleSearch} isLoading={isLoading} />

          {hasSearched && (
            <div className="mt-4 w-full max-w-2xl">
              <Filters
                location={location}
                dateFilter={dateFilter}
                remoteOnly={remoteOnly}
                onLocationChange={setLocation}
                onDateFilterChange={setDateFilter}
                onRemoteOnlyChange={setRemoteOnly}
              />
            </div>
          )}
        </section>

        <section className="pb-16">
          {isLoading && <ResultsSkeleton />}

          {error && (
            <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
              {error}
            </div>
          )}

          {!isLoading && hasSearched && !error && (
            <>
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-muted-foreground">
                  <span className="text-foreground font-medium">{total}</span>{" "}
                  {total === 1 ? t("results.result") : t("results.results")}{" "}
                  {t("results.for")}{" "}
                  <span className="text-foreground font-medium">&ldquo;{currentQuery}&rdquo;</span>
                  <span className="ml-2 text-muted-foreground/70">
                    ({(durationMs / 1000).toFixed(2)}s)
                  </span>
                </p>
              </div>

              {results.length > 0 ? (
                <div className="space-y-3">
                  {results.map((internship) => (
                    <InternshipCard key={internship.id} internship={internship} />
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                  <SearchX className="h-12 w-12 mb-4 opacity-40" />
                  <p className="text-lg font-medium">{t("results.none.title")}</p>
                  <p className="text-sm mt-1">{t("results.none.subtitle")}</p>
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}
