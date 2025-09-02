import random
import time
import csv
import os
from urllib.parse import quote
from camoufox.sync_api import Camoufox
from playwright.sync_api import Page, Error as PlaywrightError
from typing import List, Callable, Optional
import threading
import platform
import subprocess
from browserforge.fingerprints import Screen

class WhatsAppBot:
    """
    Encapsula a automação do WhatsApp usando Camoufox, com suporte para perfis persistentes.
    """
    def __init__(
        self,
        numeros: List[str],
        mensagens: List[str],
        log_callback: Callable[[str], None],
        status_callback: Callable[[bool], None],
        progress_callback: Callable[[int, int], None],
        stop_event: threading.Event,
        profile_path: Optional[str] = None
    ):
        self.numeros = numeros
        self.mensagens = mensagens
        self.log = log_callback
        self.update_status_callback = status_callback
        self.update_progress_callback = progress_callback
        self.stop_event = stop_event
        self.profile_path = profile_path

    def _interruptible_sleep(self, duration: float):
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.stop_event.is_set(): break
            time.sleep(0.1)

    def _save_progress(self, enviados: List[str], faltantes: List[str]):
        try:
            with open("enviados.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for numero in enviados: writer.writerow([numero])
            with open("faltantes.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for numero in faltantes: writer.writerow([numero])
        except Exception as e: self.log(f"⚠️ Erro ao salvar progresso: {e}")

    def _enviar_mensagem(self, page: Page, numero: str, mensagem: str):
        try:
            self.log(f"➡️ Tentando enviar para {numero}...")
            encoded_message = quote(mensagem)
            url = f"https://web.whatsapp.com/send?phone={numero}&text={encoded_message}"
            page.goto(url, timeout=90000, wait_until="domcontentloaded")
            self.log("   Aguardando 12 segundos para a página carregar...")
            self._interruptible_sleep(12)
            if self.stop_event.is_set(): return
            delay_envio = random.uniform(2, 6)
            self.log(f"   Aguardando {delay_envio:.2f} segundos antes de enviar...")
            self._interruptible_sleep(delay_envio)
            if self.stop_event.is_set(): return
            page.keyboard.press("Enter")
            self.log(f"✅ Mensagem enviada para {numero}!")
            self._interruptible_sleep(random.uniform(2, 4))
        except Exception as e: self.log(f"❌ Erro ao tentar enviar para {numero}: {e}")

    def run(self):
        numeros_enviados, numeros_faltantes, total_inicial = [], list(self.numeros), len(self.numeros)
        
        if self.profile_path and not os.path.exists(self.profile_path):
            self.log(f"ℹ️ Criando diretório de perfil em: {self.profile_path}")
            os.makedirs(self.profile_path)

        for attempt in range(2):
            try:
                with Camoufox(
                    headless=False,
                    humanize=True,
                    args=['--no-proxy-server'],
                    user_data_dir="novo_perfil_whatsapp",
                    persistent_context=True,
                    screen=Screen(max_width=600, max_height=400)
                ) as context:   
                    page = context.pages[0]
                    page.goto("https://web.whatsapp.com/")

                    self.log("="*50)
                    try:
                        self.log("A verificar estado do login...")
                        page.wait_for_selector("#pane-side, div[data-testid='qrcode']", timeout=30000)
                    except PlaywrightError:
                        self.log("❌ A página do WhatsApp não carregou corretamente.")
                        break

                    if page.locator("#pane-side").is_visible():
                        self.log("✅ Login persistente encontrado!")
                        logged_in = True
                    else:
                        self.log("📱 Por favor, escaneie o QR Code na janela do navegador.")
                        logged_in = False
                        for _ in range(300):
                            if self.stop_event.is_set(): break
                            if page.locator("#pane-side").is_visible():
                                logged_in = True
                                break
                            time.sleep(1)

                    if self.stop_event.is_set(): self.log("🛑 Processo interrompido durante o login."); break
                    if not logged_in: self.log("❌ TEMPO ESGOTADO: O QR Code não foi lido a tempo."); break
                    
                    self.log("="*50)
                    self.log("✅ Login bem-sucedido!")
                    self.log("🚀 Iniciando processo de envio...")
                    self.log("="*50)
                    while numeros_faltantes and not self.stop_event.is_set():
                        numero_atual = numeros_faltantes[0]
                        self.log("-" * 30)
                        self.log(f"Processando {len(numeros_enviados) + 1} de {total_inicial}...")
                        mensagem = self.mensagens[len(numeros_enviados) % len(self.mensagens)]
                        self._enviar_mensagem(page, numero_atual, mensagem)
                        if self.stop_event.is_set(): break
                        numeros_enviados.append(numero_atual)
                        numeros_faltantes.pop(0)
                        self._save_progress(numeros_enviados, numeros_faltantes)
                        self.update_progress_callback(len(numeros_enviados), total_inicial)
                    
                    if self.stop_event.is_set():
                        self.log("🛑 Processo interrompido pelo usuário.")
                    else:
                        self.log("\n🎉 Processo finalizado! Todos os contatos foram processados.")
                break
            except Exception as e:
                is_missing_browser_error = "Executable doesn't exist" in str(e) or "playwright install" in str(e)
                if is_missing_browser_error and attempt == 0:
                    self.log("⚠️ Firefox (necessário para automação) não foi encontrado.")
                    self.log("⏳ Tentando instalar automaticamente... Isso pode levar alguns minutos.")
                    try:
                        startupinfo = None
                        process = subprocess.Popen(["playwright", "install", "firefox"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
                        for line in iter(process.stdout.readline, ''): self.log(f"[Instalador] {line.strip()}")
                        process.wait()
                        if process.returncode == 0: self.log("✅ Firefox instalado com sucesso! A reiniciar a automação..."); continue
                        else:
                            stderr_output = process.stderr.read()
                            self.log(f"❌ Falha na instalação do Firefox. Erro: {stderr_output}")
                            self.log("👉 Por favor, feche a app, abra o terminal e execute: playwright install firefox")
                            break
                    except Exception as install_error: self.log(f"❌ Falha crítica ao tentar instalar o Firefox: {install_error}"); break
                else: self.log(f"❌ ERRO CRÍTICO NA AUTOMAÇÃO: {e}"); break
        self.log("Progresso final salvo.")
        self.update_status_callback(False)
