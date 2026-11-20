"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function TentarNovamente() {
  const router = useRouter();
  const [pendente, iniciar] = useTransition();

  return (
    <button
      type="button"
      disabled={pendente}
      onClick={() => iniciar(() => router.refresh())}
    >
      {pendente ? "Tentando..." : "Tentar novamente"}
    </button>
  );
}
