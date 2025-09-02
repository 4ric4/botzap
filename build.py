import subprocess
import os
import sys
import shutil

# --- Configurações ---
APP_NAME = "DisparadorWhatsApp"
ENTRY_POINT = "main.py"  # Atualizei para main.py (onde a GUI principal está)
ICON_PATH = os.path.join("assets", "icon.ico")

# Dependências que o PyInstaller precisa coletar dados
PACKAGES_WITH_DATA = [
    'camoufox',
    'browserforge',
    'language_tags',
    'playwright',
    'customtkinter'
]

# Pastas/arquivos de build a limpar
CLEAN_FOLDERS = ["dist", "build", f"{APP_NAME}.spec"]

def clean_previous_build():
    for path in CLEAN_FOLDERS:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)

def build_exe():
    print("="*50)
    print("⚡ Iniciando build do executável .exe")
    print("="*50)

    # Limpa builds anteriores
    clean_previous_build()

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean"
    ]

    # Adiciona nome do app
    command.append(f"--name={APP_NAME}")

    # Adiciona ícone se existir
    if os.path.exists(ICON_PATH):
        command.append(f"--icon={ICON_PATH}")
    else:
        print(f"⚠️ Ícone '{ICON_PATH}' não encontrado. Ignorando.")

    # Excluir módulos de teste desnecessários
    command.extend([
        "--exclude-module", "tkinter.test",
        "--exclude-module", "tests"
    ])

    # Coleta dados dos pacotes
    for pkg in PACKAGES_WITH_DATA:
        command.extend(["--collect-all", pkg])

    # Arquivo principal
    command.append(ENTRY_POINT)

    print("\nComando gerado para PyInstaller:")
    print(" ".join(command))
    print("="*50 + "\n")

    # Executa PyInstaller
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )

        for line in iter(process.stdout.readline, ''):
            print(line.strip())

        process.wait()
        if process.returncode == 0:
            print("\n✅ Executável criado com sucesso! Verifique a pasta 'dist'.")
        else:
            print("\n❌ Erro durante a criação do executável.")
    except Exception as e:
        print(f"\n❌ Falha inesperada: {e}")

if __name__ == "__main__":
    input("Pressione ENTER para iniciar a criação do .exe...")
    build_exe()
