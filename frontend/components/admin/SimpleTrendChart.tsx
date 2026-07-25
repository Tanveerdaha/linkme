"use client";

type TrendPoint = { date: string; count: number };

type SimpleTrendChartProps = {
  title: string;
  data: TrendPoint[];
};

export function SimpleTrendChart({ title, data }: SimpleTrendChartProps) {
  const max = Math.max(1, ...data.map((d) => d.count));

  return (
    <div className="rounded-xl border border-border/60 bg-card/80 p-4">
      <h3 className="mb-3 text-sm font-medium">{title}</h3>
      <div className="flex h-32 items-end gap-1">
        {data.map((point) => (
          <div key={point.date} className="group relative flex flex-1 flex-col items-center justify-end">
            <div
              className="w-full rounded-t bg-primary/70 transition-colors group-hover:bg-primary"
              style={{ height: `${(point.count / max) * 100}%`, minHeight: point.count ? 4 : 0 }}
              title={`${point.date}: ${point.count}`}
            />
          </div>
        ))}
      </div>
      <div className="mt-2 flex justify-between text-[10px] text-muted-foreground">
        <span>{data[0]?.date?.slice(5)}</span>
        <span>{data[data.length - 1]?.date?.slice(5)}</span>
      </div>
    </div>
  );
}
