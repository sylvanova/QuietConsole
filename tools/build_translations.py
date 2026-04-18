"""Generate .po and .mo files for QuietConsole from source translation data.

Run from the repo root:

    python tools/build_translations.py

This writes locale/<lang>/LC_MESSAGES/nvda.po and nvda.mo for each supported
language, seeded from the embedded TRANSLATIONS dict below. The .po files are
the long-term source of truth; re-run this script (with the dict kept in sync)
to regenerate both artifacts after changes. No gettext tools required — a
small pure-Python .mo writer is included.
"""
from __future__ import annotations

import os
import struct
from pathlib import Path


SOURCE_LANG = "en"
LOCALE_TO_DIR = {
    "de": "de",
    "es": "es",
    "fr": "fr",
    "it": "it",
    "ja": "ja",
    "nl": "nl",
    "pl": "pl",
    "pt": "pt",
    "ru": "ru",
    "zh": "zh_CN",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "Quiet Console": {
        "de": "Stille Konsole",
        "es": "Consola silenciosa",
        "fr": "Console silencieuse",
        "it": "Console silenziosa",
        "ja": "静かなコンソール",
        "nl": "Stille console",
        "pl": "Cicha konsola",
        "pt": "Console silencioso",
        "ru": "Тихая консоль",
        "zh": "静音控制台",
    },
    "Start consoles in quiet mode": {
        "de": "Konsolen im Ruhemodus starten",
        "es": "Iniciar las consolas en modo silencioso",
        "fr": "Démarrer les consoles en mode silencieux",
        "it": "Avvia le console in modalità silenziosa",
        "ja": "コンソールを静音モードで開始",
        "nl": "Consoles starten in stille modus",
        "pl": "Uruchamiaj konsolę w trybie cichym",
        "pt": "Iniciar consoles em modo silencioso",
        "ru": "Запускать консоль в тихом режиме",
        "zh": "以静音模式启动控制台",
    },
    "Log suppressed events (for debugging)": {
        "de": "Unterdrückte Ereignisse protokollieren (Debug)",
        "es": "Registrar eventos suprimidos (depuración)",
        "fr": "Journaliser les événements supprimés (debug)",
        "it": "Registra eventi soppressi (debug)",
        "ja": "抑制イベントをログに記録（デバッグ用）",
        "nl": "Log onderdrukte gebeurtenissen (debug)",
        "pl": "Loguj tłumione zdarzenia (debug)",
        "pt": "Registrar eventos suprimidos (depuração)",
        "ru": "Логировать подавленные события (отладка)",
        "zh": "记录被抑制的事件（调试）",
    },
    "Extreme suppression mode (aggressive)": {
        "de": "Extremer Unterdrückungsmodus (aggressiv)",
        "es": "Modo de supresión extrema (agresivo)",
        "fr": "Mode suppression extrême (agressif)",
        "it": "Modalità di soppressione estrema (aggressiva)",
        "ja": "強力抑制モード（高強度）",
        "nl": "Extreme onderdrukkingsmodus (agressief)",
        "pl": "Tryb ekstremalnego tłumienia (agresywny)",
        "pt": "Modo de supressão extrema (agressivo)",
        "ru": "Экстремальное подавление (агрессивно)",
        "zh": "极限抑制模式（高强度）",
    },
    "Toggle quiet console mode for this terminal window.": {
        "de": "Ruhigen Konsolenmodus für dieses Terminal umschalten.",
        "es": "Alternar el modo consola silenciosa para esta terminal.",
        "fr": "Basculer le mode console silencieuse pour ce terminal.",
        "it": "Attiva/disattiva la modalità console silenziosa per questo terminale.",
        "ja": "この端末の静音モードを切り替えます。",
        "nl": "Schakel stille consolemodus voor dit venster.",
        "pl": "Przełącz tryb cichej konsoli dla tego terminala.",
        "pt": "Alternar o modo console silencioso para esta janela.",
        "ru": "Переключить тихий режим для этого терминала.",
        "zh": "为此终端切换静音模式。",
    },
    "Toggle live plain text view for this terminal window.": {
        "de": "Live-Textansicht für dieses Terminalfenster umschalten.",
        "es": "Alternar vista de texto plano en vivo para esta terminal.",
        "fr": "Basculer la vue texte brut en direct pour ce terminal.",
        "it": "Attiva/disattiva la vista testo semplice in tempo reale per questo terminale.",
        "ja": "この端末のライブプレーンテキスト表示を切り替えます。",
        "nl": "Schakel live platte-tekstweergave voor dit terminalvenster.",
        "pl": "Przełącz widok zwykłego tekstu na żywo dla tego terminala.",
        "pt": "Alternar visualização de texto simples em tempo real para esta consola.",
        "ru": "Переключить живой просмотр простого текста для этого терминала.",
        "zh": "为此终端切换实时纯文本视图。",
    },
    "Focus a supported console window first.": {
        "de": "Fokussiere zuerst ein unterstütztes Konsolenfenster.",
        "es": "Enfoca primero una ventana de consola compatible.",
        "fr": "Placez d'abord le focus sur une fenêtre de console prise en charge.",
        "it": "Metti prima il focus su una finestra console supportata.",
        "ja": "先に対応しているコンソールウィンドウにフォーカスしてください。",
        "nl": "Focus eerst een ondersteund consolevenster.",
        "pl": "Najpierw ustaw fokus na obsługiwanym oknie konsoli.",
        "pt": "Coloque primeiro o foco numa janela de consola suportada.",
        "ru": "Сначала сфокусируйте поддерживаемое окно консоли.",
        "zh": "请先聚焦到受支持的控制台窗口。",
    },
    "enabled": {
        "de": "aktiviert",
        "es": "activado",
        "fr": "activé",
        "it": "abilitato",
        "ja": "有効",
        "nl": "ingeschakeld",
        "pl": "włączony",
        "pt": "ativado",
        "ru": "включено",
        "zh": "已启用",
    },
    "disabled": {
        "de": "deaktiviert",
        "es": "desactivado",
        "fr": "désactivé",
        "it": "disabilitato",
        "ja": "無効",
        "nl": "uitgeschakeld",
        "pl": "wyłączony",
        "pt": "desativado",
        "ru": "выключено",
        "zh": "已禁用",
    },
    "Quiet console mode {state}.": {
        "de": "Ruhiger Konsolenmodus {state}.",
        "es": "Modo consola silenciosa {state}.",
        "fr": "Mode console silencieuse {state}.",
        "it": "Modalità console silenziosa {state}.",
        "ja": "静音モードを{state}にしました。",
        "nl": "Stille consolemodus {state}.",
        "pl": "Tryb cichej konsoli {state}.",
        "pt": "Modo consola silenciosa {state}.",
        "ru": "Тихий режим консоли {state}.",
        "zh": "静音模式已{state}。",
    },
    "Quiet Console - Live Plain Text": {
        "de": "Stille Konsole - Live-Textansicht",
        "es": "Consola silenciosa - Texto plano en vivo",
        "fr": "Console silencieuse - Texte brut en direct",
        "it": "Console silenziosa - Testo semplice in tempo reale",
        "ja": "静かなコンソール - ライブプレーンテキスト",
        "nl": "Stille console - Live platte tekst",
        "pl": "Cicha konsola - Zwykły tekst na żywo",
        "pt": "Console silencioso - Texto simples em tempo real",
        "ru": "Тихая консоль - Живой простой текст",
        "zh": "静音控制台 - 实时纯文本",
    },
    "Follow bottom": {
        "de": "Unten folgen",
        "es": "Seguir al final",
        "fr": "Suivre le bas",
        "it": "Segui il fondo",
        "ja": "末尾に追従",
        "nl": "Onderkant volgen",
        "pl": "Śledź dół",
        "pt": "Seguir o final",
        "ru": "Следовать за концом",
        "zh": "跟随末尾",
    },
    "Fixed line": {
        "de": "Feste Zeile",
        "es": "Línea fija",
        "fr": "Ligne fixe",
        "it": "Riga fissa",
        "ja": "固定行",
        "nl": "Vaste regel",
        "pl": "Stała linia",
        "pt": "Linha fixa",
        "ru": "Фиксированная строка",
        "zh": "固定行",
    },
    "Plain text view opened.": {
        "de": "Textansicht geöffnet.",
        "es": "Vista de texto plano abierta.",
        "fr": "Vue texte brut ouverte.",
        "it": "Vista testo semplice aperta.",
        "ja": "プレーンテキストビューを開きました。",
        "nl": "Platte-tekstweergave geopend.",
        "pl": "Widok zwykłego tekstu otwarty.",
        "pt": "Vista de texto simples aberta.",
        "ru": "Открыт просмотр простого текста.",
        "zh": "纯文本视图已打开。",
    },
    "Plain text view closed.": {
        "de": "Textansicht geschlossen.",
        "es": "Vista de texto plano cerrada.",
        "fr": "Vue texte brut fermée.",
        "it": "Vista testo semplice chiusa.",
        "ja": "プレーンテキストビューを閉じました。",
        "nl": "Platte-tekstweergave gesloten.",
        "pl": "Widok zwykłego tekstu zamknięty.",
        "pt": "Vista de texto simples fechada.",
        "ru": "Просмотр простого текста закрыт.",
        "zh": "纯文本视图已关闭。",
    },
}


def _escape_po(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
         .replace("\"", "\\\"")
         .replace("\n", "\\n")
         .replace("\t", "\\t")
    )


def write_po(path: Path, lang: str, messages: dict[str, str]) -> None:
    header = (
        'msgid ""\n'
        'msgstr ""\n'
        f'"Project-Id-Version: QuietConsole\\n"\n'
        f'"Language: {lang}\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
    )
    body = []
    for msgid, msgstr in messages.items():
        body.append(f'\nmsgid "{_escape_po(msgid)}"')
        body.append(f'msgstr "{_escape_po(msgstr)}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n".join(body) + "\n", encoding="utf-8")


def write_mo(path: Path, messages: dict[str, str]) -> None:
    # metadata msgid "" must come first when sorted; sort by msgid (empty sorts first)
    items = sorted(messages.items(), key=lambda kv: kv[0].encode("utf-8"))
    n = len(items)

    keys_blob = b""
    vals_blob = b""
    key_offsets: list[tuple[int, int]] = []  # (length, offset)
    val_offsets: list[tuple[int, int]] = []

    for msgid, msgstr in items:
        k = msgid.encode("utf-8")
        v = msgstr.encode("utf-8")
        key_offsets.append((len(k), len(keys_blob)))
        val_offsets.append((len(v), len(vals_blob)))
        keys_blob += k + b"\x00"
        vals_blob += v + b"\x00"

    header_size = 7 * 4
    key_table_size = n * 8
    val_table_size = n * 8
    keys_start = header_size + key_table_size + val_table_size
    vals_start = keys_start + len(keys_blob)

    header = struct.pack(
        "<IIIIIII",
        0x950412DE,                 # magic
        0,                          # version
        n,                          # number of strings
        header_size,                # offset of originals table
        header_size + key_table_size,  # offset of translations table
        0,                          # hash size (unused)
        0,                          # hash offset (unused)
    )

    key_table = b"".join(
        struct.pack("<II", length, keys_start + offset)
        for length, offset in key_offsets
    )
    val_table = b"".join(
        struct.pack("<II", length, vals_start + offset)
        for length, offset in val_offsets
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(header)
        f.write(key_table)
        f.write(val_table)
        f.write(keys_blob)
        f.write(vals_blob)


def build(locale_root: Path) -> None:
    for lang, dir_name in LOCALE_TO_DIR.items():
        messages: dict[str, str] = {
            "": (
                f"Project-Id-Version: QuietConsole\n"
                f"Language: {lang}\n"
                "MIME-Version: 1.0\n"
                "Content-Type: text/plain; charset=UTF-8\n"
                "Content-Transfer-Encoding: 8bit\n"
            )
        }
        for source, per_lang in TRANSLATIONS.items():
            translated = per_lang.get(lang)
            if translated:
                messages[source] = translated

        lc_dir = locale_root / dir_name / "LC_MESSAGES"
        write_po(lc_dir / "nvda.po", lang, messages)
        write_mo(lc_dir / "nvda.mo", messages)
        print(f"  {lang:>5} -> {lc_dir}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    locale_root = repo_root / "locale"
    print(f"Writing translations to {locale_root}")
    build(locale_root)
    print("Done.")


if __name__ == "__main__":
    main()
