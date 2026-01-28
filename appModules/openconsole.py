"""Reuse QuietConsole AppModule for OpenConsole.exe (Windows Terminal host)."""
from .cmd import AppModule as CmdAppModule


class AppModule(CmdAppModule):
    pass
