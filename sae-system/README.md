# SAE IA — Assistente Inteligente para o SAE Digital

Sistema web com IA que faz login no SAE Digital e responde perguntas sobre trilhas e relatórios dos alunos.

## Como rodar localmente

### 1. Instale as dependências
```bash
pip install flask playwright anthropic python-dotenv
playwright install chromium
```

### 2. Configure as credenciais
Crie um arquivo `.env` na pasta `sae-system/`:
```
SAE_EMAIL=juciano@agapepatos.com.br
SAE_PASSWORD=E@agape2026
ANTHROPIC_API_KEY=sua_chave_aqui
```

### 3. Rode o sistema
```bash
cd sae-system
python app.py
```

Acesse: http://localhost:5000

## Como usar

1. Abra o navegador em `http://localhost:5000`
2. Digite qualquer pergunta sobre o SAE, por exemplo:
   - "Quais alunos completaram a trilha?"
   - "Quem ainda não fez a atividade?"
   - "Qual a média de acertos da turma?"
3. A IA faz login automaticamente, navega pelo SAE e traz a resposta

## Você precisa de uma chave da API Anthropic

Crie sua chave em: https://console.anthropic.com/
