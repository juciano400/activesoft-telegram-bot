# Bot de Registro de Aulas - Activesoft (Telegram)

Este bot permite registrar o conteúdo das aulas no portal Activesoft diretamente pelo Telegram.

## 🚀 Como Configurar

### 1. Criar o Bot no Telegram
1. Fale com o [@BotFather](https://t.me/botfather) no Telegram.
2. Use o comando `/newbot` e siga as instruções para dar um nome e um username ao seu bot.
3. O BotFather enviará um **API TOKEN**. Guarde-o.

### 2. Configurar o Código
No arquivo `activesoft_bot.py`, substitua a linha:
```python
TOKEN = 'SEU_TELEGRAM_BOT_TOKEN'
```
Pelo token que você recebeu do BotFather.

### 3. Instalar Dependências
Você precisará do Python instalado. Instale as bibliotecas necessárias:
```bash
pip install pyTelegramBotAPI requests
```

## ☁️ Onde Hospedar Grátis (24/7)

Como o bot precisa estar "sempre ligado", você pode usar um destes serviços gratuitos:

### Opção A: PythonAnywhere (Recomendado para Iniciantes)
1. Crie uma conta em [pythonanywhere.com](https://www.pythonanywhere.com/).
2. No painel, vá em **Files** e faça o upload do seu arquivo `activesoft_bot.py`.
3. Vá em **Consoles** -> **Bash** e instale a biblioteca: `pip3 install --user pyTelegramBotAPI`.
4. Para rodar o bot: `python3 activesoft_bot.py`.
*Nota: Na conta gratuita, você precisará clicar em um botão no site uma vez por dia para manter o bot rodando.*

### Opção B: Render ou Railway
Estes serviços permitem rodar processos em segundo plano.
1. Crie um repositório no GitHub com o arquivo `activesoft_bot.py` e um arquivo chamado `requirements.txt` contendo:
   ```text
   pyTelegramBotAPI
   requests
   ```
2. Conecte seu GitHub ao [Render.com](https://render.com) ou [Railway.app](https://railway.app).
3. Escolha o tipo de serviço "Background Worker".

## 🛠️ Comandos do Bot
- `/start`: Inicia a conversa.
- `/registrar`: Inicia o processo de registro de uma nova aula (Data, Conteúdo e Tarefa).

---
**Segurança:** Suas credenciais já estão configuradas no código conforme solicitado. Se desejar mudar de conta, basta editar as variáveis `USERNAME` e `PASSWORD` no arquivo.
