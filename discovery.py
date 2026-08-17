"""Descoberta gratuita de vagas públicas e alertas recebidos no Gmail."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from gmail_service import fetch_job_alert_links


SEARCH_TERMS = [
    "analista de operacoes comerciais", "analista de inteligencia comercial",
    "sales operations", "sales ops", "revops junior", "revenue operations",
    "sales enablement", "analista de customer success", "customer experience",
    "relacionamento b2b", "customer operations", "onboarding de clientes",
    "analista de implantacao", "analista de operacoes", "analista de processos",
    "analista de projetos junior", "pmo junior", "analista de crm",
    "analista de indicadores", "analista de performance junior",
    "assistente de operacoes", "assistente comercial inbound",
    "atendimento ao cliente remoto", "assistente de atendimento remoto",
    "analista de atendimento remoto", "customer support brasil",
    "customer service remoto", "suporte ao cliente remoto",
    "assistente de relacionamento", "pos venda remoto",
    "consultora comercial remoto", "consultora comercial fortaleza",
    "consultora comercial inbound", "assistente comercial remoto",
    "ai creator junior", "analista de ia generativa",
    "analista de automacao de processos", "analista de solucoes e automacoes",
    "desenvolvedor low code junior", "desenvolvedor no code junior",
    "aplicacoes internas junior", "internal tools junior",
]

HEADERS = {"User-Agent": "RadarVagasAndressa/1.0 (busca pessoal de empregos)"}


def _clean_html(value: object) -> str:
    return " ".join(BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True).split())


def _find_job_posting(value):
    if isinstance(value, dict):
        if value.get("@type") == "JobPosting":
            return value
        for child in value.values():
            found = _find_job_posting(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_job_posting(child)
            if found:
                return found
    return None


def _salary(posting: dict) -> float | None:
    value = posting.get("baseSalary")
    if isinstance(value, dict):
        value = value.get("value", value)
        if isinstance(value, dict):
            value = value.get("minValue") or value.get("value")
    try:
        return float(value) if value else None
    except (TypeError, ValueError):
        return None


def fetch_job_detail(url: str, title_hint: str = "", source: str = "Web") -> dict | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return {"title": title_hint, "company": source, "location": "", "work_mode": "Não informado", "salary_min": None, "description": title_hint, "url": url, "source": source} if title_hint else None

    soup = BeautifulSoup(response.text, "html.parser")
    posting = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            posting = _find_job_posting(json.loads(script.string or "{}"))
        except (json.JSONDecodeError, TypeError):
            continue
        if posting:
            break

    if posting:
        organization = posting.get("hiringOrganization") or {}
        location_data = posting.get("jobLocation") or {}
        if isinstance(location_data, list):
            location_data = location_data[0] if location_data else {}
        address = location_data.get("address", {}) if isinstance(location_data, dict) else {}
        location = ", ".join(str(address.get(key, "")) for key in ("addressLocality", "addressRegion", "addressCountry") if address.get(key))
        remote = posting.get("jobLocationType") == "TELECOMMUTE" or "remoto" in _clean_html(posting.get("description")).lower()
        return {
            "title": posting.get("title") or title_hint,
            "company": organization.get("name") if isinstance(organization, dict) else str(organization),
            "location": location,
            "work_mode": "Remoto" if remote else "Não informado",
            "salary_min": _salary(posting),
            "description": _clean_html(posting.get("description"))[:20000],
            "url": url,
            "source": source,
        }

    description = soup.get_text(" ", strip=True)
    return {"title": title_hint or (soup.title.string if soup.title else "Vaga"), "company": source, "location": "", "work_mode": "Remoto" if "remoto" in description.lower() else "Não informado", "salary_min": None, "description": " ".join(description.split())[:20000], "url": url, "source": source}


def _search_gupy_term(term: str, limit: int) -> list[tuple[str, str]]:
    search_url = "https://portal.gupy.io/job-search/" + quote(f"term={term}", safe="")
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=12)
        response.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    matches: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/job/" not in href:
            continue
        url = urljoin("https://portal.gupy.io", href)
        title = " ".join(anchor.get_text(" ", strip=True).split())[:240] or term
        matches.append((url, title))
        if len(matches) >= limit:
            break
    return matches


def discover_gupy(limit_per_term: int = 3) -> list[dict]:
    links: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for matches in pool.map(lambda term: _search_gupy_term(term, limit_per_term), SEARCH_TERMS):
            for url, title in matches:
                links[url] = title

    def load_detail(item: tuple[str, str]) -> dict | None:
        url, title = item
        return fetch_job_detail(url, title, "Gupy")

    with ThreadPoolExecutor(max_workers=5) as pool:
        return [job for job in pool.map(load_detail, links.items()) if job]


def discover_all() -> list[dict]:
    found: dict[str, dict] = {}
    for item in discover_gupy():
        found[item["url"]] = item
    for alert in fetch_job_alert_links():
        detail = fetch_job_detail(alert["url"], alert["title_hint"], alert["source"])
        if detail:
            found[detail["url"]] = detail
    return list(found.values())
