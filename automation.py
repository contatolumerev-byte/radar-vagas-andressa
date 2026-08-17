"""Worker gratuito para GitHub Actions: reavalia vagas ainda não processadas."""

from __future__ import annotations

import os

from scoring import score_job


def main() -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Supabase não configurado; execução encerrada com segurança.")
        return

    from supabase import create_client

    client = create_client(url, key)
    jobs = client.table("jobs").select("*").is_("score", "null").execute().data
    for job in jobs:
        result = score_job(job)
        status = "Na fila" if result.decision in {"AUTOAPLICAR", "REVISAR"} else result.decision.title()
        client.table("jobs").update({**result.to_dict(), "status": status}).eq("id", job["id"]).execute()
    print(f"Triagem concluída: {len(jobs)} vaga(s) processada(s).")


if __name__ == "__main__":
    main()
