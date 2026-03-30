"use client";

import { MapPin, Clock, Wifi } from "lucide-react";
import { useLocale } from "@/lib/locale-context";

interface FiltersProps {
  location: string;
  dateFilter: string;
  remoteOnly: boolean;
  onLocationChange: (v: string) => void;
  onDateFilterChange: (v: string) => void;
  onRemoteOnlyChange: (v: boolean) => void;
}

export function Filters({
  location,
  dateFilter,
  remoteOnly,
  onLocationChange,
  onDateFilterChange,
  onRemoteOnlyChange,
}: FiltersProps) {
  const { t } = useLocale();

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative">
        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={location}
          onChange={(e) => onLocationChange(e.target.value)}
          placeholder={t("filter.location")}
          className="h-10 rounded-lg border border-border bg-card pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/50 w-44"
        />
      </div>

      <div className="relative">
        <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <select
          value={dateFilter}
          onChange={(e) => onDateFilterChange(e.target.value)}
          className="h-10 rounded-lg border border-border bg-card pl-9 pr-8 text-sm text-foreground appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring/50"
        >
          <option value="all">{t("filter.anytime")}</option>
          <option value="24h">{t("filter.24h")}</option>
          <option value="7d">{t("filter.7d")}</option>
          <option value="30d">{t("filter.30d")}</option>
        </select>
      </div>

      <button
        onClick={() => onRemoteOnlyChange(!remoteOnly)}
        className={`flex items-center gap-2 h-10 rounded-lg border px-4 text-sm font-medium transition-colors ${
          remoteOnly
            ? "border-primary bg-primary text-primary-foreground"
            : "border-border bg-card text-muted-foreground hover:text-foreground"
        }`}
      >
        <Wifi className="h-4 w-4" />
        {t("filter.remote")}
      </button>
    </div>
  );
}
