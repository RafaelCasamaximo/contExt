"""
Classe Pixel serve como auxiliar de ProcessaImagem. Consegue guarda uma coordenada (x, y) e um valor (esperado de 0 a 255)
Seu comparador foi implementado para retornar True se todos os seus atributos são iguais. Isso é utilizado como condição de parada no algoritmo de extraiContorno em ProcessaImagem
"""
class Pixel:
        def __init__(self, x, y, value):
            self.x = x
            self.y = y
            self.value = value

        def __eq__(self, other):
            if isinstance(other, Pixel):
                return other.x == self.x and other.y == self.y and other.value == self.value
            
            return False