"""Reuse QuietConsole AppModule for wt.exe (Windows Terminal launcher)."""
from .cmd import AppModule as CmdAppModule


class AppModule(CmdAppModule):
    pass

