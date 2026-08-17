"""Regras transparentes de aderência das vagas ao perfil da Andressa."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict


ROLE_FAMILIES = [
    ("Atendimento, Suporte e Relacionamento", 30, [
        "atendimento ao cliente", "assistente de atendimento",
        "analista de atendimento", "agente de atendimento",
        "suporte ao cliente", "customer support", "customer service",
        "assistente de relacionamento", "pos-venda", "pos venda",
    ]),
    ("IA aplicada, Automação e Aplicativos", 32, [
        "ai creator", "analista de ia generativa", "generative ai analyst",
        "analista de automacao", "automacao de processos", "process automation",
        "analista de solucoes", "low-code", "low code", "no-code", "no code",
        "aplicacoes internas", "internal tools", "product builder",
    ]),
    ("Customer Success e Relacionamento", 34, [
        "customer success", "sucesso do cliente", "customer experience",
        "experiencia do cliente", "analista de relacionamento", "customer care",
        "customer operations", "customer support", "onboarding de clientes",
    ]),
    ("RevOps, Sales Ops e Inteligência Comercial", 34, [
        "revops", "revenue operations", "sales ops", "sales operations",
        "inteligencia comercial", "operacoes comerciais", "enablement",
    ]),
    ("Comercial consultivo sem hunting", 32, [
        "consultora comercial", "consultor comercial", "assistente comercial",
        "executiva de contas", "executivo de contas", "account manager",
        "inside sales", "closer", "pos-venda", "pre-vendas inbound",
    ]),
    ("Operações, Processos e Projetos", 28, [
        "analista de operacoes", "assistente de operacoes", "business operations",
        "product operations", "analista de processos", "assistente de projetos",
        "analista de projetos", "pmo", "implantacao", "implementacao",
    ]),
    ("CRM e Marketing Operacional", 26, [
        "analista de crm", "assistente de crm", "marketing operations",
        "operacoes de marketing", "lifecycle", "customer marketing",
        "analista de marketing", "growth operations", "social media",
    ]),
    ("Dados e BI Júnior", 24, [
        "analista de dados junior", "analista de dados jr", "assistente de dados",
        "business intelligence junior", "bi junior", "analista de indicadores",
        "analista de performance", "analista de relatorios",
    ]),
    ("Backoffice e Administrativo", 22, [
        "assistente administrativo", "analista administrativo", "backoffice",
        "back office", "assistente de atendimento", "analista de atendimento",
    ]),
]

POSITIVE_TERMS = {
    "remoto": 16,
    "home office": 16,
    "fortaleza": 12,
    "inbound": 8,
    "carteira de clientes": 8,
    "fidelizacao": 8,
    "retencao": 8,
    "onboarding": 8,
    "crm": 5,
    "hubspot": 5,
    "pipedrive": 5,
    "rd crm": 5,
    "excel": 5,
    "google sheets": 5,
    "indicadores": 5,
    "kpi": 5,
    "dashboard": 4,
    "processos": 4,
    "automacao": 4,
    "projetos": 4,
    "dados": 4,
    "ia generativa": 5,
    "inteligencia artificial": 5,
    "streamlit": 5,
    "supabase": 5,
    "python": 4,
    "javascript": 3,
    "low-code": 5,
    "no-code": 5,
    "aplicativos internos": 5,
    "aplicacoes internas": 5,
    "automacao de processos": 5,
    "api": 3,
    "segunda a sexta": 5,
}

HARD_BLOCKS = {
    "hunting": "Exige hunting/prospecção ativa",
    "hunter": "Perfil hunter",
    "outbound": "Exige prospecção outbound",
    "prospeccao ativa": "Exige prospecção ativa",
    "cold call": "Exige cold calls",
    "telemarketing": "Rotina de telemarketing",
    "porta a porta": "Venda externa/porta a porta",
    "vendedor externo": "Venda externa",
    "consultor externo": "Venda externa",
    "escala 6x1": "Escala 6x1",
    "shopping": "Ambiente de shopping",
    "call center": "Rotina de call center",
    "machine learning engineer": "Engenharia de Machine Learning fora do foco atual",
    "engenheiro de machine learning": "Engenharia de Machine Learning fora do foco atual",
    "engenheira de machine learning": "Engenharia de Machine Learning fora do foco atual",
    "data scientist": "Ciência de Dados fora do foco atual",
    "cientista de dados": "Ciência de Dados fora do foco atual",
}

REVIEW_TERMS = {
    "prospeccao": "Pode envolver prospecção",
    "metas agressivas": "Metas agressivas",
    "disponibilidade de horario": "Horário não detalhado",
    "presencial": "Confirmar localização e rotina presencial",
}


def normalize(value: object) -> str:
    text = str(value or "").lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip()


def parse_salary(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = normalize(value).replace("r$", "").replace(".", "").replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


@dataclass
class ScoreResult:
    score: int
    decision: str
    reasons: list[str]
    blocks: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def score_job(job: dict, auto_threshold: int = 85, review_threshold: int = 70) -> ScoreResult:
    title = normalize(job.get("title"))
    description = normalize(job.get("description"))
    location = normalize(job.get("location"))
    work_mode = normalize(job.get("work_mode"))
    combined = " ".join([title, description, location, work_mode])
    salary = parse_salary(job.get("salary_min"))

    reasons: list[str] = []
    blocks = [reason for term, reason in HARD_BLOCKS.items() if term in combined]
    warnings = [reason for term, reason in REVIEW_TERMS.items() if term in combined]

    if salary is not None and salary < 2500:
        blocks.append(f"Salário abaixo de R$ 2.500 (R$ {salary:,.0f})")

    score = 30
    matches = [
        (points, family, term)
        for family, points, terms in ROLE_FAMILIES
        for term in terms
        if term in combined
    ]
    if matches:
        points, family, term = max(matches)
        score += points
        reasons.append(f"Trilha compatível: {family} ({term})")
    else:
        warnings.append("Cargo fora das trilhas prioritárias")
        score -= 18

    positive_points = 0
    for term, points in POSITIVE_TERMS.items():
        if term in combined:
            positive_points += points
            reasons.append(f"Ponto positivo: {term}")
    score += min(24, positive_points)

    if salary is not None and salary >= 2500:
        score += 8
        reasons.append("Salário dentro do mínimo")
    elif salary is None:
        warnings.append("Salário não informado")

    explicit_office = any(term in work_mode for term in ("presencial", "hibrido"))
    if explicit_office and "fortaleza" not in location:
            blocks.append("Presencial/híbrida fora de Fortaleza")
    elif not explicit_office and "remoto" not in combined and "home office" not in combined:
        warnings.append("Modelo de trabalho precisa ser confirmado")

    if any(term in title for term in ("senior", "sr", "especialista", "coordenador", "gerente", "head")):
        warnings.append("Senioridade acima do foco atual")
        score -= 12

    score -= min(20, len(warnings) * 5)
    score = max(0, min(100, score))

    if blocks:
        decision = "BLOQUEADA"
    elif score >= auto_threshold:
        decision = "AUTOAPLICAR"
    elif score >= review_threshold:
        decision = "REVISAR"
    else:
        decision = "DESCARTAR"

    return ScoreResult(score, decision, reasons, blocks, warnings)
