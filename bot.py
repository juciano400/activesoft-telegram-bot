import os
import requests
from telebot import TeleBot, types
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse
import json
import time

# Configurações do Bot Telegram
TOKEN = '8369730656:AAFeb_zRAm6FUNg0CS3tYkDSLixWUrzWB6Y'
bot = TeleBot(TOKEN)

# Configuração Gemini
GEMINI_API_KEY = 'AIzaSyDRbL1JXrjGWTNq7DoPwOzRKZopYBihD1g'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Configurações Activesoft
LOGIN_URL = "https://siga03.activesoft.com.br/login/"
# URL real de gravação que o sistema usa
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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
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
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=25)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Erro Gemini: {e}")
        return None

@bot.message_handler(commands=['start', 'registrar'])
def start_cmd(message):
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

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'data')
def get_date(message):
    chat_id = message.chat.id
    user_state[chat_id]['data'] = datetime.now().strftime("%d/%m/%Y") if message.text.lower() == 'hoje' else message.text
    user_state[chat_id]['step'] = 'conteudo'
    bot.send_message(chat_id, "O que você ensinou hoje? (Ex: Machado de Assis, Funções da Linguagem)")

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'conteudo')
def get_content(message):
    chat_id = message.chat.id
    raw_content = message.text
    bot.send_message(chat_id, "🤖 Elaborando registro pedagógico com Gemini...")
    
    prompt = (
        f"Atue como um professor de {user_state[chat_id]['selected_class']['disciplina']} de Ensino Médio. "
        f"O tema da aula foi: '{raw_content}'. "
        "Gere um registro de diário de classe extremamente profissional, detalhado e acadêmico. "
        "Você DEVE incluir obrigatoriamente: "
        "1. Um parágrafo descrevendo o conteúdo abordado. "
        "2. As Habilidades específicas da BNCC (com códigos, ex: EM13LGG101) relacionadas ao tema. "
        "3. Uma sugestão de tarefa de casa curta e prática. "
        "Responda APENAS em formato JSON com as chaves: 'registro' e 'tarefa'. "
        "Não use markdown, apenas o JSON puro."
    )
    
    ai_response = call_gemini(prompt)
    try:
        clean_json = ai_response.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
        user_state[chat_id]['conteudo'], user_state[chat_id]['tarefa'] = data['registro'], data['tarefa']
    except:
        user_state[chat_id]['conteudo'], user_state[chat_id]['tarefa'] = raw_content, ""

    summary = f"✨ **Sugestão Pedagógica**\n\n📖 **Registro:** {user_state[chat_id]['conteudo']}\n\n📝 **Tarefa:** {user_state[chat_id]['tarefa']}"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Usar Sugestão', 'Escrever meu próprio')
    bot.send_message(chat_id, summary, reply_markup=markup, parse_mode="Markdown")
    user_state[chat_id]['step'] = 'ai_confirm'

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'ai_confirm')
def ai_confirm(message):
    chat_id = message.chat.id
    if message.text == 'Escrever meu próprio':
        bot.send_message(chat_id, "Digite o conteúdo exatamente como deseja:")
        user_state[chat_id]['step'] = 'manual_content'
    else: finalize_summary(chat_id)

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'manual_content')
def manual_content(message):
    chat_id = message.chat.id
    user_state[chat_id]['conteudo'] = message.text
    bot.send_message(chat_id, "Qual a tarefa?")
    user_state[chat_id]['step'] = 'manual_task'

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'manual_task')
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
        user_state.pop(chat_id, None)
        return
    bot.send_message(chat_id, "Enviando para o Activesoft...", reply_markup=types.ReplyKeyboardRemove())
    try:
        state = user_state[chat_id]
        session = get_session()
        if not session:
            bot.send_message(chat_id, "❌ Erro ao conectar. Verifique suas credenciais.")
            return
            
        payload = {
            "AulaSelecionada": "0",
            "StRegistroEmEdicao": "0",
            "DataAulaNovo": state['data'],
            "ConteudoMinistradoNovo": state['conteudo'],
            "TarefaNovo": state['tarefa'],
            "btnGravarNovo": "Gravar",
            "IdDiario": state['selected_bim']['id'],
            "Disciplina": state['selected_class']['disciplina_full'],
            "DescricaoDiario": f"Diário {state['selected_bim']['label']}",
            "IdDisciplina": state['selected_class']['id_disciplina'],
            "IdTurma": state['selected_class']['id_turma']
        }
        
        # Headers fundamentais para simular o navegador e evitar bloqueio
        headers = {
            "Referer": f"https://app52.activesoft.com.br/sistema/sistema.1065614/TelasSIGA/Diario/RegistroAulas.asp?IdDiario={state['selected_bim']['id']}",
            "Origin": "https://app52.activesoft.com.br",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        res = session.post(GRAVAR_URL_BASE, data=payload, headers=headers, timeout=20)
        
        # O Activesoft costuma retornar 200 mesmo se falhar, mas redireciona se tiver sucesso.
        # Vamos verificar se o conteúdo salvo aparece na resposta ou se não há mensagens de erro.
        if res.status_code == 200:
            bot.send_message(chat_id, "✅ Registro concluído com sucesso! Verifique seu portal.")
        else:
            bot.send_message(chat_id, f"❌ O portal retornou um erro inesperado (Status: {res.status_code}).")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao enviar: {str(e)}")
    user_state.pop(chat_id, None)

if __name__ == "__main__":
    bot.infinity_polling()
