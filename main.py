import os
import time
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


load_dotenv()

USUARIO = os.getenv("USUARIO_FATOR")
SENHA = os.getenv("SENHA_FATOR")

if not USUARIO or not SENHA:
    raise ValueError("USUARIO_FATOR ou SENHA_FATOR não encontrados no arquivo .env")


URL_PORTAL = "http://54.94.113.205:8079/pmlaurodefreitas/index.html"

DATA_DESLIGAMENTO_INICIAL = "01/06/2026"
DATA_DESLIGAMENTO_FINAL = "30/06/2026"


def limpar_e_digitar(campo, valor=""):
    campo.click()
    time.sleep(0.2)
    campo.send_keys(Keys.CONTROL, "a")
    time.sleep(0.1)
    campo.send_keys(Keys.DELETE)
    time.sleep(0.1)

    if valor:
        campo.send_keys(valor)
        time.sleep(0.2)


def forcar_valor_extjs(driver, campo, valor=""):
    driver.execute_script("""
        const input = arguments[0];
        const value = arguments[1];

        input.focus();
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));

        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        input.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
        input.blur();

        if (window.Ext) {
            const cmpId = input.getAttribute('data-componentid');
            const cmp = cmpId ? Ext.getCmp(cmpId) : null;

            if (cmp && cmp.setValue) {
                cmp.setValue(value);
                cmp.fireEvent('change', cmp, value);
                cmp.fireEvent('blur', cmp);
            }
        }
    """, campo, valor)

    time.sleep(0.4)


def criar_driver():
    options = Options()
    options.add_argument("--start-maximized")

    options.add_argument(r"--user-data-dir=C:\ChromeRoboFatorRH")
    options.add_argument("--profile-directory=Default")

    # Permitir conteúdo/download inseguro no Chrome do robô
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://54.94.113.205:8079")
    options.add_argument("--disable-features=BlockInsecurePrivateNetworkRequests")
    options.add_argument("--disable-web-security")

    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.insecure_content": 1,
        "profile.default_content_settings.popups": 0,
    }

    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


def fazer_login(driver, wait):
    driver.get(URL_PORTAL)

    time.sleep(5)

    campo_usuario = wait.until(
        EC.visibility_of_element_located((By.ID, "textfield-1026-inputEl"))
    )
    limpar_e_digitar(campo_usuario, USUARIO)
    print("Usuário preenchido.")

    campo_senha = wait.until(
        EC.visibility_of_element_located((By.ID, "textfield-1027-inputEl"))
    )
    limpar_e_digitar(campo_senha, SENHA)
    print("Senha preenchida.")

    wait.until(
        EC.element_to_be_clickable((By.ID, "combobox-1032-trigger-picker"))
    ).click()

    print("Combo aberto.")
    time.sleep(5)

    municipio = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//*[contains(text(),'MUNICIPIO DE LAURO DE FREITAS')]"
        ))
    )
    municipio.click()

    print("Município selecionado.")

    wait.until(
        EC.element_to_be_clickable((By.ID, "button-1036"))
    ).click()

    print("Login realizado.")
    time.sleep(5)


def abrir_listagem_desligados(driver, wait):
    botao_listagem = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//*[contains(text(),'09-Listagem Desligados')]"
        ))
    )

    botao_listagem.click()
    print("Botão 09-Listagem Desligados clicado.")

    time.sleep(5)


def preencher_filtros_desligados(driver, wait):
    time.sleep(5)

    campos_data = wait.until(
        EC.presence_of_all_elements_located((
            By.XPATH,
            "//input[@maxlength='10' and contains(@class,'x-form-field')]"
        ))
    )

    campos_visiveis = [
        campo for campo in campos_data
        if campo.is_displayed() and campo.is_enabled()
    ]

    print(f"Campos de data encontrados: {len(campos_visiveis)}")

    if len(campos_visiveis) < 4:
        raise Exception(
            f"Não encontrei todos os campos de data. Encontrados: {len(campos_visiveis)}"
        )

    forcar_valor_extjs(driver, campos_visiveis[0], "")
    forcar_valor_extjs(driver, campos_visiveis[1], "")
    forcar_valor_extjs(driver, campos_visiveis[2], DATA_DESLIGAMENTO_INICIAL)
    forcar_valor_extjs(driver, campos_visiveis[3], DATA_DESLIGAMENTO_FINAL)

    print("Campos de Data Admissão apagados.")
    print(f"Data inicial de desligamento preenchida: {DATA_DESLIGAMENTO_INICIAL}")
    print(f"Data final de desligamento preenchida: {DATA_DESLIGAMENTO_FINAL}")


def aceitar_download_bloqueado(driver):
    time.sleep(3)

    aba_original = driver.current_window_handle

    driver.execute_script("window.open('chrome://downloads/', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    time.sleep(3)

    try:
        clicou = driver.execute_script("""
            const manager = document.querySelector('downloads-manager');
            if (!manager || !manager.shadowRoot) return false;

            const items = manager.shadowRoot.querySelectorAll('downloads-item');

            for (const item of items) {
                const root = item.shadowRoot;
                if (!root) continue;

                const botoes = [
                    root.querySelector('#keep'),
                    root.querySelector('#save-dangerous'),
                    root.querySelector('#save-dangerous-button'),
                    root.querySelector('cr-button[focus-type="save"]')
                ];

                for (const botao of botoes) {
                    if (botao) {
                        botao.click();
                        return true;
                    }
                }
            }

            return false;
        """)

        if clicou:
            print("Clique em 'Manter' executado.")
        else:
            print("Botão 'Manter' não encontrado em chrome://downloads.")

    except Exception as e:
        print(f"Erro ao tentar aceitar download bloqueado: {e}")

    time.sleep(2)

    driver.close()
    driver.switch_to.window(aba_original)


def selecionar_xlsx_e_baixar(driver, wait):
    time.sleep(2)

    campo_pdf = wait.until(
        EC.presence_of_element_located((
            By.XPATH,
            "//input[contains(@value,'PDF - Adobe Reader')]"
        ))
    )

    seta_combo = campo_pdf.find_element(
        By.XPATH,
        "./ancestor::div[contains(@class,'x-form-trigger-wrap')]//div[contains(@class,'x-form-arrow-trigger')]"
    )

    driver.execute_script("arguments[0].click();", seta_combo)

    print("Seta do combo clicada.")

    time.sleep(1)

    campo_pdf.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.5)
    campo_pdf.send_keys(Keys.ENTER)

    print("Tentativa de selecionar XLSX com seta para baixo + ENTER.")

    time.sleep(1)

    valor_atual = campo_pdf.get_attribute("value")
    print(f"Formato selecionado agora: {valor_atual}")

    botao_ok = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//span[normalize-space()='Ok']/ancestor::a[contains(@class,'x-btn')]"
        ))
    )

    botao_ok.click()

    print("OK clicado. Download solicitado.")

    aceitar_download_bloqueado(driver)

    time.sleep(10)


def executar():
    driver = criar_driver()
    wait = WebDriverWait(driver, 30)

    try:
        fazer_login(driver, wait)
        abrir_listagem_desligados(driver, wait)
        preencher_filtros_desligados(driver, wait)
        selecionar_xlsx_e_baixar(driver, wait)

        print("Processo executado com sucesso.")

        input("\nPressione ENTER para fechar...")

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        input("\nErro encontrado. Pressione ENTER para fechar...")

    finally:
        driver.quit()


if __name__ == "__main__":
    executar()