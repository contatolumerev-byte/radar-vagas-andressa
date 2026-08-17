"""Persistência: Supabase quando configurado, sessão do Streamlit caso contrário."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from scoring import score_job


DEMO_JOBS = [
    {
        "id": "demo-1",
        "title": "Analista de Customer Success",
        "company": "Startup Exemplo",
        "location": "Remoto - Brasil",
        "work_mode": "Remoto",
        "salary_min": 3200,
        "description": "Onboarding, relacionamento, retenção e gestão da carteira de clientes via CRM.",
        "url": "",
        "status": "Nova",
        "created_at": "2026-08-17T09:00:00+00:00",
    },
    {
        "id": "demo-2",
        "title": "Assistente Comercial",
        "company": "Empresa Local",
        "location": "Fortaleza, CE",
        "work_mode": "Presencial",
        "salary_min": 2700,
        "description": "Atendimento inbound, propostas e pós-venda de segunda a sexta.",
        "url": "",
        "status": "Nova",
        "created_at": "2026-08-17T10:00:00+00:00",
    },
    {
        "id": "demo-3",
        "title": "Consultora Comercial Hunter",
        "company": "Vendas Externas Ltda.",
        "location": "Fortaleza, CE",
        "work_mode": "Externo",
        "salary_min": 2500,
        "description": "Hunting, cold call e visitas porta a porta em escala 6x1.",
        "url": "",
        "status": "Nova",
        "created_at": "2026-08-17T11:00:00+00:00",
    },
]


def _supabase_client():
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_SECRET_KEY") or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            return None
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def mode() -> str:
    return "Supabase" if _supabase_client() else "Demonstração"


def list_jobs() -> list[dict]:
    client = _supabase_client()
    if client:
        return client.table("jobs").select("*").order("created_at", desc=True).execute().data
    if "jobs" not in st.session_state:
        st.session_state.jobs = DEMO_JOBS.copy()
    return st.session_state.jobs


def add_job(job: dict) -> dict:
    result = score_job(job)
    row = {
        **job,
        **result.to_dict(),
        "status": "Na fila" if result.decision in {"AUTOAPLICAR", "REVISAR"} else result.decision.title(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client = _supabase_client()
    if client:
        return client.table("jobs").insert(row).execute().data[0]
    row["id"] = f"local-{len(list_jobs()) + 1}"
    st.session_state.jobs.insert(0, row)
    return row
