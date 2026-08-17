"""Dados fixos e posicionamento dinâmico do currículo da Andressa."""

from __future__ import annotations

import re
import unicodedata


PROFILE_HEADER = {
    "name": "ANDRESSA ELLEN MARTINS FREIRE",
    "location": "Fortaleza – CE",
    "email": "contato.andressafreire@gmail.com",
    "linkedin": "linkedin.com/in/andressafreire",
}


TARGET_ROLE_GROUPS = {
    "Prioridade principal": [
        "Analista de Operações Comerciais",
        "Analista de Inteligência Comercial",
        "Analista de Sales Operations / Sales Ops",
        "Analista de Revenue Operations / RevOps Júnior",
        "Analista de Sales Enablement",
    ],
    "Relacionamento e jornada do cliente": [
        "Analista de Customer Success",
        "Analista de Customer Experience",
        "Analista de Relacionamento B2B",
        "Analista de Customer Operations",
        "Analista de Onboarding ou Implantação",
        "Account Manager com carteira, sem hunting",
    ],
    "Vagas próximas e vagas-ponte": [
        "Analista ou Assistente de Operações",
        "Analista de Processos",
        "Analista ou Assistente de Projetos / PMO",
        "Analista de CRM",
        "Analista de Indicadores ou Performance Júnior",
        "Analista de Backoffice ou Atendimento",
        "Assistente ou Consultora Comercial inbound, sem hunting",
    ],
}


HEADLINE_RULES = [
    (
        ("revops", "revenue operations", "sales ops", "sales operations", "operacoes comerciais", "inteligencia comercial", "sales enablement"),
        "Revenue Operations | Sales Operations | CRM | Inteligência Comercial",
    ),
    (
        ("customer success", "sucesso do cliente", "customer experience", "experiencia do cliente", "relacionamento b2b", "customer operations", "customer care"),
        "Customer Success | Customer Experience | Relacionamento B2B | SaaS",
    ),
    (
        ("implantacao", "implementacao", "onboarding", "implementation"),
        "Implantação | Onboarding | Customer Success | Gestão de Projetos",
    ),
    (
        ("projetos", "project", "pmo"),
        "Projetos | Processos | Operações | Indicadores",
    ),
    (
        ("operacoes", "operations", "processos", "process analyst", "backoffice", "back office"),
        "Operações | Processos | Projetos | Indicadores",
    ),
    (
        ("crm", "lifecycle", "marketing operations", "growth operations"),
        "CRM | Jornada do Cliente | Automação | Indicadores",
    ),
    (
        ("dados", "data analyst", "business intelligence", "bi junior", "indicadores", "performance", "relatorios"),
        "Dados | Indicadores | Dashboards | Melhoria de Processos",
    ),
    (
        ("consultor comercial", "consultora comercial", "assistente comercial", "inside sales", "account manager", "executivo de contas", "executiva de contas", "pos-venda"),
        "Comercial Consultivo | Relacionamento | CRM | Pós-venda",
    ),
    (
        ("atendimento", "relacionamento", "customer support", "suporte ao cliente"),
        "Relacionamento com Clientes | Atendimento | CRM | Experiência do Cliente",
    ),
]


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip()


def headline_for_job(job: dict | None = None) -> str:
    """Escolhe uma linha profissional defensável a partir do título e da descrição."""
    if not job:
        return "Operações Comerciais | Customer Success | CRM | Processos"

    title = _normalize(job.get("title"))
    description = _normalize(job.get("description"))
    # O título pesa primeiro; a descrição desempata vagas com nomenclatura genérica.
    for source in (title, f"{title} {description}"):
        for terms, headline in HEADLINE_RULES:
            if any(term in source for term in terms):
                return headline
    return "Operações Comerciais | Customer Success | CRM | Processos"


def resume_header(job: dict | None = None) -> dict:
    return {**PROFILE_HEADER, "headline": headline_for_job(job)}
