"""Worker gratuito para GitHub Actions: reavalia vagas ainda não processadas."""

from __future__ import annotations

import os

from discovery import discover_all
from scoring import score_job


def main() -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Supabase não configurado; execução encerrada com segurança.")
        return

    from supabase import create_client

    client = create_client(url, key)
    existing_rows = client.table("jobs").select("url").execute().data
    existing_urls = {row.get("url") for row in existing_rows if row.get("url")}
    discovered = discover_all()
    inserted = 0
    for job in discovered:
        if not job.get("url") or job["url"] in existing_urls:
            continue
        result = score_job(job)
        status = "Aguardando aprovação" if result.decision in {"AUTOAPLICAR", "REVISAR"} else result.decision.title()
        client.table("jobs").insert({**job, **result.to_dict(), "status": status}).execute()
        existing_urls.add(job["url"])
        inserted += 1

    jobs = client.table("jobs").select("*").is_("score", "null").execute().data
    for job in jobs:
        result = score_job(job)
        status = "Aguardando aprovação" if result.decision in {"AUTOAPLICAR", "REVISAR"} else result.decision.title()
        client.table("jobs").update({**result.to_dict(), "status": status}).eq("id", job["id"]).execute()
    print(f"Busca concluída: {len(discovered)} encontrada(s), {inserted} nova(s) e {len(jobs)} reavaliada(s).")


if __name__ == "__main__":
    main()
