import cv2
import json
from pixel import Pixel
from pprint import pprint
from datetime import datetime


class ContourExtraction:

    """
    Constructor da classe ContourExtraction
    Path é o caminho até a imagem desejada
    A imagem (por enquanto) deve ser em preto em branco. Caso seja uma imagem colorida o programa converterá automaticamente para preto e branco UTILIZANDO APENAS O CANAL BLUE,
    resultado do formato BGR

    path: caminho de entrada da imagem
    img: 3d array que guarda valor BGR da imagem [x][y][BGR]
    yTotal: valor total de linhas que tem (pixeis de altura)
    xTotal: valor total de colunas que tem (pixeis de largura)
    area: valor da área calculada pelo método de Gauss do contorno
    bidimensional_image: 2d array com [x][y] e do mesmo tamanho que img, o valor de cada posição é o valor B da img 
    MOORE_OFFSET: coordenadas que representam os 8 pontos adjascentes do ponto atual, representandos por (x, y)
    """

    def __init__(self, figurePath):
        self.figurePath = figurePath
        self.img = cv2.imread(figurePath, cv2.COLOR_BGR2GRAY)
        self.yTotal = self.img.shape[0]
        self.xTotal = self.img.shape[1]
        self.area = 0
        self.bidimensional_image = [
            [0] * self.xTotal for i in range(self.yTotal)]
        """
        |4|5|6|
        |3|P|7|
        |2|1|8|
        """
        self.MOORE_OFFSET = [[0, -1], [-1, -1], [-1, 0],
                             [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1]]
        self.boundary = []


    """
    Essa função é reponsável por 3 partes principais:
    1- Encontrar o ponto inicial para o algoritmo
    2- Extrair todos os pontos subsequentes da figura em sentido horário até encontrar o ponto inicial novamente
    3- Realizar o log de dados em um txt para ser utilizado posteriormente
    """

    def extrai_contorno(self):
        self.boundary = []
        # Converte imagem RGB para imagem PB
        self.convert_3d_to_2d_image_array()
        # Encontra o primeiro pixel branco
        startPixel = self.encontra_ponto_inicial()
        self.boundary.append(startPixel)
        pixel = startPixel
    
        backtrackIndexStart = 5
        countourPixel, backtrackIndexStart = self.moore_neighborhood(
            pixel, backtrackIndexStart)
        self.boundary.append(countourPixel)

        while countourPixel != startPixel:
            countourPixel, backtrackIndexStart = self.moore_neighborhood(
                countourPixel, backtrackIndexStart)
            self.boundary.append(countourPixel)

        xmin = min(self.boundary, key = lambda x:x.x).x
        ymin = min(self.boundary, key = lambda x:x.y).y
        xmax = max(self.boundary, key = lambda x:x.x).x
        ymax = max(self.boundary, key = lambda x:x.y).y
        self.nx = xmax - xmin
        self.ny = ymax - ymin

    """
    Função responsável por exportar o resultado da extração de contorno em um arquivo path
    """

    def exporta_contorno(self, path, interval):
        nx = self.nx
        ny = self.ny
        xmin = min(self.boundary, key = lambda x:x.x).x
        ymin = min(self.boundary, key = lambda x:x.y).y
        xmax = max(self.boundary, key = lambda x:x.x).x
        ymax = max(self.boundary, key = lambda x:x.y).y
        try:
            resultado = ""
            with open(path, "w") as dataFile:
                resultado = resultado + str(nx) + " " + str(ny) + '\n'
                resultado = resultado + str(xmin) + " " + str(ymin) + '\n'
                resultado = resultado + str(xmax) + " "  + str(ymax) + '\n'
                resultado = resultado + str((xmax - xmin)/nx) + " " + str((ymax - ymin)/ny) + '\n'
                resultado = resultado + self.converte_pixelArray_to_string(
                    self.boundary, interval)
                dataFile.write(resultado)
        except:
            print('Path does not exist for boundary export')
            return

    """
    A partir de uma certa imagem em 3 dimensões, dada pelo openCv no formato de cores BGR, em valores que alternam entre 0 e 255 (min e max),
    essa função converte para uma imagem somente em 2 dimensões [x][y] no qual o valor cas posições é dado através do canal B entre 0 e 255
    """

    def convert_3d_to_2d_image_array(self):
        for i in range(self.yTotal):
            for j in range(self.xTotal):
                self.bidimensional_image[i][j] = self.img[i][j][1]

    """
    Extrai o ponto inicial para começar o algoritmo de moore_neighborhood
    Percorre a imagem de baixo pra cima, da esquerda pra direita para encontrar o primeiro pixel branco. Após isso, retorna esse pixel (x, y, value)
    """

    def encontra_ponto_inicial(self):
        for i in range(self.yTotal - 1, -1, -1):
            for j in range(self.xTotal):
                if self.bidimensional_image[i][j] == 255:
                    pixel = Pixel(j, i, 255)
                    return pixel

    """
    Essa função é o "Core" do programa. Ela identifica o próximo ponto em sentido horário e o ponto de entrada para ele (backtrack).
    Ele percorre os 8 pixeis adjascentes em sentido horário até encontrar o primeiro pixel branco.
    Para evitar que o primeiro pixel faça parte do conjunto branco em algum dos lados, o ponto de partida é sempre o lado oposto
    ao lado inicial. Esse backtrack também é retornado para o próximo ponto
    """

    def moore_neighborhood(self, p, backtrackIndex):
        for i in range(8):
            index = (i + backtrackIndex) % 8
            neighborX = p.x + self.MOORE_OFFSET[index][0]
            neighborY = p.y + self.MOORE_OFFSET[index][1]
            try:
                neighborValue = self.bidimensional_image[neighborY][neighborX]
            except:
                neighborValue = 0
            neighborPixel = Pixel(neighborX, neighborY, neighborValue)
            if neighborPixel.value == 255:
                self.img[neighborY][neighborX] = [255, 0, 0]
                return neighborPixel, index + 5

    """
    Essa função é utilizada para converter um array de pixeis em uma string para ser impressa no arquivo de texto. Retorna a string.
    """

    def converte_pixelArray_to_string(self, array, intervalo):
        intervalo = intervalo
        content = ''
        i = 0
        while i < len(array):
            element = array[i]
            content = content + str(element.x) + " " + str(element.y) + "\n"
            i += intervalo + 1

        return content

    """
    Essa função altera a escala e o offset do conjunto do contorno após a extração dele.
    Caso os valores sejam -1 o atributo será ignorado na alteração da escala
    """

    def altera_escala(self, width, height, startXOffset, startYOffset):
        widthCoef = width / self.xTotal
        heightCoef = height / self.yTotal

        for pixel in self.boundary:
            if width != -1:
                pixel.x = pixel.x * widthCoef
            if startXOffset != -1:
                pixel.x = pixel.x + startXOffset
            if height != -1:
                pixel.y = pixel.y * heightCoef
            if startYOffset != -1:
                pixel.y = pixel.y + startYOffset

    """
    Essa função converte o resultado obtido para o matlab, pois em uma imagem o ponto (0, 0) é o ponto
    superior esquerda da imagem, e no matlab o ponto (0, 0) é dado pela coordenada inferior esquerda
    """

    def converte_matlab(self):
        for pixel in self.boundary:
            pixel.y = self.yTotal - pixel.y



    """
    Essa função utiliza de JSON para exportar metadata calculada e dada como input pelo programa
    """

    def exporta_metadata(self, output, width, height, xoffset, yoffset):
        data = {}
        data['metadata'] = []
        data['metadata'].append({
            'figure': self.figurePath,
            'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'width:': width,
            'height': height,
            'xoffset': xoffset,
            'yoffset': yoffset,
            'area': self.area,
        })
        try:
            with open(output, "w") as configFile:
                json.dump(data, configFile)
        except:
            print('Failed at exporting config file.')
            return