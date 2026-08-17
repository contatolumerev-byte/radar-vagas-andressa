# Radar de Vagas da Andressa

Aplicativo pessoal e gratuito para organizar vagas, aplicar regras transparentes de aderência e separar o que pode avançar automaticamente do que exige decisão humana.

## O que já funciona

- painel com indicadores e lista priorizada;
- pontuação de 0 a 100;
- decisões `AUTOAPLICAR`, `REVISAR`, `DESCARTAR` e `BLOQUEADA`;
- bloqueios para hunting, cold call, telemarketing ativo, venda externa, shopping, escala 6x1, salário abaixo de R$ 2.500 e presencial fora de Fortaleza;
- fila “Ação da Andressa” para CAPTCHA, SMS, vídeo e perguntas sensíveis;
- modo demonstração sem banco e sem chave de IA;
- persistência opcional no Supabase e triagem programada pelo GitHub Actions.
- personalização opcional com Gemini, sem permitir que a IA ignore bloqueios objetivos.

> Segurança: currículos, senhas e dados pessoais não devem ser versionados neste repositório. Use os Secrets do Streamlit/GitHub.

## Publicar gratuitamente no Streamlit

1. Acesse [share.streamlit.io](https://share.streamlit.io/) e entre com o GitHub.
2. Clique em **Create app**.
3. Selecione o repositório `contatolumerev-byte/radar-vagas-andressa`.
4. Use branch `main` e arquivo principal `app.py`.
5. Clique em **Deploy**.

O app abre imediatamente em modo demonstração. Não é necessário cadastrar cartão.

## Conectar o Supabase depois

1. Crie um projeto gratuito no Supabase.
2. Abra o SQL Editor e execute `supabase_schema.sql`.
3. Nos Secrets do Streamlit, cadastre:

```toml
SUPABASE_URL = "sua-url"
SUPABASE_SERVICE_ROLE_KEY = "sua-chave-service-role"
```

4. Nos Secrets do repositório GitHub, cadastre os mesmos nomes para o workflow.

Nunca envie essas chaves em conversa, commit ou captura de tela. A chave `service_role` fica somente nos cofres de secrets.

## Conectar o Gemini gratuitamente

1. Crie uma chave no [Google AI Studio](https://aistudio.google.com/app/apikey).
2. No Streamlit, abra o app, clique em **Manage app**, depois **Settings** e **Secrets**.
3. Adicione e salve:

```toml
GEMINI_API_KEY = "sua-chave"
GEMINI_MODEL = "gemini-2.5-flash"
```

O Gemini é chamado somente quando você clica em **Gerar personalização**. No nível gratuito, não envie telefone, e-mail, CPF, endereço, currículo completo nem informações de saúde; use apenas o perfil profissional aprovado e a descrição pública da vaga.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Limite importante

O projeto não tenta contornar CAPTCHA, MFA/SMS nem regras das plataformas. Esses casos param na fila humana. O envio real só deve ser ativado depois da revisão dos currículos e das respostas-padrão.
