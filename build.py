import subprocess
import os
import sys
import shutil

APP_NAME = "DisparadorWhatsApp"
ENTRY_POINT = "main_app.py"
ICON_PATH = os.path.join("assets", "icon.ico")

PACKAGES_WITH_DATA = [
    'camoufox',
    'browserforge',
    'language_tags',
    'playwright',
    'customtkinter'
]

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

    clean_previous_build()

    icon_abs_path = os.path.abspath(ICON_PATH)
    if not os.path.exists(icon_abs_path):
        print(f"⚠️ Ícone '{icon_abs_path}' não encontrado. Ignorando.")
        icon_abs_path = None

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean",
        f"--name={APP_NAME}"
    ]

    if icon_abs_path:
        command.append(f"--icon={icon_abs_path}")


    assets_path = os.path.join(os.getcwd(), "assets")
    if os.path.exists(assets_path):
        command.append(f"--add-data={assets_path}{os.pathsep}assets")
    
    command.extend([
        "--exclude-module", "tkinter.test",
        "--exclude-module", "tests"
    ])

    for pkg in PACKAGES_WITH_DATA:
        command.extend(["--collect-all", pkg])

    command.append(ENTRY_POINT)

    print("\nComando gerado para PyInstaller:")
    print(" ".join(command))
    print("="*50 + "\n")

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