"use client";

import { Internship } from "@/types/internship";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { MapPin, Calendar, Building2, ExternalLink, Wifi } from "lucide-react";
import { useLocale } from "@/lib/locale-context";

interface InternshipCardProps {
  internship: Internship;
}

export function InternshipCard({ internship }: InternshipCardProps) {
  const { t } = useLocale();

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      if (diffDays === 0) return t("card.today");
      if (diffDays === 1) return t("card.yesterday");
      if (diffDays < 7) return t("card.daysAgo", { n: diffDays });
      if (diffDays < 30) return t("card.weeksAgo", { n: Math.floor(diffDays / 7) });
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch {
      return dateStr;
    }
  };

  return (
    <Card className="group border-border/50 bg-card hover:border-border transition-all duration-200 hover:shadow-sm">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0 space-y-3">
            <div>
              <h3 className="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                {internship.title}
              </h3>
              <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
                <Building2 className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{internship.company}</span>
              </div>
            </div>

            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
              {internship.description}
            </p>

            <div className="flex flex-wrap items-center gap-2">
              {internship.location && (
                <Badge variant="secondary" className="font-normal text-xs gap-1">
                  <MapPin className="h-3 w-3" />
                  {internship.location}
                </Badge>
              )}
              {internship.remote && (
                <Badge variant="secondary" className="font-normal text-xs gap-1">
                  <Wifi className="h-3 w-3" />
                  {t("filter.remote")}
                </Badge>
              )}
              {internship.salary && (
                <Badge variant="secondary" className="font-normal text-xs">
                  {internship.salary}
                </Badge>
              )}
              {internship.duration && (
                <Badge variant="secondary" className="font-normal text-xs">
                  {internship.duration}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex flex-col items-end gap-2 shrink-0">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {formatDate(internship.date_posted)}
            </div>
            <Badge variant="outline" className="text-xs font-normal">
              {internship.source}
            </Badge>
            <a
              href={internship.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 mt-1"
            >
              {t("card.apply")} <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
