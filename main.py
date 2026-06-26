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

# ===================================================
# CARREGA VARIÁVEIS
# ===================================================

load_dotenv()

USUARIO = os.getenv("USUARIO_FATOR")
SENHA = os.getenv("SENHA_FATOR")

# ===================================================
# CHROME
# ===================================================

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 30)

# ===================================================
# ABRE PORTAL
# ===================================================

driver.get("http://54.94.113.205:8079/pmlaurodefreitas/index.html")

# ===================================================
# LOGIN
# ===================================================
time.sleep(5)

campo_usuario = wait.until(
    EC.visibility_of_element_located((By.ID, "textfield-1026-inputEl"))
)

campo_usuario.click()
campo_usuario.send_keys(Keys.CONTROL, "a")
campo_usuario.send_keys(Keys.DELETE)
campo_usuario.send_keys(USUARIO)

print("Usuário preenchido.")

# ===================================================
# SENHA
# ===================================================

campo_senha = wait.until(
    EC.visibility_of_element_located((By.ID, "textfield-1027-inputEl"))
)

campo_senha.click()
campo_senha.send_keys(SENHA)

print("Senha preenchida.")

# ===================================================
# MUNICÍPIO
# ===================================================

wait.until(
    EC.element_to_be_clickable((By.ID, "combobox-1032-trigger-picker"))
).click()

print("Combo aberto.")

# Aguarda a lista aparecer
time.sleep(5)

municipio = wait.until(
    EC.element_to_be_clickable((
        By.XPATH,
        "//*[contains(text(),'MUNICIPIO DE LAURO DE FREITAS')]"
    ))
)

municipio.click()

print("Município selecionado.")

# ===================================================
# BOTÃO OK
# ===================================================

wait.until(
    EC.element_to_be_clickable((By.ID, "button-1036"))
).click()

print("Login realizado!")

# ===================================================
# PAUSA PARA TESTE
# ===================================================

input("\nPressione ENTER para fechar...")

driver.quit()