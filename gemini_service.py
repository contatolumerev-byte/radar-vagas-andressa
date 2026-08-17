"""Personalização opcional com Gemini, sem alterar os bloqueios objetivos."""

from __future__ import annotations

import streamlit as st


APPROVED_PROFILE = """
Objetivo: Customer Success, Relacionamento, Experiência do Cliente ou Comercial consultivo sem hunting.
Competências utilizáveis quando forem pertinentes: atendimento e relacionamento com clientes,
CRM, organização de processos, follow-up, pós-venda, análise de indicadores, Excel/Google Sheets,
HubSpot, RD CRM, Pipedrive, Looker Studio e noções de SQL, Python e automações.
Formação atual: Análise e Desenvolvimento de Sistemas — UNINASSAU.
Preferências: trabalho remoto no Brasil; híbrido ou presencial apenas em Fortaleza.
""".strip()


def configured() -> bool:
    try:
        return bool(st.secrets.get("GEMINI_API_KEY"))
    except Exception:
        return False


def personalize(job: dict) -> str:
    if not configured():
        raise RuntimeError("A chave GEMINI_API_KEY ainda não foi configurada.")

    from google import genai

    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    configured_model = st.secrets.get("GEMINI_MODEL", "gemini-3-flash-preview")
    model = "gemini-3-flash-preview" if configured_model == "gemini-2.5-flash" else configured_model
    prompt = f"""
Você auxilia uma candidata brasileira a personalizar uma candidatura com honestidade.

REGRAS OBRIGATÓRIAS:
- Use somente fatos do perfil aprovado abaixo. Nunca invente experiências, resultados, cargos ou números.
- Não inclua telefone, e-mail, endereço, CPF, diagnóstico médico ou informação de saúde/PcD.
- Não responda perguntas eliminatórias em nome da candidata.
- Não altere a decisão objetiva do sistema e não recomende contornar CAPTCHA ou autenticação.
- Escreva em português brasileiro, natural e sem clichês de IA.

PERFIL APROVADO:
{APPROVED_PROFILE}

VAGA:
Cargo: {job.get('title', '')}
Empresa: {job.get('company', '')}
Local/modelo: {job.get('location', '')} / {job.get('work_mode', '')}
Descrição: {job.get('description', '')}

Entregue exatamente estas seções:
1. ADERÊNCIA: cinco competências relevantes, sem inventar.
2. RESUMO PROFISSIONAL: parágrafo de até 90 palavras para o currículo.
3. PALAVRAS-CHAVE ATS: até 12 termos presentes ou claramente exigidos pela vaga.
4. MENSAGEM DE CANDIDATURA: texto de até 120 palavras.
5. PONTOS PARA CONFIRMAR: requisitos da vaga que não podem ser comprovados pelo perfil fornecido.
""".strip()

    try:
        response = client.models.generate_content(model=model, contents=prompt)
    except Exception as error:
        if "404" not in str(error) and "NOT_FOUND" not in str(error):
            raise
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    if not response.text:
        raise RuntimeError("O Gemini não devolveu conteúdo. Tente novamente mais tarde.")
    return response.text.strip()
