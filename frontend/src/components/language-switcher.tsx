"use client";

import { useLocale } from "@/lib/locale-context";
import { languages, type Locale } from "@/lib/i18n";
import { Globe } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export function LanguageSwitcher() {
  const { locale, setLocale } = useLocale();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const current = languages.find((l) => l.code === locale);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 h-9 rounded-lg border border-border bg-card px-3 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <Globe className="h-4 w-4" />
        <span>{current?.label}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 z-50 rounded-lg border border-border bg-card shadow-lg overflow-hidden min-w-[140px]">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLocale(lang.code as Locale);
                setOpen(false);
              }}
              className={`w-full px-4 py-2.5 text-left text-sm transition-colors hover:bg-accent ${
                locale === lang.code ? "text-foreground font-medium" : "text-muted-foreground"
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
