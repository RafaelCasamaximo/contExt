
from ._mesh import Mesh
from ._numeric import divide_distance, fitted_grid_end, grid_coordinate, snap_down_to_grid, values_close


class SparseMesh:

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

    def subdivide(self, levels):
        """Refine every range while retaining all nodes from the previous grid."""
        factor = Mesh.subdivisionFactor(levels)
        for meshRange in self.ranges:
            meshRange["nx"] = (int(meshRange["nx"]) - 1) * factor + 1
            meshRange["ny"] = (int(meshRange["ny"]) - 1) * factor + 1
            meshRange["dx"] = divide_distance(meshRange["dx"], factor)
            meshRange["dy"] = divide_distance(meshRange["dy"], factor)
        self.setIntervals()
    
    """
    Adiciona informações da região da malha
    """

    def addRange(self, xmin, ymin, xmax, ymax, dxAux, dyAux):
        if len(self.ranges) > 0:
            r = self.ranges[0]
            if xmin > r["xi"]:
                xmin = snap_down_to_grid(xmin, r["xi"], r["dx"])
            elif xmin < r["xi"]:
                xmin = r["xi"]
            if ymin > r["yi"]:
                ymin = snap_down_to_grid(ymin, r["yi"], r["dy"])
            elif ymin < r["yi"]:
                ymin = r["yi"]
            xmax = snap_down_to_grid(xmax, r["xi"], r["dx"])
            ymax = snap_down_to_grid(ymax, r["yi"], r["dy"])
            for i in self.ranges[1:]:
                if i["xi"] <= xmin <= i["xf"] or i["xi"] <= xmax <= i["xf"] or i["yi"] <= ymin <= i["yf"] or i["yi"] <= ymax <= i["yf"]:
                    print("Invalid range: overlap detected")
                    return False
            dxAux = divide_distance(r["dx"], int(dxAux))
            dyAux = divide_distance(r["dy"], int(dyAux))

        nx, xmax = fitted_grid_end(xmin, xmax, dxAux)
        ny, ymax = fitted_grid_end(ymin, ymax, dyAux)
        aux = {
            "nx" : nx,
            "ny" : ny,
            "xi" : xmin,
            "yi" : ymin,
            "xf" : xmax,
            "yf" : ymax,
            "dx" : dxAux,
            "dy" : dyAux
        }

        self.ranges.append(aux)
        return True


    def updateRanges(self, dxAux, dyAux, xmin, ymin):
        originaldx = self.ranges[0]["dx"]
        originaldy = self.ranges[0]["dy"]
        for i in range(len(self.ranges)):
            
            r = self.ranges[i]

            if i == 0:
                r["dx"] = dxAux
                r["dy"] = dyAux
                r["xi"] = xmin
                r["yi"] = ymin
            else:
                auxX = max(1, int(round(originaldx / r["dx"])))
                r["dx"] = divide_distance(dxAux, auxX)
                auxY = max(1, int(round(originaldy / r["dy"])))
                r["dy"] = divide_distance(dyAux, auxY)
                if xmin > r["xi"]:
                    r["xi"] = xmin
                elif xmin < r["xi"]:
                    r["xi"] = snap_down_to_grid(r["xi"], xmin, dxAux)
                if ymin > r["yi"]:
                    r["yi"] = ymin
                elif ymin < r["yi"]:
                    r["yi"] = snap_down_to_grid(r["yi"], ymin, dyAux)

            xminAux = r["xi"]
            yminAux = r["yi"]
            xmax = r["xf"]
            ymax = r["yf"]

            r["nx"], r["xf"] = fitted_grid_end(xminAux, xmax, r["dx"])
            r["ny"], r["yf"] = fitted_grid_end(yminAux, ymax, r["dy"])

            self.ranges[i] = r

            

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
                x = grid_coordinate(r["xi"], r["dx"], i)
                if all([x < a or x > b for a,b in aux]):
                    self.dx.append(x)
            aux.append([r["xi"], r["xf"]])

        yaux = sorted(self.ranges, key = lambda value: value["dy"])
        aux = []
        for r in yaux:
            for i in range(r["ny"]):
                y = grid_coordinate(r["yi"], r["dy"], i)
                if all([y < a or y > b for a,b in aux]):
                    self.dy.append(y)
            aux.append([r["yi"], r["yf"]])
        
        self.dx.sort()
        self.dy.sort()


    def getIndex(item, itens):
        for i in range(len(itens)):
            if values_close(item, itens[i]):
                return i
        return None

    """
    Retorna o valor de x da coordenada do nó da malha onde o ponto informado está 
    """

    def getXNode(self, xpoint):
        for coordinate in self.dx:
            if values_close(xpoint, coordinate):
                return coordinate
        for i in range(len(self.dx) - 1):
            if xpoint >= self.dx[i] and xpoint < self.dx[i + 1]:
                return self.dx[i] 
        print("A figura é maior que os limites da malha")
        quit(1)

    
    """
    Retorna o valor de y da coordenada do nó da malha onde o ponto informado está 
    """
    
    def getYNode(self, ypoint):
        for coordinate in self.dy:
            if values_close(ypoint, coordinate):
                return coordinate
        for i in range(len(self.dy) - 1):
            if ypoint >= self.dy[i] and ypoint < self.dy[i + 1]:
                return self.dy[i] 
        print("A figura é maior que os limites da malha")
        quit(1)

    
    """
    Percore x e y, obtendo os nós da malha para cada ponto com a função getNode, 
    e removendo nós irrelevantes.
    """

    def get_adaptive_mesh(self, x, y, allowDiagonal=True):
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

        xAux = xResult
        yAux = yResult
        xResult = [xAux[0]]
        yResult = [yAux[0]]
        xIndex = SparseMesh.getIndex(xResult[0], self.dx)
        yIndex = SparseMesh.getIndex(yResult[0], self.dy)
        for i in range(1, len(xAux)):
            while True: 
                dxAux = xResult[-1]
                dyAux = yResult[-1]
                if xAux[i] - xResult[-1] > 0:
                    xIndex += 1
                    dxAux = self.dx[xIndex]
                elif xResult[-1] - xAux[i] > 0:
                    xIndex -= 1
                    dxAux = self.dx[xIndex]
                if yAux[i] - yResult[-1] > 0:
                    yIndex += 1
                    dyAux = self.dy[yIndex]
                elif yResult[-1] - yAux[i] > 0:
                    yIndex -= 1
                    dyAux = self.dy[yIndex]
                if dxAux != xResult[-1] or dyAux != yResult[-1]:
                    xResult.append(dxAux)
                    yResult.append(dyAux)
                else:
                    break
        
        if not allowDiagonal:
            xResult, yResult = Mesh.enforceRightAngles(xResult, yResult)

        return xResult, yResult

    """
    Retorna a coordenada do nó da malha onde o ponto informado está 
    """


    def getNode(self, xpoint, ypoint):

        flag = False
        for r in self.ranges[::-1]:
            if r["xi"] <= xpoint <= r["xf"] and r["yi"] <= ypoint <= r["yf"]:
                auxX = snap_down_to_grid(xpoint, r["xi"], r["dx"])
                auxY = snap_down_to_grid(ypoint, r["yi"], r["dy"])
                flag = True
                break
        if flag:
            return[auxX, auxY]
        
        print("A figura é maior que os limites da malha")
        quit(1)

    def getNodeSize(self, xpoint, ypoint):
        dxAux = self.ranges[0]["dx"]
        dyAux = self.ranges[0]["dy"]

        for r in self.ranges[:0:-1]:
            if r["xi"] <= xpoint < r["xf"] and r["yi"] <= ypoint < r["yf"]:
                dxAux = r["dx"]
                dyAux = r["dy"]
                break

        return dxAux, dyAux

    """
    Percore x e y, obtendo os nós da malha irregular para cada ponto com a função getNode, 
    e removendo nós irrelevantes.
    """

    def get_sparse_mesh(self, x, y, allowDiagonal=True):
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
        
        xAux = xResult
        yAux = yResult
        xResult = [xAux[0]]
        yResult = [yAux[0]]
        for i in range(1, len(xAux)):
            dxAux, dyAux = self.getNodeSize(xResult[-1], yResult[-1])
            while True: 
                offsetX = 0
                offsetY = 0
                if xAux[i] - xResult[-1] > dxAux:
                    offsetX = dxAux
                elif xResult[-1] - xAux[i] > dxAux:
                    offsetX = - dxAux
                if yAux[i] - yResult[-1] > dyAux:
                    offsetY = dyAux
                elif yResult[-1] - yAux[i] > dyAux:
                    offsetY = - dyAux
                if offsetX != 0 or offsetY != 0:
                    nextX = grid_coordinate(xResult[-1], abs(offsetX), 1 if offsetX > 0 else -1) if offsetX else xResult[-1]
                    nextY = grid_coordinate(yResult[-1], abs(offsetY), 1 if offsetY > 0 else -1) if offsetY else yResult[-1]
                    xResult.append(nextX)
                    yResult.append(nextY)
                else:
                    break
            xResult.append(xAux[i])
            yResult.append(yAux[i])

        if not allowDiagonal:
            xResult, yResult = Mesh.enforceRightAngles(xResult, yResult)

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


    def export_coords_mesh(path, x, y, toggleOrderingFlag):
        if not toggleOrderingFlag:
            x = x[::-1]
            y = y[::-1]
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
