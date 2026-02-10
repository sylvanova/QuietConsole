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

from translations import tr as _

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



