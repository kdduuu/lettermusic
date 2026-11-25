"use client";

import Image from "next/image";
import { useState } from "react";

type CapaAlbumProps = {
  url: string | null;
  titulo: string;
  className: string;
};

export function CapaAlbum({ url, titulo, className }: CapaAlbumProps) {
  const [falhaImagem, setFalhaImagem] = useState(false);

  if (!url || falhaImagem) {
    return (
      <div className={className} role="img" aria-label={`Cover unavailable: ${titulo}`}>
        ♪
      </div>
    );
  }

  return (
    <div className={className}>
      <Image
        src={url}
        alt={`Cover of ${titulo}`}
        fill
        sizes="(max-width: 700px) 100vw, 340px"
        unoptimized
        onError={() => setFalhaImagem(true)}
      />
    </div>
  );
}