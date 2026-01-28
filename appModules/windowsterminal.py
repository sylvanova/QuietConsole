"""Reuse QuietConsole AppModule for WindowsTerminal.exe."""
from .cmd import AppModule as CmdAppModule


class AppModule(CmdAppModule):
    pass

