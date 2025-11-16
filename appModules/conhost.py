"""Allow the same QuietConsole logic to run for conhost.exe windows."""
from .cmd import AppModule as CmdAppModule


class AppModule(CmdAppModule):
    pass
