"""Reuse QuietConsole AppModule for PowerShell 7 (pwsh.exe)."""
from .cmd import AppModule as CmdAppModule


class AppModule(CmdAppModule):
    pass

