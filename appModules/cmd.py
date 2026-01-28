import addonHandler

addonHandler.initTranslation()

import api
import config
import speech
import textInfos
import ui
from appModuleHandler import AppModule as BaseAppModule
from logHandler import log
from scriptHandler import script
import time
from collections import deque
# Simple inline translations to avoid dependency on mo files.
_LANG = config.conf["general"].get("language", "en").split("_")[0]
_TRANSLATIONS = {
    "quietConsoleTitle": {
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
    "startQuiet": {
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
    "linesLabel": {
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
    "logSuppression": {
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
    "extremeMode": {
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
    "toggleDesc": {
        "en": "Toggle quiet console mode for this terminal window.",
        "de": "Ruhigen Konsolenmodus für dieses Terminal umschalten.",
        "fr": "Basculer le mode console silencieuse pour ce terminal.",
        "es": "Alternar el modo consola silenciosa para esta terminal.",
        "it": "Attiva/disattiva la modalità console silenziosa per questo terminale.",
        "pt": "Alternar o modo console silencioso para esta janela.",
        "ru": "Переключить тихий режим для этого терминала.",
        "ja": "この端末の静音モードを切り替えます。",
        "zh": "为此终端切换静音模式。",
        "pl": "Przełącz tryb cichej konsoli dla tego terminala.",
        "nl": "Schakel stille consolemodus voor dit venster.",
    },
    "readDesc": {
        "en": "Read the last part of the console buffer without re-enabling live updates.",
        "de": "Liest den letzten Teil des Konsolenpuffers ohne Live-Ausgaben zu aktivieren.",
        "fr": "Lit la fin du tampon console sans réactiver les mises à jour en direct.",
        "es": "Lee la última parte del búfer de consola sin reactivar las actualizaciones en vivo.",
        "it": "Legge l’ultima parte del buffer console senza riattivare gli aggiornamenti live.",
        "pt": "Lê a parte final do buffer da consola sem reativar atualizações ao vivo.",
        "ru": "Читает конец буфера консоли без включения живых обновлений.",
        "ja": "ライブ更新を再有効化せずにコンソール末尾を読み上げます。",
        "zh": "在不重新启用实时更新的情况下读取控制台末尾。",
        "pl": "Czyta końcówkę bufora konsoli bez włączania aktualizacji na żywo.",
        "nl": "Leest het einde van de consolebuffer zonder live-updates te heractiveren.",
    },
    "enabled": {
        "en": "enabled",
        "de": "aktiviert",
        "fr": "activé",
        "es": "activado",
        "it": "abilitato",
        "pt": "ativado",
        "ru": "включено",
        "ja": "有効",
        "zh": "已启用",
        "pl": "włączony",
        "nl": "ingeschakeld",
    },
    "disabled": {
        "en": "disabled",
        "de": "deaktiviert",
        "fr": "désactivé",
        "es": "desactivado",
        "it": "disabilitato",
        "pt": "desativado",
        "ru": "выключено",
        "ja": "無効",
        "zh": "已禁用",
        "pl": "wyłączony",
        "nl": "uitgeschakeld",
    },
    "status": {
        "en": "Quiet console mode {state}.",
        "de": "Ruhiger Konsolenmodus {state}.",
        "fr": "Mode console silencieuse {state}.",
        "es": "Modo consola silenciosa {state}.",
        "it": "Modalità console silenziosa {state}.",
        "pt": "Modo consola silenciosa {state}.",
        "ru": "Тихий режим консоли {state}.",
        "ja": "静音モードを{state}しました。",
        "zh": "静音模式已{state}。",
        "pl": "Tryb cichej konsoli {state}.",
        "nl": "Stille consolemodus {state}.",
    },
    "noFocus": {
        "en": "No focus object to read.",
        "de": "Kein Fokusobjekt zum Lesen.",
        "fr": "Aucun objet au focus à lire.",
        "es": "No hay objeto con foco para leer.",
        "it": "Nessun oggetto a fuoco da leggere.",
        "pt": "Sem objeto em foco para ler.",
        "ru": "Нет объекта фокуса для чтения.",
        "ja": "読み上げるフォーカス対象がありません。",
        "zh": "没有可读取的焦点对象。",
        "pl": "Brak obiektu w fokusie do odczytu.",
        "nl": "Geen focusobject om te lezen.",
    },
    "cantExamine": {
        "en": "Unable to examine console text.",
        "de": "Konsolentext kann nicht geprüft werden.",
        "fr": "Impossible d’examiner le texte de la console.",
        "es": "No se puede examinar el texto de la consola.",
        "it": "Impossibile esaminare il testo della console.",
        "pt": "Não é possível examinar o texto da consola.",
        "ru": "Не удалось получить текст консоли.",
        "ja": "コンソールのテキストを取得できません。",
        "zh": "无法检查控制台文本。",
        "pl": "Nie można odczytać tekstu konsoli.",
        "nl": "Kan de consoletekst niet onderzoeken.",
    },
    "noText": {
        "en": "No console text available yet.",
        "de": "Noch kein Konsolentext verfügbar.",
        "fr": "Aucun texte de console disponible.",
        "es": "Aún no hay texto de consola disponible.",
        "it": "Nessun testo della console disponibile.",
        "pt": "Ainda não há texto da consola disponível.",
        "ru": "Текст консоли пока недоступен.",
        "ja": "コンソールにまだテキストがありません。",
        "zh": "暂无控制台文本。",
        "pl": "Brak dostępnego tekstu konsoli.",
        "nl": "Nog geen consoletekst beschikbaar.",
    },
}


def _(msg: str) -> str:
    if not isinstance(msg, str):
        return msg
    key_map = {
        "Quiet Console": "quietConsoleTitle",
        "Quiet console mode {state}.": "status",
        "Toggle quiet console mode for this terminal window.": "toggleDesc",
        "Read the last part of the console buffer without re-enabling live updates.": "readDesc",
        "No focus object to read.": "noFocus",
        "Unable to examine console text.": "cantExamine",
        "No console text available yet.": "noText",
        "enabled": "enabled",
        "disabled": "disabled",
    }
    key = key_map.get(msg)
    if key and key in _TRANSLATIONS:
        return _TRANSLATIONS[key].get(_LANG, _TRANSLATIONS[key].get("en", msg))
    return msg


def _touch_review_activity(mod):
    if mod is not None:
        mod._manualSpeechActive = True


def _coerce_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "on")
    if val is None:
        return default
    return bool(val)


def _get_global_extreme() -> bool:
    section = config.conf.get(AppModule.SETTINGS_SECTION, {})
    return bool(section.get(AppModule.SETTINGS_EXTREME_KEY, AppModule.DEFAULT_EXTREME_MODE))


class _RateLimiter:
    """Simple sliding-window limiter used to drop noisy NVDA events."""

    def __init__(self, maxEvents: int, windowSec: float):
        self.maxEvents = maxEvents
        self.windowSec = windowSec
        self._timestamps = deque()

    def allows(self) -> bool:
        now = time.monotonic()
        windowStart = now - self.windowSec
        while self._timestamps and self._timestamps[0] < windowStart:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.maxEvents:
            return False
        self._timestamps.append(now)
        return True

    def reset(self):
        self._timestamps.clear()


_original_setReviewPosition = getattr(api, "setReviewPosition", None)
if _original_setReviewPosition and not getattr(api, "_quietConsoleReviewWrapped", False):
    def _wrapped_setReviewPosition(*args, **kwargs):
        # Mark that the user is actively reviewing; avoid canceling their speech.
        _touch_review_activity(args[0] if args else None)
        return _original_setReviewPosition(*args, **kwargs)

    _wrapped_setReviewPosition.__doc__ = _original_setReviewPosition.__doc__
    api.setReviewPosition = _wrapped_setReviewPosition
    api._quietConsoleReviewWrapped = True


_speechIsSpeaking = getattr(speech, "isSpeaking", None)

class AppModule(BaseAppModule):
    """AppModule that throttles console noise while quiet console mode is active."""

    scriptCategory = _("Quiet Console")

    SETTINGS_SECTION = "quietConsole"
    SETTINGS_KEY = "quietModeEnabled"
    SETTINGS_EXTREME_KEY = "extremeMode"
    DEFAULT_QUIET_MODE = False
    DEFAULT_EXTREME_MODE = False
    RATE_LIMIT_MAX_EVENTS = 1
    RATE_LIMIT_WINDOW_SEC = 1.0
    DEFAULT_READ_LAST_LINES = 30
    DEFAULT_LOG_SUPPRESSION = False
    _readLastLines = DEFAULT_READ_LAST_LINES
    _logSuppression = DEFAULT_LOG_SUPPRESSION

    __gestures = {
        "kb:NVDA+shift+c": "toggleQuietConsoleMode",
        "kb:NVDA+shift+r": "readRecentConsoleLines",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._readLastLines = int(
            self._getSettingsSection().get(
                "readLastLines", self.DEFAULT_READ_LAST_LINES
            )
        )
        self.READ_LAST_LINES = self._readLastLines
        self._logSuppression = bool(
            self._getSettingsSection().get(
                "logSuppression", self.DEFAULT_LOG_SUPPRESSION
            )
        )
        self._extremeMode = self._isExtremeModeEnabled()
        self._manualSpeechActive = False
        self._loggedSuppressionIntro = False
        self._lastFocusObjId = None
        self._limiter = _RateLimiter(
            maxEvents=self.RATE_LIMIT_MAX_EVENTS,
            windowSec=self.RATE_LIMIT_WINDOW_SEC,
        )
        log.info(
            "QuietConsole ready for %s (pid=%s, quietMode=%s)",
            self.appName,
            self.processID,
            self._isQuietModeEnabled(),
        )

    @classmethod
    def _isQuietModeEnabled(cls) -> bool:
        section = cls._getSettingsSection()
        return _coerce_bool(section.get(cls.SETTINGS_KEY, cls.DEFAULT_QUIET_MODE), cls.DEFAULT_QUIET_MODE)

    @classmethod
    def _isExtremeModeEnabled(cls) -> bool:
        section = cls._getSettingsSection()
        return _coerce_bool(section.get(cls.SETTINGS_EXTREME_KEY, cls.DEFAULT_EXTREME_MODE), cls.DEFAULT_EXTREME_MODE)

    @classmethod
    def _setQuietModeEnabled(cls, enabled: bool):
        section = cls._getSettingsSection()
        section[cls.SETTINGS_KEY] = enabled
        config.conf.save()

    @classmethod
    def _setExtremeModeEnabled(cls, enabled: bool):
        section = cls._getSettingsSection()
        section[cls.SETTINGS_EXTREME_KEY] = enabled
        config.conf.save()

    @classmethod
    def _getSettingsSection(cls):
        root = config.conf
        try:
            section = root[cls.SETTINGS_SECTION]
        except KeyError:
            section = {}
            root[cls.SETTINGS_SECTION] = section
        return section

    # ------------------------- Event handling -----------------------------

    def event_caret(self, obj, nextHandler):
        if self._shouldSuppressEvent("caret", obj):
            return
        nextHandler()

    def event_valueChange(self, obj, nextHandler):
        if self._shouldSuppressEvent("valueChange", obj):
            return
        nextHandler()

    def event_textChange(self, obj, nextHandler):
        if self._shouldSuppressEvent("textChange", obj):
            return
        nextHandler()

    def event_nameChange(self, obj, nextHandler):
        if self._shouldSuppressEvent("nameChange", obj):
            return
        nextHandler()

    def event_liveRegionChange(self, obj, nextHandler):
        if self._shouldSuppressEvent("liveRegionChange", obj):
            return
        nextHandler()

    def _shouldSuppressEvent(self, name: str, obj) -> bool:
        if not self._isQuietModeEnabled():
            return False
        # Allow the first event for a new focus object so focus changes still speak.
        objId = id(obj) if obj is not None else None
        if objId is not None and objId != self._lastFocusObjId:
            self._lastFocusObjId = objId
            return False
        shouldDrop = True
        # Read extreme flag fresh each event so toggles apply everywhere.
        section = self._getSettingsSection()
        extreme = _coerce_bool(section.get(self.SETTINGS_EXTREME_KEY, self.DEFAULT_EXTREME_MODE), self.DEFAULT_EXTREME_MODE)
        if not self._loggedSuppressionIntro and extreme:
            log.info("QuietConsole suppression active for pid %s (extreme=%s)", self.processID, extreme)
            self._loggedSuppressionIntro = True
        if self._logSuppression:
            log.debug("QuietConsole suppressed %s event (extreme=%s)", name, extreme)
        if extreme and self._shouldCancelSpeech():
            try:
                speech.cancelSpeech()
            except Exception:
                pass
        return shouldDrop

    def _shouldCancelSpeech(self) -> bool:
        # In extreme mode, cancel queued speech unless the user is actively reading.
        if self._manualSpeechActive:
            if _speechIsSpeaking:
                try:
                    if _speechIsSpeaking():
                        return False
                except Exception:
                    return False
            self._manualSpeechActive = False
        if _speechIsSpeaking:
            try:
                if _speechIsSpeaking():
                    return False
            except Exception:
                return False
        return self._limiter.allows()

    # -------------------------- Scripts -----------------------------------

    @script(
        description=_("Toggle quiet console mode for this terminal window."),
    )
    def script_toggleQuietConsoleMode(self, gesture):
        newState = not self._isQuietModeEnabled()
        self._setQuietModeEnabled(newState)
        state = _("enabled") if newState else _("disabled")
        ui.message(_("Quiet console mode {state}.").format(state=state))
        log.info("QuietConsole mode now %s for pid %s", state, self.processID)

    @script(
        description=_(
            "Read the last part of the console buffer without re-enabling live updates."
        )
    )
    def script_readRecentConsoleLines(self, gesture):
        focus = api.getFocusObject()
        if not focus:
            msg = _("No focus object to read.")
            ui.message(msg)
            return
        self._manualSpeechActive = True
        try:
            info = focus.makeTextInfo(textInfos.POSITION_LAST)
        except Exception:
            msg = _("Unable to examine console text.")
            ui.message(msg)
            return

        collected = self._collectTrailingLines(info, self.READ_LAST_LINES)
        # fall back to configured value if constant differs
        if not collected and self.READ_LAST_LINES != self._readLastLines:
            collected = self._collectTrailingLines(info, self._readLastLines)
        if not collected:
            msg = _("No console text available yet.")
            ui.message(msg)
            return

        joined = "\n".join(collected)
        ui.message(joined)
        try:
            tail = focus.makeTextInfo(textInfos.POSITION_LAST)
            api.setReviewPosition(tail)
        except Exception:
            pass
        log.info("QuietConsole read %d tail lines for pid %s", len(collected), self.processID)

    def _collectTrailingLines(self, info, limit: int):
        lines = []
        cursor = info.copy()
        try:
            cursor.expand(textInfos.UNIT_LINE)
        except Exception:
            return lines
        lines.append(self._cleanLine(cursor.text))
        for _ in range(limit - 1):
            try:
                cursor.previousLine()
            except Exception:
                break
            temp = cursor.copy()
            try:
                temp.expand(textInfos.UNIT_LINE)
            except Exception:
                break
            lines.insert(0, self._cleanLine(temp.text))
        return [line for line in lines if line]

    @staticmethod
    def _cleanLine(text: str) -> str:
        return (text or "").strip().rstrip("\r\n")
    @classmethod
    def updateSettings(cls, *, quietMode=None, readLastLines=None, logSuppression=None, extremeMode=None):
        if quietMode is not None:
            cls._setQuietModeEnabled(bool(quietMode))
        section = cls._getSettingsSection()
        if readLastLines is not None:
            cls._readLastLines = int(readLastLines)
            section["readLastLines"] = cls._readLastLines
        if logSuppression is not None:
            cls._logSuppression = bool(logSuppression)
            section["logSuppression"] = cls._logSuppression
        if extremeMode is not None:
            cls._setExtremeModeEnabled(bool(extremeMode))
        config.conf.save()
