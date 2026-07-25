"use client";

import { Button } from "@/components/ui/button";

type FilterField = {
  key: string;
  label: string;
  type?: "text" | "select";
  options?: { value: string; label: string }[];
  placeholder?: string;
};

type FilterBarProps = {
  fields: FilterField[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onApply: () => void;
  onClear: () => void;
};

export function FilterBar({ fields, values, onChange, onApply, onClear }: FilterBarProps) {
  return (
    <div className="mb-4 flex flex-wrap items-end gap-3 rounded-xl border border-border/60 bg-muted/20 p-3">
      {fields.map((field) => (
        <label key={field.key} className="flex min-w-[140px] flex-1 flex-col gap-1 text-xs">
          <span className="text-muted-foreground">{field.label}</span>
          {field.type === "select" ? (
            <select
              className="h-9 rounded-lg border border-border bg-background px-2 text-sm"
              value={values[field.key] || ""}
              onChange={(e) => onChange(field.key, e.target.value)}
            >
              <option value="">All</option>
              {(field.options || []).map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              className="h-9 rounded-lg border border-border bg-background px-2 text-sm"
              placeholder={field.placeholder}
              value={values[field.key] || ""}
              onChange={(e) => onChange(field.key, e.target.value)}
            />
          )}
        </label>
      ))}
      <div className="flex gap-2">
        <Button size="sm" onClick={onApply}>
          Apply
        </Button>
        <Button size="sm" variant="outline" onClick={onClear}>
          Clear
        </Button>
      </div>
    </div>
  );
}
