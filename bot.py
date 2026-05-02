import os
import requests
from telebot import TeleBot, types
from datetime import datetime
from bs4 import BeautifulSoup
import threading
from flask import Flask
import re

# --- CONFIGURAÇÃO DO SERVIDOR WEB PARA O RENDER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÕES DE SEGURANÇA ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = TeleBot(TOKEN) if TOKEN else None

# Configurações Activesoft
LOGIN_URL = "https://siga03.activesoft.com.br/login/"
GRAVAR_URL_BASE = "https://app52.activesoft.com.br/sistema/sistema.1065614/TelasSIGA/Diario/RegistroAulasGravar.asp"

# Dados do usuário
INSTITUICAO = "AGAPE"
USERNAME = "juciano"
PASSWORD = "#Agape2025"

MY_CLASSES = [
    {"key": "1AL", "turma": "1ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "389", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - LITERATURA"},
    {"key": "1AR", "turma": "1ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "389", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - REDAÇÃO"},
    {"key": "1AC", "turma": "1ª SÉRIE - A", "disciplina": "CIÊNCIAS FORENSES", "id_turma": "389", "id_disciplina": "77", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - A - Ciências Forenses: Investigação Criminal"},
    {"key": "1BL", "turma": "1ª SÉRIE - B", "disciplina": "LITERATURA", "id_turma": "390", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - LITERATURA"},
    {"key": "1BR", "turma": "1ª SÉRIE - B", "disciplina": "REDAÇÃO", "id_turma": "390", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - REDAÇÃO"},
    {"key": "1BC", "turma": "1ª SÉRIE - B", "disciplina": "CIÊNCIAS FORENSES", "id_turma": "390", "id_disciplina": "77", "disciplina_full": "Ensino Médio / 1ª Série / 2026 / 1ª SÉRIE - B - Ciências Forenses: Investigação Criminal"},
    {"key": "2AL", "turma": "2ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "387", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 2ª Série / 2026 / 2ª SÉRIE - A - LITERATURA"},
    {"key": "2AR", "turma": "2ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "387", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 2ª Série / 2026 / 2ª SÉRIE - A - REDAÇÃO"},
    {"key": "3AL", "turma": "3ª SÉRIE - A", "disciplina": "LITERATURA", "id_turma": "388", "id_disciplina": "2", "disciplina_full": "Ensino Médio / 3ª Série / 2026 / 3ª SÉRIE - A - LITERATURA"},
    {"key": "3AR", "turma": "3ª SÉRIE - A", "disciplina": "REDAÇÃO", "id_turma": "388", "id_disciplina": "3", "disciplina_full": "Ensino Médio / 3ª Série / 2026 / 3ª SÉRIE - A - REDAÇÃO"},
    {"key": "3AC", "turma": "3ª SÉRIE - A", "disciplina": "CIÊNCIAS FORENSES", "id_turma": "388", "id_disciplina": "77", "disciplina_full": "Ensino Médio / 3ª Série / 2026 / 3ª SÉRIE - A - Ciências Forenses: Investigação Criminal"},
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

def parse_fast_command(text):
    # Padrão: 1A Lit Conteudo / Tarefa
    # Ou: 1A Red Conteudo / Tarefa
    text = text.replace("registra", "").replace("aula de hoje na", "").replace("aula de hoje no", "").strip()
    
    # Identificar Turma e Disciplina
    match_class = re.search(r'([123])\s*([AB])', text, re.I)
    if not match_class: return None
    serie = match_class.group(1)
    turma = match_class.group(2).upper()
    
    disc_key = ""
    if "lit" in text.lower(): disc_key = "L"
    elif "red" in text.lower(): disc_key = "R"
    elif "fore" in text.lower() or "cien" in text.lower(): disc_key = "C"
    
    final_key = f"{serie}{turma}{disc_key}"
    selected_class = next((c for c in MY_CLASSES if c['key'] == final_key), None)
    if not selected_class: return None
    
    # Extrair Conteúdo e Tarefa (separados por 'tarefa' ou '/')
    content_part = text
    # Limpar a parte da turma/disciplina do texto
    content_part = re.sub(r'[123]\s*[AB]', '', content_part, flags=re.I)
    content_part = re.sub(r'(lit|red|fore|cien)[a-z]*', '', content_part, flags=re.I)
    content_part = content_part.replace("sobre", "").strip()
    
    tarefa = ""
    if "tarefa" in content_part.lower():
        parts = re.split(r'tarefa', content_part, flags=re.I)
        conteudo = parts[0].strip()
        tarefa = parts[1].strip()
    elif "/" in content_part:
        parts = content_part.split("/")
        conteudo = parts[0].strip()
        tarefa = parts[1].strip()
    else:
        conteudo = content_part.strip()
        
    return {
        'class': selected_class,
        'data': datetime.now().strftime("%d/%m/%Y"),
        'conteudo': conteudo,
        'tarefa': tarefa,
        'bimestre': {"label": "2º Bimestre", "id": "9220"} # Padrão atual
    }

if bot:
    @bot.message_handler(commands=['start'])
    def start_cmd(message):
        bot.send_message(message.chat.id, "🚀 **Bot Professor Juciano v9.0 (Ultra Rápido)**\n\n"
                                         "Agora sem IA para ser infalível! Basta mandar assim:\n\n"
                                         "`1A Lit Trovadorismo tarefa ler livro`\n"
                                         "`2A Red Coesão / Exercícios pág 10`\n\n"
                                         "Ou use /registrar para o menu passo a passo.")

    @bot.message_handler(commands=['registrar'])
    def manual_registrar(message):
        chat_id = message.chat.id
        user_state[chat_id] = {'classes': MY_CLASSES}
        markup = types.InlineKeyboardMarkup()
        turmas_unicas = sorted(list(set([c['turma'] for c in MY_CLASSES])))
        for t in turmas_unicas: markup.add(types.InlineKeyboardButton(f"🏫 {t}", callback_data=f"sel_turma_{t}"))
        bot.send_message(chat_id, "Selecione a Turma:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('sel_turma_'))
    def handle_turma_selection(call):
        chat_id = call.message.chat.id
        turma_nome = call.data.replace('sel_turma_', '')
        disciplinas = [c for c in MY_CLASSES if c['turma'] == turma_nome]
        user_state[chat_id]['temp_disciplinas'] = disciplinas
        markup = types.InlineKeyboardMarkup()
        for i, d in enumerate(disciplinas): markup.add(types.InlineKeyboardButton(f"📚 {d['disciplina']}", callback_data=f"sel_disc_{i}"))
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
    def handle_fast_mode(message):
        chat_id = message.chat.id
        
        # Se estiver no fluxo manual
        if chat_id in user_state and 'step' in user_state[chat_id]:
            if user_state[chat_id]['step'] == 'data': get_date(message); return
            elif user_state[chat_id]['step'] == 'manual_content': manual_content(message); return
            elif user_state[chat_id]['step'] == 'manual_task': manual_task(message); return
            elif user_state[chat_id]['step'] == 'final_confirm': finalize_from_button(message); return

        # Modo Rápido (Lógica Direta)
        res = parse_fast_command(message.text)
        if res:
            user_state[chat_id] = {
                'selected_class': res['class'],
                'data': res['data'],
                'selected_bim': res['bimestre'],
                'conteudo': res['conteudo'],
                'tarefa': res['tarefa'],
                'step': 'final_confirm'
            }
            summary = (f"📝 **Resumo do Registro**\n\n"
                       f"🏫 **Turma:** {res['class']['turma']}\n"
                       f"📚 **Disc:** {res['class']['disciplina']}\n"
                       f"📅 **Data:** {res['data']}\n"
                       f"📖 **Conteúdo:** {res['conteudo']}\n"
                       f"📝 **Tarefa:** {res['tarefa']}\n\n"
                       f"Confirma o envio?")
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Confirmar Envio', 'Cancelar')
            bot.send_message(chat_id, summary, reply_markup=markup)
        else:
            bot.send_message(chat_id, "😅 Não entendi o comando rápido. Tente:\n`1A Lit Trovadorismo tarefa ler livro` ou use /registrar")

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
        summary = f"🚀 **Confirmar?**\n\n📅 {state['data']}\n🏫 {state['selected_class']['turma']}\n📖 {state['conteudo']}\n📝 {state['tarefa']}"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Confirmar Envio', 'Cancelar')
        bot.send_message(chat_id, summary, reply_markup=markup)
        user_state[chat_id]['step'] = 'final_confirm'

    def finalize_from_button(message):
        chat_id = message.chat.id
        if message.text == 'Cancelar':
            bot.send_message(chat_id, "Cancelado.", reply_markup=types.ReplyKeyboardRemove())
            user_state.pop(chat_id, None); return
        if message.text == 'Confirmar Envio':
            bot.send_message(chat_id, "Enviando para o Activesoft...", reply_markup=types.ReplyKeyboardRemove())
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
                if res.status_code == 200:
                    bot.send_message(chat_id, "✅ Registro concluído com sucesso!")
                else:
                    bot.send_message(chat_id, f"❌ Erro no Activesoft: Status {res.status_code}")
            except Exception as e:
                bot.send_message(chat_id, f"❌ Erro técnico: {str(e)}")
            user_state.pop(chat_id, None)

    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
else:
    print("ERRO: TOKEN não encontrado.")
