"""
chat_pracownik1.py — Okno chat dla Pracownika 1 (Ogólny Agent AI).

Uruchomienie:
  python pracownicy/chat_pracownik1.py
  # lub z root repo:
  python -m pracownicy.chat_pracownik1

Skróty:
  Enter         — wyślij wiadomość
  Shift+Enter   — nowa linia w polu wejściowym
"""

import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from neochat import load_config
except ImportError:
    print("[BŁĄD] Brak neochat.py w root repozytorium.")
    sys.exit(1)

try:
    from ai_backend import wyslij_do_ai_multi
except ImportError:
    wyslij_do_ai_multi = None

try:
    from moderacja import sprawdz_wejscie, sprawdz_wyjscie
except ImportError:
    def sprawdz_wejscie(tekst): return None
    def sprawdz_wyjscie(tekst): return tekst

# ── System prompt Pracownika 1 ────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "Jesteś autonomicznym pracownikiem AI o imieniu Pracownik 1. "
    "Dostajesz konkretne zadania i wykonujesz je bez dodatkowych pytań. "
    "Odpowiadasz konkretnie, zwięźle i merytorycznie. "
    "Jeśli zadanie wymaga kodu — piszesz kod. Jeśli wymaga tekstu — piszesz tekst. "
    "Zawsze kończysz zadanie w jednej odpowiedzi."
)

# ── Kolory (motyw ciemny Catppuccin Mocha) ────────────────────────────────────
K_TLO       = "#1e1e2e"
K_PANEL     = "#2a2a3e"
K_TEKST     = "#cdd6f4"
K_UZYTK     = "#89dceb"
K_AI        = "#a6e3a1"
K_BLAD      = "#f38ba8"
K_WEJSCIE   = "#313244"
K_PRZYCISK  = "#89b4fa"
K_MUTED     = "#6c7086"
K_SEP       = "#45475a"

CZ_CHAT     = ("Consolas", 11)
CZ_WEJSCIE  = ("Segoe UI", 11)
CZ_TITLE    = ("Segoe UI", 13, "bold")
CZ_SMALL    = ("Segoe UI", 9)
CZ_BTN      = ("Segoe UI", 10, "bold")


class ChatPracownik1:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chat — Pracownik 1 (Agent AI)")
        self.root.geometry("920x660")
        self.root.configure(bg=K_TLO)
        self.root.resizable(True, True)
        self.root.minsize(600, 400)

        self.cfg = load_config()
        self.historia: list[dict] = []
        self.max_historia = self.cfg.get("history_limit", 10)

        self._buduj_ui()
        self._dodaj_info("Pracownik 1 gotowy. Napisz zadanie lub pytanie.")
        self.wejscie.focus_set()

    # ── Budowa UI ─────────────────────────────────────────────────────────────

    def _buduj_ui(self):
        # Pasek tytułowy
        pasek = tk.Frame(self.root, bg=K_PANEL, pady=8)
        pasek.pack(fill=tk.X)

        tk.Label(
            pasek,
            text="\U0001f916  Pracownik 1 — Agent AI",
            font=CZ_TITLE,
            bg=K_PANEL,
            fg=K_PRZYCISK,
        ).pack(side=tk.LEFT, padx=16)

        model_txt = self.cfg.get("model", "gpt-4o-mini")
        tk.Label(
            pasek,
            text=f"model: {model_txt}",
            font=CZ_SMALL,
            bg=K_PANEL,
            fg=K_MUTED,
        ).pack(side=tk.RIGHT, padx=16)

        # Obszar czatu
        ramka_chat = tk.Frame(self.root, bg=K_TLO)
        ramka_chat.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 0))

        self.chat_box = scrolledtext.ScrolledText(
            ramka_chat,
            wrap=tk.WORD,
            font=CZ_CHAT,
            bg=K_TLO,
            fg=K_TEKST,
            insertbackground=K_TEKST,
            selectbackground=K_SEP,
            relief=tk.FLAT,
            state=tk.DISABLED,
            cursor="arrow",
            padx=6,
            pady=6,
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)

        self.chat_box.tag_configure("uzytkownik", foreground=K_UZYTK, font=("Consolas", 11, "bold"))
        self.chat_box.tag_configure("ai",         foreground=K_AI)
        self.chat_box.tag_configure("info",       foreground=K_MUTED, font=("Consolas", 10, "italic"))
        self.chat_box.tag_configure("blad",       foreground=K_BLAD,  font=("Consolas", 11, "bold"))
        self.chat_box.tag_configure("czas",       foreground=K_SEP,   font=("Consolas", 9))
        self.chat_box.tag_configure("label_ai",   foreground=K_AI,    font=("Consolas", 11, "bold"))

        # Separator
        tk.Frame(self.root, bg=K_SEP, height=1).pack(fill=tk.X, padx=12, pady=6)

        # Panel wejścia
        ramka_wejscie = tk.Frame(self.root, bg=K_TLO)
        ramka_wejscie.pack(fill=tk.X, padx=12, pady=(0, 6))

        self.wejscie = tk.Text(
            ramka_wejscie,
            height=3,
            font=CZ_WEJSCIE,
            bg=K_WEJSCIE,
            fg=K_TEKST,
            insertbackground=K_TEKST,
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=8,
            pady=6,
        )
        self.wejscie.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.wejscie.bind("<Return>",       self._na_enter)
        self.wejscie.bind("<Shift-Return>", lambda e: None)

        ramka_btns = tk.Frame(ramka_wejscie, bg=K_TLO)
        ramka_btns.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_wyslij = tk.Button(
            ramka_btns,
            text="Wyślij",
            font=CZ_BTN,
            bg=K_PRZYCISK,
            fg=K_TLO,
            activebackground="#74c7ec",
            activeforeground=K_TLO,
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._wyslij,
        )
        self.btn_wyslij.pack(fill=tk.X, pady=(0, 4))

        self.btn_czysc = tk.Button(
            ramka_btns,
            text="Wyczyść",
            font=CZ_SMALL,
            bg=K_SEP,
            fg=K_TEKST,
            activebackground="#585b70",
            activeforeground=K_TEKST,
            relief=tk.FLAT,
            padx=18,
            pady=5,
            cursor="hand2",
            command=self._wyczysc,
        )
        self.btn_czysc.pack(fill=tk.X)

        # Pasek statusu
        self.status_var = tk.StringVar(value="Gotowy")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=CZ_SMALL,
            bg=K_TLO,
            fg=K_MUTED,
            anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(2, 8))

    # ── Obsługa zdarzeń ───────────────────────────────────────────────────────

    def _na_enter(self, event):
        """Enter wysyła, Shift+Enter wstawia nową linię."""
        if not (event.state & 0x1):   # Shift nie wciśnięty
            self._wyslij()
            return "break"

    def _wyslij(self):
        tekst = self.wejscie.get("1.0", tk.END).strip()
        if not tekst:
            return

        self.wejscie.delete("1.0", tk.END)

        self._wstaw("czas",       f"[{self._czas()}] ")
        self._wstaw("uzytkownik", "Ty: ")
        self._wstaw("uzytkownik", f"{tekst}\n\n")

        self.btn_wyslij.configure(state=tk.DISABLED, text="…")
        self.status_var.set("Pracownik 1 pracuje…")

        threading.Thread(target=self._ai_thread, args=(tekst,), daemon=True).start()

    def _ai_thread(self, tekst: str):
        try:
            blokada = sprawdz_wejscie(tekst)
            if blokada:
                self.root.after(0, self._blad, f"[MODERACJA — ZABLOKOWANO] {blokada}")
                return

            self.historia.append({"role": "user", "content": tekst})
            # Przycinanie historii do limitu
            limit = self.max_historia * 2
            if len(self.historia) > limit:
                self.historia = self.historia[-limit:]

            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.historia

            if wyslij_do_ai_multi:
                odpowiedz = wyslij_do_ai_multi(messages, self.cfg)
            else:
                from neochat import wyslij_do_ai
                odpowiedz = wyslij_do_ai(messages, self.cfg)

            if odpowiedz is None:
                self.root.after(0, self._blad, "[BŁĄD] Brak odpowiedzi od AI.")
                return

            odpowiedz = sprawdz_wyjscie(odpowiedz)
            self.historia.append({"role": "assistant", "content": odpowiedz})
            self.root.after(0, self._odpowiedz, odpowiedz)

        except Exception as exc:
            self.root.after(0, self._blad, f"[BŁĄD] {exc}")

    def _odpowiedz(self, tekst: str):
        self._wstaw("czas",      f"[{self._czas()}] ")
        self._wstaw("label_ai",  "Pracownik 1: ")
        self._wstaw("ai",        f"{tekst}\n\n")
        self._przywroc_przyciski()
        self.wejscie.focus_set()

    def _blad(self, tekst: str):
        self._wstaw("blad", f"{tekst}\n\n")
        self._przywroc_przyciski(blad=True)

    def _przywroc_przyciski(self, blad: bool = False):
        self.btn_wyslij.configure(state=tk.NORMAL, text="Wyślij")
        self.status_var.set("Błąd — spróbuj ponownie" if blad else "Gotowy")

    def _wyczysc(self):
        self.historia.clear()
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.delete("1.0", tk.END)
        self.chat_box.configure(state=tk.DISABLED)
        self._dodaj_info("Historia wyczyszczona. Pracownik 1 gotowy.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _wstaw(self, tag: str, tekst: str):
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.insert(tk.END, tekst, tag)
        self.chat_box.configure(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def _dodaj_info(self, tekst: str):
        self._wstaw("info", f"[{self._czas()}] ℹ  {tekst}\n\n")

    @staticmethod
    def _czas() -> str:
        return datetime.now().strftime("%H:%M:%S")


# ── Punkt wejścia ─────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    ChatPracownik1(root)
    root.mainloop()


if __name__ == "__main__":
    main()
