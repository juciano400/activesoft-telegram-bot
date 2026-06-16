# SAE IA — Assistente Inteligente para o SAE Digital

Sistema web com IA que faz login no SAE Digital e responde perguntas sobre trilhas e relatórios dos alunos.

## Deploy no Railway

### 1. Crie um novo projeto no Railway
- Acesse https://railway.app e crie um projeto
- Selecione **Deploy from GitHub repo**
- Escolha o repositório `activesoft-telegram-bot`
- Defina o **Root Directory** como `sae-system`

### 2. Configure as variáveis de ambiente no Railway

Vá em **Variables** e adicione:

```
SAE_EMAIL=juciano@agapepatos.com.br
SAE_PASSWORD=E@agape2026
ANTHROPIC_API_KEY=sua_chave_aqui
```

> Sua chave Anthropic: https://console.anthropic.com/

### 3. Pronto!

O Railway vai fazer o build com Docker e subir a aplicação automaticamente.

---

## Rodar localmente

```bash
cd sae-system
pip install flask playwright anthropic python-dotenv gunicorn
playwright install chromium

# Crie o .env
echo "SAE_EMAIL=juciano@agapepatos.com.br" > .env
echo "SAE_PASSWORD=E@agape2026" >> .env
echo "ANTHROPIC_API_KEY=sua_chave" >> .env

python app.py
```

Acesse: http://localhost:5000

---

## Como usar

1. Abra a URL do Railway no navegador
2. Digite qualquer pergunta:
   - *"Quais alunos completaram a trilha?"*
   - *"Quem ainda não fez a atividade?"*
   - *"Qual a média de acertos da turma?"*
3. A IA faz login, navega pelo SAE e responde
