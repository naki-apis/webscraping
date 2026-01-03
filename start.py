import os

def start():
    root = os.path.dirname(os.path.abspath(__file__))
    chrome_dir = os.path.join(root, "selenium")
    base = os.path.join(chrome_dir, "chrome")
    total = 11

    try:
        with open(base, "wb") as out:
            for i in range(1, total + 1):
                part = f"{base}.{i:03d}"
                if not os.path.exists(part):
                    print(f"[!] Parte faltante: {part}")
                    return
                with open(part, "rb") as pf:
                    out.write(pf.read())
                print(f"[✓] Añadida parte {i:03d}")
    except Exception as e:
        print(f"[!] Error al unir: {e}")
        return

    for i in range(1, total + 1):
        part = f"{base}.{i:03d}"
        try:
            os.remove(part)
            print(f"[🗑️] Eliminada parte: {part}")
        except:
            print(f"[!] No se pudo eliminar: {part}")

    for p in [
        os.path.join(root, "selenium/chrome"),
        os.path.join(root, "selenium/chromedriver")
    ]:
        try:
            os.chmod(p, 0o755)
            print(f"[🔓] Permisos ajustados: {p}")
        except:
            print(f"[!] Error permisos: {p}")

if __name__ == "__main__":
    start()

