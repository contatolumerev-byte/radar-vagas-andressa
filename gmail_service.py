"""Leitura restrita de alertas de vagas e envio via Gmail."""

from __future__ import annotations

import email
import imaplib
import os
import re
import smtplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import EmailMessage
from email.utils import parseaddr
from urllib.parse import urlparse

from bs4 import BeautifulSoup


ALLOWED_SENDERS = (
    "linkedin.com", "gupy.io", "indeed.com", "infojobs.com.br",
    "catho.com.br", "vagas.com.br", "trampos.co", "remotar.com.br",
)

ALLOWED_JOB_HOSTS = (
    "linkedin.com", "gupy.io", "indeed.com", "infojobs.com.br",
    "catho.com.br", "vagas.com.br", "greenhouse.io", "lever.co",
    "ashbyhq.com", "workable.com", "recruitee.com", "smartrecruiters.com",
)

ROLE_HINTS = (
    "customer", "cliente", "relacionamento", "comercial", "revops",
    "sales ops", "operações", "operacoes", "processos", "projetos",
    "crm", "marketing", "dados", "data", "bi ", "atendimento",
    "backoffice", "implantação", "implantacao", "implementação",
    "ai creator", "ia generativa", "inteligência artificial",
    "inteligencia artificial", "automação", "automacao", "aplicativo",
    "low-code", "low code", "no-code", "no code", "internal tools",
    "streamlit", "supabase",
)


def _secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return st.secrets.get(name)
    except Exception:
        return None


def configured() -> bool:
    return bool(_secret("GMAIL_ADDRESS") and _secret("GMAIL_APP_PASSWORD"))


def test_connection() -> bool:
    address = _secret("GMAIL_ADDRESS")
    password = _secret("GMAIL_APP_PASSWORD")
    if not address or not password:
        return False
    mailbox = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        mailbox.login(address, password.replace(" ", ""))
        return mailbox.select("INBOX", readonly=True)[0] == "OK"
    finally:
        try:
            mailbox.logout()
        except Exception:
            pass


def _decoded_header(value: str | None) -> str:
    parts = []
    for content, charset in decode_header(value or ""):
        if isinstance(content, bytes):
            parts.append(content.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(content)
    return "".join(parts)


def _message_html(message: email.message.Message) -> str:
    html = ""
    plain = ""
    for part in message.walk() if message.is_multipart() else [message]:
        if "attachment" in (part.get("Content-Disposition") or "").lower():
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if part.get_content_type() == "text/html":
            html += text
        elif part.get_content_type() == "text/plain":
            plain += text
    return html or plain


def _is_job_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return any(domain in host for domain in ALLOWED_JOB_HOSTS) and not any(
        term in url.lower() for term in ("unsubscribe", "preferences", "settings", "login")
    )


def fetch_job_alert_links(days: int = 7, limit_messages: int = 60) -> list[dict]:
    """Lê somente mensagens recentes que parecem alertas dos portais permitidos."""
    address = _secret("GMAIL_ADDRESS")
    password = _secret("GMAIL_APP_PASSWORD")
    if not address or not password:
        return []

    since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    mailbox = imaplib.IMAP4_SSL("imap.gmail.com")
    found: dict[str, dict] = {}
    try:
        mailbox.login(address, password.replace(" ", ""))
        mailbox.select("INBOX", readonly=True)
        message_ids: set[bytes] = set()
        for domain in ALLOWED_SENDERS:
            status, data = mailbox.search(None, "SINCE", since, "FROM", f'"{domain}"')
            if status == "OK" and data:
                message_ids.update(data[0].split())
        for message_id in sorted(message_ids, key=lambda item: int(item))[-limit_messages:]:
            status, payload = mailbox.fetch(message_id, "(RFC822)")
            if status != "OK" or not payload or not isinstance(payload[0], tuple):
                continue
            message = email.message_from_bytes(payload[0][1])
            sender = parseaddr(_decoded_header(message.get("From")))[1].lower()
            subject = _decoded_header(message.get("Subject"))
            if not any(domain in sender for domain in ALLOWED_SENDERS):
                continue
            soup = BeautifulSoup(_message_html(message), "html.parser")
            for anchor in soup.find_all("a", href=True):
                url = anchor["href"].strip()
                title = " ".join(anchor.get_text(" ", strip=True).split())
                if not _is_job_url(url) or len(title) < 5:
                    continue
                if not any(hint in title.lower() for hint in ROLE_HINTS):
                    continue
                found[url] = {"url": url, "title_hint": title[:240], "source": "Gmail"}
    finally:
        try:
            mailbox.logout()
        except Exception:
            pass
    return list(found.values())


def send_application(to_address: str, subject: str, body: str, attachment_path: str | None = None) -> None:
    """Envia somente quando chamado pelo futuro worker de candidaturas aprovadas."""
    address = _secret("GMAIL_ADDRESS")
    password = _secret("GMAIL_APP_PASSWORD")
    if not address or not password:
        raise RuntimeError("Gmail não configurado.")
    message = EmailMessage()
    message["From"] = address
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    if attachment_path:
        with open(attachment_path, "rb") as file:
            message.add_attachment(file.read(), maintype="application", subtype="pdf", filename=os.path.basename(attachment_path))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(address, password.replace(" ", ""))
        smtp.send_message(message)
