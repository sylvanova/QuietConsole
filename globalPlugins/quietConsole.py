import addonHandler

addonHandler.initTranslation()

import api
import config
import gui
from gui import settingsDialogs
import wx
import globalPluginHandler
import ui
from scriptHandler import script
from logHandler import log

_LANG = config.conf["general"].get("language", "en").split("_")[0]
_TRANSLATIONS = {
    "Quiet Console": {
        "en": "Quiet Console",
        "de": "Stille Konsole",
        "fr": "Console silencieuse",
        "es": "Consola silenciosa",
        "it": "Console silenziosa",
        "pt": "Console silencioso",
        "ru": "Тихая консоль",
        "ja": "静かなコンソール",
        "zh": "静音控制台",
        "pl": "Cicha konsola",
        "nl": "Stille console",
    },
    "Start consoles in quiet mode": {
        "en": "Start consoles in quiet mode",
        "de": "Konsolen im Ruhemodus starten",
        "fr": "Démarrer les consoles en mode silencieux",
        "es": "Iniciar las consolas en modo silencioso",
        "it": "Avvia le console in modalità silenziosa",
        "pt": "Iniciar consoles em modo silencioso",
        "ru": "Запускать консоль в тихом режиме",
        "ja": "コンソールを静音モードで開始",
        "zh": "以静音模式启动控制台",
        "pl": "Uruchamiaj konsolę w trybie cichym",
        "nl": "Consoles starten in stille modus",
    },
    "Lines to read with read-last command:": {
        "en": "Lines to read with read-last command:",
        "de": "Zeilen für den Letzte-Zeilen-Befehl:",
        "fr": "Lignes à lire avec la commande fin de console :",
        "es": "Líneas a leer con el comando leer últimas:",
        "it": "Righe da leggere con il comando ultime righe:",
        "pt": "Linhas a ler com o comando ler últimas:",
        "ru": "Строк для чтения командой «прочитать последние»:",
        "ja": "末尾読み上げで読む行数:",
        "zh": "使用“读取末尾”命令读取的行数：",
        "pl": "Liczba linii dla polecenia czytania końca:",
        "nl": "Regels om te lezen met laatste-regels:",
    },
    "Log suppressed events (for debugging)": {
        "en": "Log suppressed events (for debugging)",
        "de": "Unterdrückte Ereignisse protokollieren (Debug)",
        "fr": "Journaliser les événements supprimés (debug)",
        "es": "Registrar eventos suprimidos (depuración)",
        "it": "Logga eventi soppressi (debug)",
        "pt": "Registar eventos suprimidos (depuração)",
        "ru": "Логировать подавленные события (отладка)",
        "ja": "抑制イベントをログ (デバッグ用)",
        "zh": "记录被抑制的事件（调试）",
        "pl": "Loguj tłumione zdarzenia (debug)",
        "nl": "Log onderdrukte gebeurtenissen (debug)",
    },
    "Extreme suppression mode (aggressive)": {
        "en": "Extreme suppression mode (aggressive)",
        "de": "Extremer Unterdrückungsmodus (aggressiv)",
        "fr": "Mode suppression extrême (agressif)",
        "es": "Modo de supresión extrema (agresivo)",
        "it": "Soppressione estrema (aggressiva)",
        "pt": "Modo de supressão extrema (agressivo)",
        "ru": "Экстремальное подавление (агрессивно)",
        "ja": "強力抑制モード（高強度）",
        "zh": "极限抑制模式（高强度）",
        "pl": "Tryb ekstremalnego tłumienia (agresywny)",
        "nl": "Extreme onderdrukkingsmodus (agressief)",
    },
}


def _(msg: str) -> str:
    return _TRANSLATIONS.get(msg, {}).get(_LANG, msg)


def _coerce_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "on")
    if val is None:
        return default
    return bool(val)


def _getSettingsSection():
    root = config.conf
    try:
        section = root["quietConsole"]
    except KeyError:
        section = {}
        root["quietConsole"] = section
    # configobj sections in NVDA do not always expose dict helpers like setdefault.
    try:
        section["quietModeEnabled"]
    except Exception:
        section["quietModeEnabled"] = False
    try:
        section["logSuppression"]
    except Exception:
        section["logSuppression"] = False
    try:
        section["extremeMode"]
    except Exception:
        section["extremeMode"] = False
    return section


class QuietConsoleSettingsPanel(settingsDialogs.SettingsPanel):
    title = _("Quiet Console")

    def makeSettings(self, sizer):
        section = _getSettingsSection()
        self.startQuiet = wx.CheckBox(
            self,
            label=_("Start consoles in quiet mode"),
        )
        self.startQuiet.SetValue(_coerce_bool(section.get("quietModeEnabled", False), False))
        sizer.Add(self.startQuiet, flag=wx.ALL, border=5)

        self.logSuppression = wx.CheckBox(
            self, label=_("Log suppressed events (for debugging)")
        )
        self.logSuppression.SetValue(_coerce_bool(section.get("logSuppression", False), False))
        sizer.Add(self.logSuppression, flag=wx.ALL, border=5)

        self.extremeMode = wx.CheckBox(
            self, label=_("Extreme suppression mode (aggressive)")
        )
        self.extremeMode.SetValue(_coerce_bool(section.get("extremeMode", False), False))
        sizer.Add(self.extremeMode, flag=wx.ALL, border=5)

    def onSave(self):
        section = _getSettingsSection()
        section["quietModeEnabled"] = bool(self.startQuiet.GetValue())
        section["logSuppression"] = bool(self.logSuppression.GetValue())
        section["extremeMode"] = bool(self.extremeMode.GetValue())
        config.conf.save()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Quiet Console")
    __gestures = {
        "kb:NVDA+shift+v": "togglePlainTextView",
        "kb:NVDA+alt+v": "togglePlainTextView",
    }

    def __init__(self):
        super().__init__()
        self._lastConsoleModule = None
        settingsDialogs.NVDASettingsDialog.categoryClasses.append(
            QuietConsoleSettingsPanel
        )
        log.info("QuietConsole global plugin loaded")

    def _getActiveConsoleModule(self):
        focus = api.getFocusObject()
        if not focus:
            return None
        mod = getattr(focus, "appModule", None)
        if mod and hasattr(mod, "script_togglePlainTextView"):
            self._lastConsoleModule = mod
            return mod
        if self._lastConsoleModule and hasattr(self._lastConsoleModule, "script_togglePlainTextView"):
            return self._lastConsoleModule
        return None

    @script(
        description=_("Toggle live plain text view for this terminal window."),
    )
    def script_togglePlainTextView(self, gesture):
        mod = self._getActiveConsoleModule()
        if not mod:
            ui.message(_("Focus a supported console window first."))
            return
        try:
            from logHandler import log
            log.info("QuietConsole global plain view toggle routed to %s", getattr(mod, "appName", "<unknown>"))
        except Exception:
            pass
        mod.script_togglePlainTextView(gesture)

    def terminate(self):
        try:
            settingsDialogs.NVDASettingsDialog.categoryClasses.remove(
                QuietConsoleSettingsPanel
            )
        except ValueError:
            pass
