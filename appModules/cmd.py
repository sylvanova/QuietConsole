import addonHandler

addonHandler.initTranslation()

import api
import config
import speech
import textInfos
import ui
import wx
from appModuleHandler import AppModule as BaseAppModule
from logHandler import log
from scriptHandler import script
import time
import re
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


def _coerce_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "on")
    if val is None:
        return default
    return bool(val)


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


_speechIsSpeaking = getattr(speech, "isSpeaking", None)


class _LiveConsoleTextDialog(wx.Dialog):
    """Hotkey-opened read-only window that mirrors console text live."""

    TIMER_INTERVAL_MS = 500
    MAX_BUFFER_CHARS = 200000

    def __init__(self, parent, appModule, sourceObj):
        super().__init__(
            parent,
            title="Quiet Console - Live Plain Text",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._appModule = appModule
        self._sourceObj = sourceObj
        self._lastText = ""
        self._followBottom = True
        self._timer = wx.Timer(self)
        self._textCtrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
        )
        self._textCtrl.Bind(wx.EVT_SET_FOCUS, self._onTextFocus)
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(self._textCtrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
        self.SetSizer(root)
        self.SetSize((900, 600))
        self.Bind(wx.EVT_TIMER, self._onTimer, self._timer)
        self.Bind(wx.EVT_CLOSE, self._onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self._onCharHook)
        self._timer.Start(self.TIMER_INTERVAL_MS)
        self.refreshNow()
        wx.CallAfter(self._placeAtLatestLineStart)
        wx.CallLater(80, self._placeAtLatestLineStart)

    def _onTimer(self, evt):
        self.refreshNow()

    def refreshNow(self):
        text = self._appModule._getLiveConsoleText(sourceObj=self._sourceObj)
        if text is None:
            return
        text = self._appModule._cleanPlainTextForView(text)
        if len(text) > self.MAX_BUFFER_CHARS:
            text = text[-self.MAX_BUFFER_CHARS:]
        if text == self._lastText:
            return
        # Read current cursor line.
        numOldLines = max(1, self._textCtrl.GetNumberOfLines())
        curLine = 0
        try:
            ok, _col, row = self._textCtrl.PositionToXY(
                self._textCtrl.GetInsertionPoint()
            )
            if ok:
                curLine = row
        except Exception:
            pass
        # Read selection endpoints as line/col.
        selFrom, selTo = self._textCtrl.GetSelection()
        hasSelection = selFrom != selTo
        selSL = selSC = selEL = selEC = 0
        if hasSelection:
            try:
                ok1, sc, sr = self._textCtrl.PositionToXY(selFrom)
                ok2, ec, er = self._textCtrl.PositionToXY(selTo)
                if ok1 and ok2:
                    selSL, selSC, selEL, selEC = sr, sc, er, ec
                else:
                    hasSelection = False
            except Exception:
                hasSelection = False
        # Replace text without generating wx events.
        self._textCtrl.ChangeValue(text)
        numNewLines = max(1, self._textCtrl.GetNumberOfLines())
        if self._followBottom:
            # Anchor relative to the bottom of the document.
            offsetFromBottom = max(0, numOldLines - 1 - curLine)
            targetLine = max(0, numNewLines - 1 - offsetFromBottom)
        else:
            # Fixed line mode: stay on the same line number.
            targetLine = max(0, min(curLine, numNewLines - 1))
        pos = self._textCtrl.XYToPosition(0, targetLine)
        if pos < 0:
            pos = 0
        self._textCtrl.SetInsertionPoint(pos)
        # Restore selection if the user had one.
        if hasSelection:
            if self._followBottom:
                sOff = max(0, numOldLines - 1 - selSL)
                eOff = max(0, numOldLines - 1 - selEL)
                sl = max(0, numNewLines - 1 - sOff)
                el = max(0, numNewLines - 1 - eOff)
            else:
                sl = max(0, min(selSL, numNewLines - 1))
                el = max(0, min(selEL, numNewLines - 1))
            sp = self._textCtrl.XYToPosition(selSC, sl)
            ep = self._textCtrl.XYToPosition(selEC, el)
            if sp < 0:
                sp = self._textCtrl.XYToPosition(0, sl)
            if ep < 0:
                ep = self._textCtrl.XYToPosition(0, el)
            if sp >= 0 and ep >= 0 and sp != ep:
                self._textCtrl.SetSelection(sp, ep)
        self._lastText = text

    def _moveCaretToEnd(self):
        try:
            self._textCtrl.SetFocus()
            self._moveCaretToLastLineStart()
        except Exception:
            pass

    def _placeAtLatestLineStart(self):
        self._moveCaretToEnd()

    def _moveCaretToLastLineStart(self):
        numLines = self._textCtrl.GetNumberOfLines()
        if numLines <= 0:
            self._textCtrl.SetInsertionPoint(0)
            self._textCtrl.SetSelection(0, 0)
            self._textCtrl.ShowPosition(0)
            return
        lastLine = numLines - 1
        pos = self._textCtrl.XYToPosition(0, lastLine)
        if pos < 0:
            pos = self._textCtrl.GetLastPosition()
        # Force viewport to the true end first; then place caret at start of last line.
        lastPos = self._textCtrl.GetLastPosition()
        self._textCtrl.SetInsertionPoint(lastPos)
        self._textCtrl.ShowPosition(lastPos)
        self._textCtrl.SetInsertionPoint(pos)
        self._textCtrl.SetSelection(pos, pos)
        self._textCtrl.ShowPosition(pos)

    def _onClose(self, evt):
        if self._timer.IsRunning():
            self._timer.Stop()
        self._appModule._plainTextDialog = None
        evt.Skip()

    def _onCharHook(self, evt):
        key = evt.GetKeyCode()
        mods = evt.GetModifiers()
        if key == wx.WXK_ESCAPE:
            self.Close()
            return
        if key == wx.WXK_END and mods in (wx.MOD_NONE,):
            self._moveCaretToLastLineStart()
            return
        if key == wx.WXK_F5 and mods == wx.MOD_NONE:
            self._followBottom = not self._followBottom
            if self._followBottom:
                ui.message(_("Follow bottom"))
            else:
                ui.message(_("Fixed line"))
            return
        evt.Skip()

    def _onTextFocus(self, evt):
        # Focus changes should not alter cursor anchor/position.
        evt.Skip()


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
    DEFAULT_LOG_SUPPRESSION = False
    _ansiEscapePattern = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    _symbolLinePattern = re.compile(r"^[\s\W_]+$")
    _separatorPattern = re.compile(r"^\s*([\-=_~#*.`|:])\1{7,}\s*$")
    _logSuppression = DEFAULT_LOG_SUPPRESSION

    __gestures = {
        "kb:NVDA+shift+c": "toggleQuietConsoleMode",
        "kb:NVDA+shift+v": "togglePlainTextView",
        "kb:NVDA+alt+v": "togglePlainTextView",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logSuppression = _coerce_bool(
            self._getSettingsSection().get(
                "logSuppression", self.DEFAULT_LOG_SUPPRESSION
            ),
            self.DEFAULT_LOG_SUPPRESSION,
        )
        self._extremeMode = self._isExtremeModeEnabled()
        self._loggedSuppressionIntro = False
        self._plainTextDialog = None
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
        # configobj sections in NVDA do not always expose dict helpers like setdefault.
        try:
            section[cls.SETTINGS_KEY]
        except Exception:
            section[cls.SETTINGS_KEY] = cls.DEFAULT_QUIET_MODE
        try:
            section[cls.SETTINGS_EXTREME_KEY]
        except Exception:
            section[cls.SETTINGS_EXTREME_KEY] = cls.DEFAULT_EXTREME_MODE
        try:
            section["logSuppression"]
        except Exception:
            section["logSuppression"] = cls.DEFAULT_LOG_SUPPRESSION
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

    def event_UIA_notification(self, obj, nextHandler, *args, **kwargs):
        if self._shouldSuppressEvent("UIA_notification", obj):
            return
        nextHandler()

    def event_gainFocus(self, obj, nextHandler):
        if self._shouldSuppressEvent("gainFocus", obj):
            return
        nextHandler()

    def event_focusEntered(self, obj, nextHandler):
        if self._shouldSuppressEvent("focusEntered", obj):
            return
        nextHandler()

    def event_show(self, obj, nextHandler):
        if self._shouldSuppressEvent("show", obj):
            return
        nextHandler()

    def event_descriptionChange(self, obj, nextHandler):
        if self._shouldSuppressEvent("descriptionChange", obj):
            return
        nextHandler()

    def event_stateChange(self, obj, nextHandler):
        if self._shouldSuppressEvent("stateChange", obj):
            return
        nextHandler()

    def event_alert(self, obj, nextHandler):
        if self._shouldSuppressEvent("alert", obj):
            return
        nextHandler()

    def _shouldSuppressEvent(self, name: str, obj) -> bool:
        if not self._isQuietModeEnabled():
            return False
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
        return True

    def _shouldCancelSpeech(self) -> bool:
        if _speechIsSpeaking:
            try:
                if not _speechIsSpeaking():
                    return False
            except Exception:
                return self._limiter.allows()
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
        description=_("Toggle live plain text view for this terminal window."),
    )
    def script_togglePlainTextView(self, gesture):
        log.info("QuietConsole plain view toggle requested for pid %s", self.processID)
        if self._plainTextDialog and self._plainTextDialog.IsShown():
            self._plainTextDialog.Close()
            ui.message(_("Plain text view closed."))
            return
        sourceObj = self._findLiveTextSource()
        initialText = self._getLiveConsoleText(sourceObj=sourceObj)
        if initialText is None:
            log.warning("QuietConsole plain view opened without initial text source (pid=%s)", self.processID)
        self._plainTextDialog = _LiveConsoleTextDialog(None, self, sourceObj)
        self._plainTextDialog.Show()
        self._plainTextDialog.Raise()
        wx.CallAfter(self._plainTextDialog._placeAtLatestLineStart)
        wx.CallLater(60, self._plainTextDialog._placeAtLatestLineStart)
        wx.CallLater(180, self._plainTextDialog._placeAtLatestLineStart)
        ui.message(_("Plain text view opened."))

    def _candidateTextObjects(self, sourceObj=None):
        def _belongsToThisModule(obj):
            try:
                mod = getattr(obj, "appModule", None)
                return bool(mod and getattr(mod, "processID", None) == self.processID)
            except Exception:
                return False

        if sourceObj is not None:
            yield sourceObj
            parent = getattr(sourceObj, "parent", None)
            for _ in range(6):
                if not parent:
                    break
                yield parent
                parent = getattr(parent, "parent", None)
        focus = api.getFocusObject()
        candidates = []
        if focus and _belongsToThisModule(focus):
            candidates.append(focus)
            parent = getattr(focus, "parent", None)
            for _ in range(6):
                if not parent:
                    break
                if _belongsToThisModule(parent):
                    candidates.append(parent)
                parent = getattr(parent, "parent", None)
        nav = api.getNavigatorObject()
        if nav and _belongsToThisModule(nav):
            candidates.append(nav)
        fg = api.getForegroundObject()
        if fg and _belongsToThisModule(fg):
            candidates.append(fg)
            parent = getattr(fg, "parent", None)
            for _ in range(6):
                if not parent:
                    break
                if _belongsToThisModule(parent):
                    candidates.append(parent)
                parent = getattr(parent, "parent", None)
        for obj in candidates:
            yield obj

    def _extractTextFromObject(self, obj):
        if not obj:
            return None
        try:
            info = obj.makeTextInfo(textInfos.POSITION_ALL)
        except Exception:
            return None
        try:
            text = (info.text or "").replace("\r\n", "\n")
        except Exception:
            return None
        return text or None

    def _findLiveTextSource(self):
        seen = set()
        for obj in self._candidateTextObjects():
            if not obj:
                continue
            objId = id(obj)
            if objId in seen:
                continue
            seen.add(objId)
            if self._extractTextFromObject(obj):
                return obj
        return None

    def _getLiveConsoleText(self, sourceObj=None):
        seen = set()
        for obj in self._candidateTextObjects(sourceObj=sourceObj):
            if not obj:
                continue
            objId = id(obj)
            if objId in seen:
                continue
            seen.add(objId)
            text = self._extractTextFromObject(obj)
            if text:
                return text
        return None

    def _cleanPlainTextForView(self, text):
        text = self._ansiEscapePattern.sub("", text or "")
        # Keep CRLF normalization, but do not convert lone CR to newline.
        # Terminal progress updates often use CR to rewrite the same line.
        text = text.replace("\r\n", "\n").replace("\r", "")
        cleaned = []
        for raw in text.split("\n"):
            line = raw.rstrip().lstrip(" \t")
            if not line.strip():
                continue
            if self._symbolLinePattern.match(line):
                continue
            if self._separatorPattern.match(line):
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def terminate(self):
        if self._plainTextDialog:
            try:
                self._plainTextDialog.Destroy()
            except Exception:
                pass
            self._plainTextDialog = None
        super().terminate()

    @classmethod
    def updateSettings(cls, *, quietMode=None, logSuppression=None, extremeMode=None):
        if quietMode is not None:
            cls._setQuietModeEnabled(bool(quietMode))
        section = cls._getSettingsSection()
        if logSuppression is not None:
            cls._logSuppression = bool(logSuppression)
            section["logSuppression"] = cls._logSuppression
        if extremeMode is not None:
            cls._setExtremeModeEnabled(bool(extremeMode))
        config.conf.save()
