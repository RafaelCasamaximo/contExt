from .core import Callbacks
from .ui import Interface


class App:
    def __init__(self) -> None:
        self.interface = Interface(Callbacks())


def run() -> App:
    return App()
