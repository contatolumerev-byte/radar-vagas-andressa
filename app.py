from __future__ import annotations

import pandas as pd
import streamlit as st

from gemini_service import configured as gemini_configured, personalize
from scoring import score_job
from storage import add_job, list_jobs, mode


st.set_page_config(page_title="Radar de Vagas da Andressa", page_icon="🎯", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {background: #17223b;}
    [data-testid="stSidebar"] * {color: #fff8ed;}
    .stMetric {background:#fff8ed;border:1px solid #ead9bd;padding:14px;border-radius:14px;}
    h1, h2, h3 {color:#70193d;}
    </style>
    """,
    unsafe_allow_html=True,
)


def enriched_jobs() -> list[dict]:
    rows = []
    for job in list_jobs():
        if "score" not in job or "decision" not in job:
            result = score_job(job)
            job = {**job, **result.to_dict()}
        rows.append(job)
    return rows


def jobs_table(rows: list[dict]) -> None:
    if not rows:
        st.info("Nenhuma vaga nesta lista.")
        return
    frame = pd.DataFrame(rows)
    columns = ["decision", "score", "title", "company", "location", "work_mode", "salary_min", "status", "url"]
    columns = [column for column in columns if column in frame.columns]
    frame = frame[columns].rename(
        columns={
            "decision": "Decisão",
            "score": "Nota",
            "title": "Vaga",
            "company": "Empresa",
            "location": "Local",
            "work_mode": "Modelo",
            "salary_min": "Salário mínimo",
            "status": "Status",
            "url": "Link",
        }
    )
    st.dataframe(frame, use_container_width=True, hide_index=True, column_config={"Link": st.column_config.LinkColumn()})


st.sidebar.title("🎯 Radar da Andressa")
page = st.sidebar.radio("Navegação", ["Painel", "Vagas", "Fila de revisão", "Personalizar com Gemini", "Currículos", "Configurações", "Conexões"])
st.sidebar.caption(f"Modo atual: {mode()}")

jobs = enriched_jobs()

if page == "Painel":
    st.title("Painel de recolocação")
    st.caption("As melhores oportunidades primeiro, com regras claras e controle sobre exceções.")
    metrics = st.columns(5)
    metrics[0].metric("Vagas", len(jobs))
    metrics[1].metric("Autoaplicar", sum(j["decision"] == "AUTOAPLICAR" for j in jobs))
    metrics[2].metric("Revisar", sum(j["decision"] == "REVISAR" for j in jobs))
    metrics[3].metric("Bloqueadas", sum(j["decision"] == "BLOQUEADA" for j in jobs))
    metrics[4].metric("Entrevistas", sum(j.get("status") == "Entrevista" for j in jobs))
    st.subheader("Vagas mais aderentes")
    jobs_table(sorted(jobs, key=lambda item: item["score"], reverse=True)[:10])
    st.info("O envio real só será habilitado depois que o currículo correto e os acessos forem validados. CAPTCHA, SMS, vídeo e perguntas sensíveis sempre param para sua ação.")

elif page == "Vagas":
    st.title("Vagas")
    tab_list, tab_add = st.tabs(["Lista", "Adicionar vaga"])
    with tab_list:
        decision = st.multiselect("Filtrar decisão", ["AUTOAPLICAR", "REVISAR", "DESCARTAR", "BLOQUEADA"], default=[])
        filtered = [job for job in jobs if not decision or job["decision"] in decision]
        jobs_table(filtered)
    with tab_add:
        with st.form("new_job", clear_on_submit=True):
            col1, col2 = st.columns(2)
            title = col1.text_input("Cargo *")
            company = col2.text_input("Empresa *")
            location = col1.text_input("Local")
            work_mode = col2.selectbox("Modelo", ["Remoto", "Híbrido", "Presencial", "Não informado"])
            salary = col1.number_input("Salário mínimo", min_value=0, step=100)
            url = col2.text_input("Link da vaga")
            description = st.text_area("Descrição da vaga *", height=180)
            submitted = st.form_submit_button("Analisar vaga")
            if submitted:
                if not title or not company or not description:
                    st.error("Preencha cargo, empresa e descrição.")
                else:
                    saved = add_job({"title": title, "company": company, "location": location, "work_mode": work_mode, "salary_min": salary or None, "url": url, "description": description})
                    st.success(f"Vaga analisada: {saved['decision']} — nota {saved['score']}/100.")

elif page == "Fila de revisão":
    st.title("Ação da Andressa")
    st.caption("Itens que exigem decisão humana ficam aqui; o robô não inventa respostas.")
    queue = [job for job in jobs if job["decision"] == "REVISAR" or job.get("status") == "Ação da Andressa"]
    jobs_table(queue)
    st.warning("Perguntas sobre saúde/PcD/adaptação, pretensão ambígua, vídeo, CAPTCHA, SMS ou autenticação nunca serão respondidas automaticamente.")

elif page == "Personalizar com Gemini":
    st.title("Personalização com Gemini")
    st.caption("O Gemini sugere texto; as regras objetivas e os bloqueios continuam sob controle do sistema.")
    if not gemini_configured():
        st.warning("Gemini ainda não conectado. Adicione GEMINI_API_KEY nos Secrets do Streamlit.")
        st.code('GEMINI_API_KEY = "cole-a-chave-aqui"\nGEMINI_MODEL = "gemini-2.5-flash"', language="toml")
    eligible = [job for job in jobs if job["decision"] != "BLOQUEADA"]
    if not eligible:
        st.info("Não há vagas elegíveis para personalizar.")
    else:
        labels = {f"{job['title']} — {job['company']} ({job['score']}/100)": job for job in eligible}
        selected_label = st.selectbox("Escolha uma vaga", list(labels))
        selected_job = labels[selected_label]
        if selected_job["decision"] == "DESCARTAR":
            st.warning("A vaga está abaixo da nota de revisão. A personalização não muda essa decisão.")
        if st.button("Gerar personalização", disabled=not gemini_configured()):
            try:
                with st.spinner("Analisando a vaga sem inventar informações..."):
                    st.session_state.gemini_result = personalize(selected_job)
                st.success("Personalização gerada. Revise antes de usar.")
            except Exception as error:
                st.error(f"Não foi possível consultar o Gemini: {error}")
        if st.session_state.get("gemini_result"):
            st.markdown(st.session_state.gemini_result)
    st.info("Privacidade: no plano gratuito, não envie telefone, e-mail, CPF, endereço, currículo completo ou informações de saúde ao Gemini.")

elif page == "Currículos":
    st.title("Currículos e personalização")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Customer Success")
        st.error("Bloqueado para envio")
        st.write("A formação precisa ser atualizada para **Análise e Desenvolvimento de Sistemas — UNINASSAU** antes de usar.")
    with col2:
        st.subheader("Comercial sem hunting")
        st.warning("Base pendente")
        st.write("Será montada com foco em atendimento, relacionamento, inbound, propostas, CRM e pós-venda.")
    st.info("A personalização usará apenas blocos verdadeiros e previamente aprovados. Nenhuma experiência será inventada.")

elif page == "Configurações":
    st.title("Regras de busca e envio")
    st.number_input("Nota mínima para envio automático", min_value=70, max_value=100, value=85, disabled=True)
    st.number_input("Nota mínima para revisão", min_value=0, max_value=100, value=70, disabled=True)
    st.number_input("Salário mínimo mensal", min_value=0, value=2500, step=100, disabled=True)
    st.write("**Trilhas:** Customer Success/Relacionamento; Assistente ou Consultora Comercial sem hunting.")
    st.write("**Prioridade:** remoto no Brasil; híbrido/presencial somente em Fortaleza.")
    st.write("**Bloqueios:** hunting, outbound/cold call, telemarketing ativo, venda externa/porta a porta, shopping e escala 6x1.")
    st.caption("A edição persistente dessas regras será liberada após conectar o banco.")

else:
    st.title("Conexões")
    st.success("GitHub: conectado — repositório privado")
    if mode() == "Supabase":
        st.success("Supabase: conectado")
    else:
        st.warning("Supabase: ainda não conectado; o app está em modo demonstração")
    if gemini_configured():
        st.success("Gemini: conectado")
    else:
        st.warning("Gemini: ainda não conectado")
    st.write("GitHub Actions executará a triagem em horários programados depois que os segredos do Supabase forem cadastrados.")
