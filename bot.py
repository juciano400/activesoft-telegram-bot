import os
import requests
from telebot import TeleBot, types
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse
import json

# Configurações do Bot Telegram
TOKEN = '8369730656:AAFeb_zRAm6FUNg0CS3tYkDSLixWUrzWB6Y'
bot = TeleBot(TOKEN)

# Configuração Gemini
GEMINI_API_KEY = 'AIzaSyDRbL1JXrjGWTNq7DoPwOzRKZopYBihD1g'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Configurações Activesoft
LOGIN_URL = "https://siga03.activesoft.com.br/login/"
PORTAL_URL = "https://siga03.activesoft.com.br/portal_eb_professor/"
GRAVAR_URL_BASE = "https://app52.activesoft.com.br/sistema/sistema.1065614/TelasSIGA/Diario/RegistroAulasGravar.asp"

# Dados do usuário
INSTITUICAO = "AGAPE"
USERNAME = "juciano"
PASSWORD = "#Agape2025"

user_state = {}

def get_session():
    # Configurar sessão para ignorar proxies do ambiente que podem causar erro 403 no Railway/PythonAnywhere
    session = requests.Session()
    session.trust_env = False  # Ignora variáveis de ambiente como HTTP_PROXY
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    session.headers.update(headers)
    
    try:
        # 1. Obter CSRF Token
        r_init = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r_init.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        # 2. Login
        login_data = {
            "csrfmiddlewaretoken": csrf_token,
            "codigo": INSTITUICAO,
            "login": USERNAME,
            "senha": PASSWORD,
        }
        session.post(LOGIN_URL, data=login_data, timeout=15)
        return session
    except Exception as e:
        print(f"Erro na sessão: {e}")
        raise e

def get_classes_and_disciplines(session):
    r = session.get(PORTAL_URL, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    data = []
    current_turma = "Turma"
    for element in soup.find_all(['div', 'span', 'strong', 'a']):
        text = element.get_text().strip()
        if "2026 /" in text and "SÉRIE" in text: current_turma = text
        if text == "Diário de classe" and element.name == 'a' and 'href' in element.attrs:
            href = element['href']
            params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            disc_name = "Disciplina"
            parent = element.find_parent('div')
            if parent:
                ft = parent.get_text()
                disc_name = ft.split("Professor")[0].strip() if "Professor" in ft else ft.split("Digitação")[0].strip()
            data.append({"turma": current_turma, "disciplina": disc_name, "id_turma": params.get('IdTurma', [None])[0], "id_disciplina": params.get('IdDisciplina', [None])[0], "disciplina_full": params.get('Disciplina', [''])[0]})
    
    if not data:
        data = [
            {"turma": "1ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "389", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - LITERATURA"},
            {"turma": "1ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "389", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - REDAÇÃO"},
            {"turma": "1ª SÉRIE - B", "disciplina": "LITERATURA", "id_turma": "390", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - LITERATURA"},
        ]
    return data

def call_gemini(prompt):
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=20)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return None

@bot.message_handler(commands=['start', 'registrar'])
def start_cmd(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔍 Buscando turmas no Activesoft...")
    try:
        session = get_session()
        classes = get_classes_and_disciplines(session)
        user_state[chat_id] = {'classes': classes}
        markup = types.InlineKeyboardMarkup()
        for i, item in enumerate(classes):
            btn_text = f"{item['turma'].split('/')[-2].strip() if '/' in item['turma'] else item['turma']} - {item['disciplina']}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"class_{i}"))
        bot.send_message(chat_id, "Selecione a Turma/Disciplina:", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro de Conexão: O servidor de hospedagem está bloqueando o Activesoft. Detalhe: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('class_'))
def handle_class_selection(call):
    chat_id = call.message.chat.id
    idx = int(call.data.split('_')[1])
    user_state[chat_id]['selected_class'] = user_state[chat_id]['classes'][idx]
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

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'data')
def get_date(message):
    chat_id = message.chat.id
    user_state[chat_id]['data'] = datetime.now().strftime("%d/%m/%Y") if message.text.lower() == 'hoje' else message.text
    user_state[chat_id]['step'] = 'conteudo'
    bot.send_message(chat_id, "O que você ensinou hoje?")

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'conteudo')
def get_content(message):
    chat_id = message.chat.id
    raw_content = message.text
    bot.send_message(chat_id, "🤖 Consultando Gemini...")
    
    prompt = f"Como professor de {user_state[chat_id]['selected_class']['disciplina']}, estou registrando a aula: '{raw_content}'. Gere um texto formal para o diário de classe, inclua os códigos das habilidades BNCC relacionadas e sugira uma tarefa de casa curta. Formate como JSON com as chaves: 'registro', 'tarefa'."
    
    ai_response = call_gemini(prompt)
    try:
        clean_json = ai_response.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
        user_state[chat_id]['conteudo'] = data['registro']
        user_state[chat_id]['tarefa'] = data['tarefa']
    except:
        user_state[chat_id]['conteudo'] = raw_content
        user_state[chat_id]['tarefa'] = ""

    summary = f"✨ **Sugestão do Gemini**\n\n📖 **Conteúdo:** {user_state[chat_id]['conteudo']}\n\n📝 **Tarefa:** {user_state[chat_id]['tarefa']}"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Usar Sugestão', 'Escrever meu próprio')
    bot.send_message(chat_id, summary, reply_markup=markup, parse_mode="Markdown")
    user_state[chat_id]['step'] = 'ai_confirm'

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'ai_confirm')
def ai_confirm(message):
    chat_id = message.chat.id
    if message.text == 'Escrever meu próprio':
        bot.send_message(chat_id, "Digite o conteúdo:")
        user_state[chat_id]['step'] = 'manual_content'
    else: finalize_summary(chat_id)

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'manual_content')
def manual_content(message):
    chat_id = message.chat.id
    user_state[chat_id]['conteudo'] = message.text
    bot.send_message(chat_id, "E qual a tarefa?")
    user_state[chat_id]['step'] = 'manual_task'

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'manual_task')
def manual_task(message):
    chat_id = message.chat.id
    user_state[chat_id]['tarefa'] = "" if message.text.lower() == 'não' else message.text
    finalize_summary(chat_id)

def finalize_summary(chat_id):
    state = user_state[chat_id]
    summary = f"🚀 **Confirmar Envio?**\n\n📅 {state['data']}\n📖 {state['conteudo']}\n📝 {state['tarefa']}"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Confirmar Envio', 'Cancelar')
    bot.send_message(chat_id, summary, reply_markup=markup)
    user_state[chat_id]['step'] = 'final_confirm'

@bot.message_handler(func=lambda message: message.text in ['Confirmar Envio', 'Cancelar'])
def finalize(message):
    chat_id = message.chat.id
    if message.text == 'Cancelar':
        bot.send_message(chat_id, "Cancelado.", reply_markup=types.ReplyKeyboardRemove())
        user_state.pop(chat_id, None)
        return
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
        res = session.post(GRAVAR_URL_BASE, data=payload, timeout=20)
        bot.send_message(chat_id, "✅ Registrado!" if res.status_code == 200 else f"❌ Erro: {res.status_code}")
    except Exception as e: bot.send_message(chat_id, f"❌ Erro: {str(e)}")
    user_state.pop(chat_id, None)

if __name__ == "__main__":
    bot.infinity_polling()
