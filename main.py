from interface import Interface
from callbacks import Callbacks

"""
    A classe app é responsável pela execução do programa como um todo, e é o ponto de partida.
"""
class App:
    def __init__(self) -> None:
        self.interface = Interface(Callbacks())
        pass


if __name__ == '__main__':
   app = App()