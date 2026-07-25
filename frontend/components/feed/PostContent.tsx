"use client";

type PostContentProps = {
  content: string;
};

export function PostContent({ content }: PostContentProps) {
  if (!content) return null;
  return (
    <p className="mt-2 whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
      {content}
    </p>
  );
}
