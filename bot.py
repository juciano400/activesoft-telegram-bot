import os
import requests
from telebot import TeleBot, types
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import urllib.parse
import json
import time
import re

# Configurações do Bot Telegram
TOKEN = '8369730656:AAFeb_zRAm6FUNg0CS3tYkDSLixWUrzWB6Y'
bot = TeleBot(TOKEN)

# Configuração Gemini - Usando v1beta para suporte a JSON mode se necessário, mas mantendo estável
GEMINI_API_KEY = 'AIzaSyDRbL1JXrjGWTNq7DoPwOzRKZopYBihD1g'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Configurações Activesoft
LOGIN_URL = "https://siga03.activesoft.com.br/login/"
GRAVAR_URL_BASE = "https://app52.activesoft.com.br/sistema/sistema.1065614/TelasSIGA/Diario/RegistroAulasGravar.asp"

# Dados do usuário
INSTITUICAO = "AGAPE"
USERNAME = "juciano"
PASSWORD = "#Agape2025"

MY_CLASSES = [
    {"turma": "1ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "389", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - LITERATURA"},
    {"turma": "1ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "389", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - REDAÇÃO"},
    {"turma": "1ª SÉRIE - A", "disciplina": "CIÊNCIAS FORENSES", "id_turma": "389", "id_disciplina": "77", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - Ciências Forenses: Investigação Criminal"},
    {"turma": "1ª SÉRIE - B", "disciplina": "LITERATURA", "id_turma": "390", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - LITERATURA"},
    {"turma": "1ª SÉRIE - B", "disciplina": "REDAÇÃO", "id_turma": "390", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - REDAÇÃO"},
    {"turma": "1ª SÉRIE - B", "disciplina": "CIÊNCIAS FORENSES", "id_turma": "390", "id_disciplina": "77", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - Ciências Forenses: Investigação Criminal"},
    {"turma": "2ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "387", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 2ª Série / 2026 / 2ª SÉRIE - A - LITERATURA"},
    {"turma": "2ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "387", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 2ª Série / 2026 / 2ª SÉRIE - A - REDAÇÃO"},
    {"turma": "3ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "388", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 3ª Série / 2026 / 3ª SÉRIE - A - LITERATURA"},
    {"turma": "3ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "388", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 3ª Série / 2026 / 3ª SÉRIE - A - REDAÇÃO"},
    {"turma": "3ª SÉRIE - A", "disciplina": "CIÊNCIAS FORENSES", "id_turma": "388", "id_disciplina": "77", "disciplina_full": "Ensino Médio / 3ª Série / 2026 / 3ª SÉRIE - A - Ciências Forenses: Investigação Criminal"},
]

user_state = {}

def get_session():
    session = requests.Session()
    session.trust_env = False
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    session.headers.update(headers)
    try:
        r_init = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r_init.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        login_data = {"csrfmiddlewaretoken": csrf_token, "codigo": INSTITUICAO, "login": USERNAME, "senha": PASSWORD}
        session.post(LOGIN_URL, data=login_data, timeout=15)
        return session
    except Exception as e:
        print(f"Erro login: {e}")
        return None

def call_gemini(prompt):
    headers = {'Content-Type': 'application/json'}
    # Adicionando resposta forçada em JSON
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }
    try:
        res = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=30)
        res_json = res.json()
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Resposta inesperada do Gemini: {res_json}")
            return None
    except Exception as e:
        print(f"Erro Gemini: {e}")
        return None

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "👋 Olá Professor Juciano! Eu sou seu assistente inteligente para o Activesoft.\n\n"
                                     "Agora você pode registrar suas aulas de duas formas:\n\n"
                                     "1️⃣ **Manual:** Digite /registrar e siga os botões.\n"
                                     "2️⃣ **Inteligente:** Basta me mandar uma mensagem direta! \n"
                                     "Ex: *'Registra aula de hoje na 1A de Literatura sobre Romantismo e tarefa ler pag 10'*")

@bot.message_handler(commands=['registrar'])
def manual_registrar(message):
    chat_id = message.chat.id
    user_state[chat_id] = {'classes': MY_CLASSES}
    markup = types.InlineKeyboardMarkup()
    turmas_unicas = sorted(list(set([c['turma'] for c in MY_CLASSES])))
    for t in turmas_unicas:
        markup.add(types.InlineKeyboardButton(f"🏫 {t}", callback_data=f"sel_turma_{t}"))
    bot.send_message(chat_id, "Selecione a Turma:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('sel_turma_'))
def handle_turma_selection(call):
    chat_id = call.message.chat.id
    turma_nome = call.data.replace('sel_turma_', '')
    disciplinas = [c for c in MY_CLASSES if c['turma'] == turma_nome]
    user_state[chat_id]['temp_disciplinas'] = disciplinas
    markup = types.InlineKeyboardMarkup()
    for i, d in enumerate(disciplinas):
        markup.add(types.InlineKeyboardButton(f"📚 {d['disciplina']}", callback_data=f"sel_disc_{i}"))
    bot.edit_message_text(f"Turma: {turma_nome}\nEscolha a Disciplina:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('sel_disc_'))
def handle_disc_selection(call):
    chat_id = call.message.chat.id
    idx = int(call.data.replace('sel_disc_', ''))
    user_state[chat_id]['selected_class'] = user_state[chat_id]['temp_disciplinas'][idx]
    markup = types.InlineKeyboardMarkup()
    bimestres = [{"label": "1º Bimestre", "id": "9219"}, {"label": "2º Bimestre", "id": "9220"}, {"label": "3º Bimestre", "id": "9221"}, {"label": "4º Bimestre", "id": "9222"}]
    user_state[chat_id]['bimestres'] = bimestres
    for i, b in enumerate(bimestres): markup.add(types.InlineKeyboardButton(b['label'], callback_data=f"bim_{i}"))
    bot.edit_message_text("Escolha o Bimestre:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('bim_'))
def handle_bim_selection(call):
    chat_id = call.message.chat.id
    user_state[chat_id]['selected_bim'] = user_state[chat_id]['bimestres'][int(call.data.split('_')[1])]
    bot.send_message(chat_id, "Data da aula? (DD/MM/AAAA ou 'hoje')")
    user_state[chat_id]['step'] = 'data'

@bot.message_handler(func=lambda message: True)
def handle_nlp(message):
    chat_id = message.chat.id
    if chat_id in user_state and 'step' in user_state[chat_id]:
        if user_state[chat_id]['step'] == 'data': get_date(message); return
        elif user_state[chat_id]['step'] == 'manual_content': manual_content(message); return
        elif user_state[chat_id]['step'] == 'manual_task': manual_task(message); return

    bot.send_chat_action(chat_id, 'typing')
    
    # Datas relativas
    hoje = datetime.now()
    amanha = hoje + timedelta(days=1)
    ontem = hoje - timedelta(days=1)
    
    prompt = (
        f"Analise a solicitação: '{message.text}'. "
        f"Hoje é {hoje.strftime('%d/%m/%Y')}. "
        "Extraia os dados para o diário escolar em JSON.\n"
        "Turmas disponíveis (índices):\n"
        + "\n".join([f"{i}: {c['turma']} - {c['disciplina']}" for i, c in enumerate(MY_CLASSES)]) +
        "\n\nRegras:\n"
        "1. Identifique o 'class_idx' correto.\n"
        "2. Identifique a 'data' (formato DD/MM/AAAA).\n"
        "3. 'bim_idx' padrão é 1 (2º Bimestre).\n"
        "4. Crie um 'registro' pedagógico detalhado com habilidades BNCC.\n"
        "5. Extraia a 'tarefa'.\n"
        "Retorne APENAS o JSON: {'class_idx': int, 'data': 'string', 'bim_idx': int, 'registro': 'string', 'tarefa': 'string'}"
    )
    
    ai_response = call_gemini(prompt)
    if not ai_response:
        bot.send_message(chat_id, "❌ Erro ao conectar com o Gemini. Tente novamente em instantes.")
        return

    try:
        data = json.loads(ai_response)
        idx = int(data['class_idx'])
        user_state[chat_id] = {
            'selected_class': MY_CLASSES[idx],
            'data': data['data'],
            'selected_bim': [{"label": "1º Bimestre", "id": "9219"}, {"label": "2º Bimestre", "id": "9220"}, {"label": "3º Bimestre", "id": "9221"}, {"label": "4º Bimestre", "id": "9222"}][int(data['bim_idx'])],
            'conteudo': data['registro'],
            'tarefa': data['tarefa']
        }
        
        summary = (
            f"🧠 **Entendi seu pedido!**\n\n"
            f"🏫 **Turma:** {user_state[chat_id]['selected_class']['turma']}\n"
            f"📚 **Disciplina:** {user_state[chat_id]['selected_class']['disciplina']}\n"
            f"📅 **Data:** {user_state[chat_id]['data']}\n"
            f"📖 **Registro:** {user_state[chat_id]['conteudo']}\n"
            f"📝 **Tarefa:** {user_state[chat_id]['tarefa'] or 'Nenhuma'}\n\n"
            f"Deseja confirmar o envio?"
        )
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Confirmar Envio', 'Cancelar')
        bot.send_message(chat_id, summary, reply_markup=markup, parse_mode="Markdown")
        user_state[chat_id]['step'] = 'final_confirm'
        
    except Exception as e:
        print(f"Erro processamento JSON: {e}\nResposta: {ai_response}")
        bot.send_message(chat_id, "😅 Não entendi bem. Tente algo como: 'Registra aula de hoje na 1A de Literatura sobre Barroco'.")

def get_date(message):
    chat_id = message.chat.id
    user_state[chat_id]['data'] = datetime.now().strftime("%d/%m/%Y") if message.text.lower() == 'hoje' else message.text
    user_state[chat_id]['step'] = 'manual_content'
    bot.send_message(chat_id, "O que você ensinou hoje?")

def manual_content(message):
    chat_id = message.chat.id
    user_state[chat_id]['conteudo'] = message.text
    bot.send_message(chat_id, "Qual a tarefa?")
    user_state[chat_id]['step'] = 'manual_task'

def manual_task(message):
    chat_id = message.chat.id
    user_state[chat_id]['tarefa'] = "" if message.text.lower() in ['não', 'nao', 'nada'] else message.text
    finalize_summary(chat_id)

def finalize_summary(chat_id):
    state = user_state[chat_id]
    summary = f"🚀 **Confirmar Envio Final?**\n\n📅 Data: {state['data']}\n🏫 Turma: {state['selected_class']['turma']}\n📚 Disciplina: {state['selected_class']['disciplina']}\n📖 Registro: {state['conteudo'][:100]}...\n📝 Tarefa: {state['tarefa']}"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Confirmar Envio', 'Cancelar')
    bot.send_message(chat_id, summary, reply_markup=markup)
    user_state[chat_id]['step'] = 'final_confirm'

@bot.message_handler(func=lambda message: message.text in ['Confirmar Envio', 'Cancelar'])
def finalize(message):
    chat_id = message.chat.id
    if message.text == 'Cancelar':
        bot.send_message(chat_id, "Operação cancelada.", reply_markup=types.ReplyKeyboardRemove())
        user_state.pop(chat_id, None); return
    
    bot.send_message(chat_id, "Enviando para o Activesoft...", reply_markup=types.ReplyKeyboardRemove())
    try:
        state = user_state[chat_id]
        session = get_session()
        if not session: bot.send_message(chat_id, "❌ Erro de login."); return
            
        payload = {
            "AulaSelecionada": "0", "StRegistroEmEdicao": "0", "DataAulaNovo": state['data'],
            "ConteudoMinistradoNovo": state['conteudo'], "TarefaNovo": state['tarefa'],
            "btnGravarNovo": "Gravar", "IdDiario": state['selected_bim']['id'],
            "Disciplina": state['selected_class']['disciplina_full'], "DescricaoDiario": f"Diário {state['selected_bim']['label']}",
            "IdDisciplina": state['selected_class']['id_disciplina'], "IdTurma": state['selected_class']['id_turma']
        }
        headers = {"Referer": f"https://app52.activesoft.com.br/sistema/sistema.1065614/TelasSIGA/Diario/RegistroAulas.asp?IdDiario={state['selected_bim']['id']}", "Origin": "https://app52.activesoft.com.br"}
        res = session.post(GRAVAR_URL_BASE, data=payload, headers=headers, timeout=20)
        bot.send_message(chat_id, "✅ Registro concluído com sucesso!" if res.status_code == 200 else f"❌ Erro {res.status_code}")
    except Exception as e: bot.send_message(chat_id, f"❌ Erro: {str(e)}")
    user_state.pop(chat_id, None)

if __name__ == "__main__":
    bot.infinity_polling()
