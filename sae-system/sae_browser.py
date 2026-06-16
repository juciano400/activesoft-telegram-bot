"""
Controle do navegador SAE via Playwright.
Mantém uma sessão logada e expõe ações para o agente de IA.
"""
import os
from playwright.sync_api import sync_playwright, Page, Browser

CHROMIUM_PATH = os.getenv("CHROMIUM_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
SAE_EMAIL = os.getenv("SAE_EMAIL", "")
SAE_PASSWORD = os.getenv("SAE_PASSWORD", "")
LOGIN_URL = "https://app.sae.digital/login"

_pw = None
_browser: Browser = None
_page: Page = None


def _launch():
    global _pw, _browser, _page
    _pw = sync_playwright().start()
    launch_kwargs = {
        "headless": True,
        "args": ["--ignore-certificate-errors", "--no-sandbox", "--disable-setuid-sandbox"],
    }
    if CHROMIUM_PATH:
        launch_kwargs["executable_path"] = CHROMIUM_PATH
    _browser = _pw.chromium.launch(**launch_kwargs)
    context = _browser.new_context(ignore_https_errors=True)
    _page = context.new_page()


def get_page() -> Page:
    global _page
    if _page is None:
        _launch()
    return _page


def login() -> str:
    page = get_page()
    page.goto(LOGIN_URL, timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)

    page.fill('input[type="email"]', SAE_EMAIL)
    page.fill('input[type="password"]', SAE_PASSWORD)
    page.click('button[type="submit"]')

    try:
        page.wait_for_url("**/painel/**", timeout=15000)
    except Exception:
        page.wait_for_load_state("networkidle", timeout=10000)

    if "login" in page.url:
        return "ERRO: Login falhou. Verifique credenciais."
    return f"Login OK. URL atual: {page.url}"


def navigate(url: str) -> str:
    page = get_page()
    page.goto(url, timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)
    return f"Navegou para: {page.url}"


def get_page_text() -> str:
    page = get_page()
    text = page.evaluate("() => document.body.innerText")
    return text[:8000]


def get_page_url() -> str:
    return get_page().url


def click_element(selector: str) -> str:
    page = get_page()
    try:
        page.click(selector, timeout=5000)
        page.wait_for_load_state("networkidle", timeout=8000)
        return f"Clicou em '{selector}'. URL: {page.url}"
    except Exception as e:
        return f"Erro ao clicar: {str(e)}"


def fill_input(selector: str, value: str) -> str:
    page = get_page()
    try:
        page.fill(selector, value, timeout=5000)
        return f"Preencheu '{selector}' com '{value}'"
    except Exception as e:
        return f"Erro ao preencher: {str(e)}"


def find_links() -> str:
    page = get_page()
    links = page.evaluate("""
        () => [...document.querySelectorAll('a[href]')]
            .map(a => ({ text: a.innerText.trim(), href: a.href }))
            .filter(l => l.text && l.href.startsWith('http'))
            .slice(0, 30)
    """)
    return "\n".join([f"- {l['text']}: {l['href']}" for l in links])


def close():
    global _pw, _browser, _page
    if _browser:
        _browser.close()
    if _pw:
        _pw.stop()
    _pw = _browser = _page = None
