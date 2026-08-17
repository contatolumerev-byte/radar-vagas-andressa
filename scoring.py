"""Regras transparentes de aderência das vagas ao perfil da Andressa."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict


TARGET_TERMS = {
    "customer success": 30,
    "sucesso do cliente": 30,
    "customer experience": 24,
    "experiencia do cliente": 24,
    "relacionamento": 24,
    "atendimento ao cliente": 20,
    "consultora comercial": 24,
    "consultor comercial": 24,
    "assistente comercial": 24,
    "pos-venda": 18,
}

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
    "segunda a sexta": 5,
}

HARD_BLOCKS = {
    "hunting": "Exige hunting/prospecção ativa",
    "hunter": "Perfil hunter",
    "cold call": "Exige cold calls",
    "telemarketing ativo": "Telemarketing ativo",
    "porta a porta": "Venda externa/porta a porta",
    "vendedor externo": "Venda externa",
    "consultor externo": "Venda externa",
    "escala 6x1": "Escala 6x1",
    "shopping": "Ambiente de shopping",
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

    score = 35
    matched_target = False
    for term, points in TARGET_TERMS.items():
        if term in combined:
            score += points
            reasons.append(f"Trilha desejada: {term}")
            matched_target = True
            break
    if not matched_target:
        warnings.append("Cargo fora das trilhas prioritárias")
        score -= 20

    for term, points in POSITIVE_TERMS.items():
        if term in combined:
            score += points
            reasons.append(f"Ponto positivo: {term}")

    if salary is not None and salary >= 2500:
        score += 8
        reasons.append("Salário dentro do mínimo")
    elif salary is None:
        warnings.append("Salário não informado")

    if "remoto" not in combined and "home office" not in combined:
        if "fortaleza" not in location:
            blocks.append("Presencial/híbrida fora de Fortaleza")

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
