from interface import Interface
from callbacks import Callbacks

class App:
    def __init__(self) -> None:
        self.interface = Interface(Callbacks())
        pass


if __name__ == '__main__':
   app = App()