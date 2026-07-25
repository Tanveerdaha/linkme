"use client";

type Option<T extends string> = { value: T; label: string; description?: string };

type VisibilitySelectorProps<T extends string> = {
  label: string;
  value: T;
  options: Option<T>[];
  onChange: (value: T) => void;
  disabled?: boolean;
};

export function VisibilitySelector<T extends string>({
  label,
  value,
  options,
  onChange,
  disabled,
}: VisibilitySelectorProps<T>) {
  return (
    <fieldset className="space-y-3">
      <legend className="text-sm font-medium text-foreground">{label}</legend>
      <div className="space-y-2">
        {options.map((opt) => (
          <label
            key={opt.value}
            className="flex cursor-pointer items-start gap-3 rounded-lg border border-transparent px-2 py-2 hover:bg-muted/40 has-[:checked]:border-border/70 has-[:checked]:bg-muted/30"
          >
            <input
              type="radio"
              className="mt-1"
              name={label}
              value={opt.value}
              checked={value === opt.value}
              disabled={disabled}
              onChange={() => onChange(opt.value)}
            />
            <span>
              <span className="block text-sm font-medium">{opt.label}</span>
              {opt.description ? (
                <span className="mt-0.5 block text-xs text-muted-foreground">
                  {opt.description}
                </span>
              ) : null}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
