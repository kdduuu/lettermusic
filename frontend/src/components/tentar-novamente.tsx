"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import controles from "./controles.module.css";

export function TentarNovamente() {
  const router = useRouter();
  const [pendente, iniciar] = useTransition();

  return (
    <button
      type="button"
      className={controles.retry}
      disabled={pendente}
      onClick={() => iniciar(() => router.refresh())}
    >
      {pendente ? "Tentando..." : "Tentar novamente"}
    </button>
  );
}
