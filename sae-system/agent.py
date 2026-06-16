"""
Agente Claude com ferramentas de controle do navegador SAE.
"""
import anthropic
import sae_browser

client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "login_sae",
        "description": "Faz login no SAE digital. Use sempre antes de navegar.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "navigate",
        "description": "Navega para uma URL no SAE.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL completa para navegar"}},
            "required": ["url"],
        },
    },
    {
        "name": "get_page_text",
        "description": "Retorna o texto visível da página atual. Use para ler dados, tabelas, resultados.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_page_url",
        "description": "Retorna a URL da página atual.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "find_links",
        "description": "Lista os links disponíveis na página atual. Use para descobrir onde navegar.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "click_element",
        "description": "Clica em um elemento da página usando CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string", "description": "CSS selector do elemento"}},
            "required": ["selector"],
        },
    },
    {
        "name": "fill_input",
        "description": "Preenche um campo de texto na página.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector do input"},
                "value": {"type": "string", "description": "Valor a preencher"},
            },
            "required": ["selector", "value"],
        },
    },
]

SYSTEM_PROMPT = """Você é um assistente especializado em navegar no SAE Digital (app.sae.digital) para o Prof. Juciano do Colégio Ágape.

Você tem acesso a ferramentas para controlar um navegador que está logado no SAE.

URLs úteis conhecidas:
- Painel: https://app.sae.digital/painel/
- Relatório específico: https://app.sae.digital/conteudo/materiais/68c1b413232cab0181339bd3/secoes/68c1b413232cab0181339bb7/?tab=relatorio

Instruções:
1. Se ainda não estiver logado (primeira pergunta), faça login primeiro.
2. Navegue pelas páginas para encontrar a informação pedida.
3. Leia o conteúdo das páginas e extraia os dados relevantes.
4. Responda de forma clara e direta em português.
5. Se encontrar tabelas com alunos, notas ou resultados, organize-os bem na resposta.
"""

_logged_in = False
_messages = []


def run_tool(name: str, inputs: dict) -> str:
    global _logged_in
    if name == "login_sae":
        result = sae_browser.login()
        if "OK" in result:
            _logged_in = True
        return result
    elif name == "navigate":
        return sae_browser.navigate(inputs["url"])
    elif name == "get_page_text":
        return sae_browser.get_page_text()
    elif name == "get_page_url":
        return sae_browser.get_page_url()
    elif name == "find_links":
        return sae_browser.find_links()
    elif name == "click_element":
        return sae_browser.click_element(inputs["selector"])
    elif name == "fill_input":
        return sae_browser.fill_input(inputs["selector"], inputs["value"])
    return "Ferramenta desconhecida."


def chat(user_message: str) -> str:
    global _messages, _logged_in

    if not _logged_in:
        _messages.append({
            "role": "user",
            "content": f"[Sistema: Você ainda não está logado no SAE. Faça login antes de responder.]\n\n{user_message}"
        })
    else:
        _messages.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=_messages,
        )

        _messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "Sem resposta."

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[Tool] {block.name}({block.input})")
                    result = run_tool(block.name, block.input)
                    print(f"[Result] {result[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            _messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Processo concluído."


def reset_chat():
    global _messages, _logged_in
    _messages = []
    _logged_in = False
    sae_browser.close()
