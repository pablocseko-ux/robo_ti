import os
import time
import calendar
from datetime import datetime

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


PASTA_RELATORIOS = r"\\srvan2\DTIC SECAD\RPA RH\Entrada\2026"

MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def obter_data_execucao():
    hoje = datetime.now()

    ano = hoje.year
    mes = hoje.month

    primeiro_dia = datetime(ano, mes, 1)
    ultimo_dia_numero = calendar.monthrange(ano, mes)[1]
    ultimo_dia = datetime(ano, mes, ultimo_dia_numero)

    data_inicial = primeiro_dia.strftime("%d/%m/%Y")
    data_final = ultimo_dia.strftime("%d/%m/%Y")

    data_arquivo = hoje.strftime("%d-%m-%Y")
    mes_nome = MESES_PT[mes]

    nome_arquivo = f"RH_{mes_nome}_{ano}_{data_arquivo}.xlsx"

    pasta_do_dia = os.path.join(PASTA_RELATORIOS, data_arquivo)

    return data_inicial, data_final, nome_arquivo, pasta_do_dia


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

def garantir_pasta_relatorios():
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS, exist_ok=True)

    if not os.path.isdir(PASTA_RELATORIOS):
        raise Exception(f"Pasta de relatórios não encontrada: {PASTA_RELATORIOS}")

    print(f"Pasta de relatórios configurada: {PASTA_RELATORIOS}")


def aguardar_download_e_renomear(arquivos_antes, nome_arquivo_final, pasta_do_dia, timeout=120):
    print("Aguardando download do XLSX...")

    inicio = time.time()

    while time.time() - inicio < timeout:
        arquivos_agora = set(os.listdir(PASTA_RELATORIOS))
        novos_arquivos = arquivos_agora - arquivos_antes

        downloads_em_andamento = [
            arquivo for arquivo in arquivos_agora
            if arquivo.lower().endswith(".crdownload")
        ]

        arquivos_xlsx = [
            arquivo for arquivo in novos_arquivos
            if arquivo.lower().endswith(".xlsx")
        ]

        if arquivos_xlsx and not downloads_em_andamento:
            arquivo_baixado = arquivos_xlsx[0]

            caminho_atual = os.path.join(PASTA_RELATORIOS, arquivo_baixado)

            os.makedirs(pasta_do_dia, exist_ok=True)

            caminho_final = os.path.join(pasta_do_dia, nome_arquivo_final)

            if os.path.exists(caminho_final):
                os.remove(caminho_final)

            os.rename(caminho_atual, caminho_final)

            print(f"Relatório salvo como: {caminho_final}")
            return caminho_final

        time.sleep(1)

    raise Exception("Tempo limite atingido aguardando o download do relatório XLSX.")

def criar_driver():
    garantir_pasta_relatorios()

    options = Options()
    options.add_argument("--start-maximized")

    # Perfil fixo do Chrome para o robô
    options.add_argument(r"--user-data-dir=C:\ChromeRoboFatorRH")
    options.add_argument("--profile-directory=Default")

    # Reduz bloqueios de download do Chrome automatizado
    options.add_argument("--safebrowsing-disable-download-protection")
    options.add_argument("--disable-features=InsecureDownloadWarnings")
    options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://54.94.113.205:8079")

    # Downloads automáticos
    prefs = {
        "download.default_directory": PASTA_RELATORIOS,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "profile.default_content_setting_values.automatic_downloads": 1,

        # Libera download no perfil automatizado
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
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


def preencher_filtros_desligados(driver, wait, data_inicial, data_final):
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

    for i, campo in enumerate(campos_visiveis):
        print(
            f"{i} | id={campo.get_attribute('id')} | "
            f"name={campo.get_attribute('name')} | "
            f"value={campo.get_attribute('value')}"
        )

    if len(campos_visiveis) < 4:
        raise Exception(
            f"Não encontrei todos os campos de data. Encontrados: {len(campos_visiveis)}"
        )

    campo_data_admissao_inicial = campos_visiveis[0]
    campo_data_admissao_final = campos_visiveis[1]
    campo_desligamento_inicial = campos_visiveis[2]
    campo_desligamento_final = campos_visiveis[3]

    forcar_valor_extjs(driver, campo_data_admissao_inicial, "")
    forcar_valor_extjs(driver, campo_data_admissao_final, "")

    print("Campos de Data Admissão apagados.")

    forcar_valor_extjs(driver, campo_desligamento_inicial, data_inicial)
    forcar_valor_extjs(driver, campo_desligamento_final, data_final)

    print(f"Data inicial de desligamento preenchida: {data_inicial}")
    print(f"Data final de desligamento preenchida: {data_final}")

    time.sleep(1)

    print("Valores após preenchimento:")

    for i, campo in enumerate(campos_visiveis):
        print(
            f"{i} | id={campo.get_attribute('id')} | "
            f"value={campo.get_attribute('value')}"
        )


def selecionar_xlsx_e_baixar(driver, wait, nome_arquivo_final, pasta_do_dia):
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

    # Depois de abrir o combo:
    # seta para baixo para ir até XLSX
    # enter para selecionar
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
    arquivos_antes = set(os.listdir(PASTA_RELATORIOS))

    botao_ok.click()

    print("OK clicado. Download solicitado.")

    aguardar_download_e_renomear(arquivos_antes, nome_arquivo_final, pasta_do_dia)

def executar():
    data_inicial, data_final, nome_arquivo_final, pasta_do_dia = obter_data_execucao()
    
    print(f"Pasta do dia: {pasta_do_dia}")
    print("Executando relatório diário de desligados:")
    print(f"Período: {data_inicial} até {data_final}")
    print(f"Arquivo final: {nome_arquivo_final}")

    driver = criar_driver()
    wait = WebDriverWait(driver, 30)

    try:
        fazer_login(driver, wait)
        abrir_listagem_desligados(driver, wait)
        preencher_filtros_desligados(driver, wait, data_inicial, data_final)
        selecionar_xlsx_e_baixar(driver, wait, nome_arquivo_final, pasta_do_dia)

        print("Processo executado com sucesso.")

    except Exception as e:
        print(f"Erro durante a execução: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    executar()