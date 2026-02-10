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
from translations import tr as _


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
            title=_("Quiet Console - Live Plain Text"),
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
        ctrlShift = wx.MOD_CONTROL | wx.MOD_SHIFT
        if key == wx.WXK_DOWN and mods == ctrlShift:
            self._selectLinesDown()
            return
        if key == wx.WXK_UP and mods == ctrlShift:
            self._selectLinesUp()
            return
        evt.Skip()

    def _selectLinesDown(self):
        numLines = self._textCtrl.GetNumberOfLines()
        if numLines <= 0:
            return
        selFrom, selTo = self._textCtrl.GetSelection()
        if selFrom == selTo:
            ok, _, row = self._textCtrl.PositionToXY(
                self._textCtrl.GetInsertionPoint()
            )
            if not ok:
                return
            anchor = self._textCtrl.XYToPosition(0, row)
            targetRow = row
        else:
            anchor = selFrom
            ok, _, row = self._textCtrl.PositionToXY(selTo)
            if not ok:
                return
            targetRow = row
        if targetRow + 1 < numLines:
            endPos = self._textCtrl.XYToPosition(0, targetRow + 1)
        else:
            endPos = self._textCtrl.GetLastPosition()
        if anchor >= 0 and endPos >= 0:
            self._textCtrl.SetSelection(anchor, endPos)

    def _selectLinesUp(self):
        numLines = self._textCtrl.GetNumberOfLines()
        if numLines <= 0:
            return
        selFrom, selTo = self._textCtrl.GetSelection()
        if selFrom == selTo:
            ok, _, row = self._textCtrl.PositionToXY(
                self._textCtrl.GetInsertionPoint()
            )
            if not ok:
                return
            startPos = self._textCtrl.XYToPosition(0, row)
            if row + 1 < numLines:
                endPos = self._textCtrl.XYToPosition(0, row + 1)
            else:
                endPos = self._textCtrl.GetLastPosition()
        else:
            ok, _, startRow = self._textCtrl.PositionToXY(selFrom)
            if not ok:
                return
            targetRow = max(0, startRow - 1)
            startPos = self._textCtrl.XYToPosition(0, targetRow)
            endPos = selTo
        if startPos >= 0 and endPos >= 0:
            self._textCtrl.SetSelection(startPos, endPos)

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
            line = " ".join(raw.split())
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

