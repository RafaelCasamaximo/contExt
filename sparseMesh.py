
from mesh import Mesh


class ProcessaMalhaEsparsa:

    """
    Constructor da classe ProcessaMalha
    x e y são vetores que representam as coordenadas que representam a figura que será representada na malha
    xmin e ymin são os valores mínimos da malha
    defaultmin define se os valores mínimos são informados ou calculados automaticamente
    nx e ny são os números de nós da malha em cada eixo
    dx e dy são os tamanhos do nó da malha em cada eixo
    é necessário que pelo menos o tamanho ou número de nós seja informado
    mesh é onde as coordenadas dos nós da malha gerada serão armazenadas
    """

    def __init__(self):
        self.ranges = []
        self.dx = []
        self.dy = []
    
    """
    Adiciona informações da região da malha
    """

    def addRange(self, xmin, ymin, xmax, ymax, nx, ny):
        flag = True
        if len(self.ranges) == 0:
            dx = (xmax - xmin)/(nx - 1)
            dy = (ymax - ymin)/(ny - 1)
        else:
            r = self.ranges[0]
            xmin = (xmin - r["xi"]) // r["dx"] * r["dx"] + r["xi"]
            ymin = (ymin - r["yi"]) // r["dy"] * r["dy"] + r["yi"]
            xmax = (xmax - r["xi"]) // r["dx"] * r["dx"] + r["xi"]
            ymax = (ymax - r["yi"]) // r["dy"] * r["dy"] + r["yi"]
            for i in self.ranges[1:]:
                if i["xmin"] <= xmin <= i ["xmax"] or i["xmin"] <= xmax <= i["xmax"] or i["ymin"] <= ymin <= i["ymax"] or i["ymin"] <= ymax <= i["ymax"]:
                    print("Invalid range due to overlap")
                    flag = False
            dx = r["dx"]/(2**nx)
            dy = r["dy"]/(2**ny)
            nx = round((xmax - xmin)/dx) + 1
            ny = round((ymax - ymin)/dy) + 1
        if flag:
            aux = {
                "nx" : nx,
                "ny" : ny,
                "xi" : xmin,
                "yi" : ymin,
                "xf" : xmax,
                "yf" : ymax,
                "dx" : dx,
                "dy" : dy
            }
            self.ranges.append(aux)

    """
    Obtem os intervalos da malha
    """

    def setIntervals(self):
        self.dx = []
        self.dy = []

        xaux = sorted(self.ranges, key = lambda value: value["dx"])
        aux = []
        for r in xaux:
            for i in range(r["nx"]):
                x = r["xi"] + i * r["dx"]
                if all([x < a or x > b for a,b in aux]):
                    self.dx.append(x)
            aux.append([r["xi"], r["xf"]])

        yaux = sorted(self.ranges, key = lambda value: value["dy"])
        aux = []
        for r in yaux:
            for i in range(r["ny"]):
                y = r["yi"] + i * r["dy"]
                if all([y < a or y > b for a,b in aux]):
                    self.dy.append(y)
            aux.append([r["yi"], r["yf"]])
        
        self.dx.sort()
        self.dy.sort()




    """
    Retorna o valor de x da coordenada do nó da malha onde o ponto informado está 
    """

    def getXNode(self, xpoint):
        for i in range(len(self.dx) - 1):
            if xpoint >= self.dx[i] and xpoint < self.dx[i + 1]:
                return self.dx[i] 
        if xpoint == self.dx[-1]:
            return self.dx[-1]
        print("A figura é maior que os limites da malha")
        quit(1)

    
    """
    Retorna o valor de y da coordenada do nó da malha onde o ponto informado está 
    """
    
    def getYNode(self, ypoint):
        for i in range(len(self.dy) - 1):
            if ypoint >= self.dy[i] and ypoint < self.dy[i + 1]:
                return self.dy[i] 
        if ypoint == self.dy[-1]:
            return self.dy[-1]
        print("A figura é maior que os limites da malha")
        print(ypoint)
        quit(1)

    
    """
    Percore x e y, obtendo os nós da malha para cada ponto com a função getNode, 
    e removendo nós irrelevantes.
    """

    def get_adaptative_mesh(self, x, y):
        self.setIntervals()
        xResult = []
        yResult = []
        prevpoint = [self.getXNode(x[0]), self.getYNode(y[0])] 
        xResult.append(prevpoint[0])
        yResult.append(prevpoint[1])
        flagx = 0
        flagy = 0
        dirx = prevpoint[0] > x[-2]
        diry = prevpoint[1] > y[-2]
        tam = len(x)
        for i in range(1,tam):
            point = [self.getXNode(x[i]), self.getYNode(y[i])]
            if point[0] != prevpoint[0] or point[1] != prevpoint[1]:
                if flagx and point[1] == prevpoint[1] and ((point[0] > prevpoint[0]) != diry):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                elif flagy and point[0] == prevpoint[0] and ((point[1] > prevpoint[1]) == dirx):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                elif flagy and point[1] == prevpoint[1] and ((point[0] > prevpoint[0]) != dirx):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                elif flagx and point[0] == prevpoint[0] and ((point[1] > prevpoint[1]) != diry):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                else:
                    xResult.append(point[0])
                    yResult.append(point[1])
                flagx = 0
                flagy = 0
                if point[0] == xResult[-2]:
                    flagx = 1
                elif point[1] == yResult[-2]:
                    flagy = 1
                dirx = point[0] > xResult[-2]
                diry = point[1] > yResult[-2]
                prevpoint = point
        point = [xResult[0], yResult[0]]
        if flagx:
            if point[1] == prevpoint[1]:
                xResult[-1] = point[0]
                yResult[-1] = point[1]
        elif flagy:
            if point[0] == prevpoint[0]:
                xResult[-1] = point[0]
                yResult[-1] = point[1]
        if point[0] != prevpoint[0] or point[1] != prevpoint[1]:
            xResult.append(point[0])
            yResult.append(point[1])
        return xResult, yResult

    """
    Retorna a coordenada do nó da malha onde o ponto informado está 
    """


    def getNode(self, xpoint, ypoint):
        auxX = xpoint
        auxY = ypoint
        flag = 0
        for r in self.ranges[::-1]:
            if r["xi"] <= xpoint <= r["xf"] and r["yi"] <= ypoint <= r["yf"]:
                auxX = (xpoint - r["xi"]) // r["dx"] * r["dx"] + r["xi"]
                auxY = (ypoint - r["yi"]) // r["dy"] * r["dy"] + r["yi"]
                flag = 1
                break
        if flag:
            return[auxX, auxY] 
        print("A figura é maior que os limites da malha")
        quit(1)

    """
    Percore x e y, obtendo os nós da malha irregular para cada ponto com a função getNode, 
    e removendo nós irrelevantes.
    """

    def get_sparse_mesh(self, x, y):
        xResult = []
        yResult = []
        prevpoint = self.getNode(x[0], y[0])
        xResult.append(prevpoint[0])
        yResult.append(prevpoint[1])
        flagx = 0
        flagy = 0
        dirx = prevpoint[0] > x[-2]
        diry = prevpoint[1] > y[-2]
        tam = len(x)
        for i in range(1,tam):
            point = self.getNode(x[i], y[i])
            if point[0] != prevpoint[0] or point[1] != prevpoint[1]:
                if flagx and point[1] == prevpoint[1] and ((point[0] > prevpoint[0]) != diry):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                elif flagy and point[0] == prevpoint[0] and ((point[1] > prevpoint[1]) == dirx):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                elif flagy and point[1] == prevpoint[1] and ((point[0] > prevpoint[0]) != dirx):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                elif flagx and point[0] == prevpoint[0] and ((point[1] > prevpoint[1]) != diry):
                    xResult[-1] = point[0]
                    yResult[-1] = point[1]
                else:
                    xResult.append(point[0])
                    yResult.append(point[1])
                flagx = 0
                flagy = 0
                if point[0] == xResult[-2]:
                    flagx = 1
                elif point[1] == yResult[-2]:
                    flagy = 1
                dirx = point[0] > xResult[-2]
                diry = point[1] > yResult[-2]
                prevpoint = point
        point = [xResult[0], yResult[0]]
        if flagx:
            if point[1] == prevpoint[1]:
                xResult[-1] = point[0]
                yResult[-1] = point[1]
        elif flagy:
            if point[0] == prevpoint[0]:
                xResult[-1] = point[0]
                yResult[-1] = point[1]
        if point[0] != prevpoint[0] or point[1] != prevpoint[1]:
            xResult.append(point[0])
            yResult.append(point[1])
        return xResult, yResult


    
    """
    Adiciona as informações das regiões da malha em um arquivo
    """

    def export_ranges(self, path):
        try:
            with open(path, "w") as dataFile:
                content = ''
                for i in self.ranges:
                    aux = ' '.join([str(elem) for elem in i.values()])
                    content = content + aux + "\n"
                dataFile.write(content)
        except:
            print('Path does not exist for export')
            return


    def export_coords_mesh(path, x, y):
        content = ''
        try:
            with open(path, "w") as dataFile:
                content += Mesh.converte_pointArray_to_string(x, y)
                dataFile.write(content)
        except:
            print('Path does not exist for mesh export')
            return
    
    def export_node_size_mesh(self, pathX, pathY):
        try:
            content = ''
            with open(pathX, "w") as dataFile:
                for i in self.dx:
                    content += str(i) + "\n"
                dataFile.write(content)
        except:
            print('Path for dx does not exist for mesh export')

        try:
            content = ''
            with open(pathY, "w") as dataFile:
                for i in self.dy:
                    content += str(i) + "\n"
                dataFile.write(content)
        except:
            print('Path for dy does not exist for mesh export')
            return

