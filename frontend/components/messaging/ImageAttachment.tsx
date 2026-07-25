"use client";

type ImageAttachmentProps = {
  src: string;
  alt?: string;
};

export function ImageAttachment({ src, alt = "Image attachment" }: ImageAttachmentProps) {
  return (
    <a
      href={src}
      target="_blank"
      rel="noopener noreferrer"
      className="block overflow-hidden rounded-xl border border-border/60 transition-opacity hover:opacity-90"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} className="max-h-64 max-w-full object-cover" />
    </a>
  );
}
