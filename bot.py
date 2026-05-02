import os
import requests
from telebot import TeleBot, types
from datetime import datetime
from bs4 import BeautifulSoup
import json

# --- CONFIGURAÇÕES DE SEGURANÇA ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TOKEN or not GEMINI_API_KEY:
    print("ERRO CRÍTICO: Variáveis de ambiente TELEGRAM_TOKEN ou GEMINI_API_KEY não configuradas!")

bot = TeleBot(TOKEN) if TOKEN else None

# Configuração Gemini Estável
GEMINI_MODEL = "gemini-1.5-flash"

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

def call_gemini(prompt, chat_id=None):
    # Usando a URL estável v1
    url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        res_json = res.json()
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            error_msg = res_json.get('error', {}).get('message', 'Erro desconhecido')
            if chat_id:
                bot.send_message(chat_id, f"❌ Erro na IA: {error_msg}")
            return None
    except Exception as e:
        if chat_id:
            bot.send_message(chat_id, f"❌ Erro técnico: {str(e)}")
        return None

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "👋 Professor Juciano! Versão 8.2 Estável Ativa.\n\n"
                                     "Tente: *'Registra aula de hoje na 1A de Literatura sobre Barroco'*")

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
    hoje = datetime.now()
    
    prompt = (
        f"Analise: '{message.text}'. Hoje: {hoje.strftime('%d/%m/%Y')}.\n"
        "Turmas (class_idx):\n"
        + "\n".join([f"{i}: {c['turma']} - {c['disciplina']}" for i, c in enumerate(MY_CLASSES)]) +
        "\nRegras: Identifique class_idx, data (DD/MM/AAAA), bim_idx (padrão 1), registro detalhado com BNCC, tarefa.\n"
        "Retorne JSON: {'class_idx': int, 'data': 'string', 'bim_idx': int, 'registro': 'string', 'tarefa': 'string'}"
    )
    
    ai_response = call_gemini(prompt, chat_id)
    if not ai_response: return

    try:
        data = json.loads(ai_response)
        user_state[chat_id] = {
            'selected_class': MY_CLASSES[int(data['class_idx'])],
            'data': data['data'],
            'selected_bim': [{"label": "1º Bimestre", "id": "9219"}, {"label": "2º Bimestre", "id": "9220"}, {"label": "3º Bimestre", "id": "9221"}, {"label": "4º Bimestre", "id": "9222"}][int(data['bim_idx'])],
            'conteudo': data['registro'],
            'tarefa': data['tarefa']
        }
        summary = f"🧠 **Assistente**\n\n🏫 **Turma:** {user_state[chat_id]['selected_class']['turma']}\n📚 **Disc:** {user_state[chat_id]['selected_class']['disciplina']}\n📅 **Data:** {user_state[chat_id]['data']}\n📖 **Reg:** {user_state[chat_id]['conteudo']}\n📝 **Tarefa:** {user_state[chat_id]['tarefa']}\n\nDeseja confirmar?"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Confirmar Envio', 'Cancelar')
        bot.send_message(chat_id, summary, reply_markup=markup)
        user_state[chat_id]['step'] = 'final_confirm'
    except Exception:
        bot.send_message(chat_id, "😅 Não entendi. Tente: 'Registra aula de hoje na 1A de Literatura sobre Barroco'.")

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
    summary = f"🚀 **Confirmar?**\n\n📅 {state['data']}\n🏫 {state['selected_class']['turma']}\n📖 {state['conteudo'][:100]}...\n📝 {state['tarefa']}"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Confirmar Envio', 'Cancelar')
    bot.send_message(chat_id, summary, reply_markup=markup)
    user_state[chat_id]['step'] = 'final_confirm'

@bot.message_handler(func=lambda message: message.text in ['Confirmar Envio', 'Cancelar'])
def finalize(message):
    chat_id = message.chat.id
    if message.text == 'Cancelar':
        bot.send_message(chat_id, "Cancelado.", reply_markup=types.ReplyKeyboardRemove())
        user_state.pop(chat_id, None); return
    bot.send_message(chat_id, "Enviando...", reply_markup=types.ReplyKeyboardRemove())
    try:
        state = user_state[chat_id]
        session = get_session()
        payload = {
            "AulaSelecionada": "0", "StRegistroEmEdicao": "0", "DataAulaNovo": state['data'],
            "ConteudoMinistradoNovo": state['conteudo'], "TarefaNovo": state['tarefa'],
            "btnGravarNovo": "Gravar", "IdDiario": state['selected_bim']['id'],
            "Disciplina": state['selected_class']['disciplina_full'], "DescricaoDiario": f"Diário {state['selected_bim']['label']}",
            "IdDisciplina": state['selected_class']['id_disciplina'], "IdTurma": state['selected_class']['id_turma']
        }
        headers = {"Referer": f"https://app52.activesoft.com.br/sistema/sistema.1065614/TelasSIGA/Diario/RegistroAulas.asp?IdDiario={state['selected_bim']['id']}", "Origin": "https://app52.activesoft.com.br"}
        res = session.post(GRAVAR_URL_BASE, data=payload, headers=headers, timeout=20)
        bot.send_message(chat_id, "✅ Registro concluído!" if res.status_code == 200 else f"❌ Erro {res.status_code}")
    except Exception as e: bot.send_message(chat_id, f"❌ Erro: {str(e)}")
    user_state.pop(chat_id, None)

if __name__ == "__main__":
    if bot:
        bot.infinity_polling()
