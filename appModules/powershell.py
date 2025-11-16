"""Reuse QuietConsole AppModule for Windows PowerShell hosts."""
from .cmd import AppModule as CmdAppModule


class AppModule(CmdAppModule):
    pass

