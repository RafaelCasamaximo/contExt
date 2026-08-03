from math import fsum

from shapely.geometry import Point, Polygon

from ._numeric import divide_distance, grid_coordinate, grid_count, interpolate_value, snap_down_to_grid, values_close

class Mesh:

    @staticmethod
    def enforceRightAngles(x, y):
        """Insert grid corners so every contour segment is axis-aligned."""
        if len(x) != len(y):
            raise ValueError("x and y must contain the same number of coordinates")
        if not x:
            return [], []

        xResult = [x[0]]
        yResult = [y[0]]

        for xPoint, yPoint in zip(x[1:], y[1:]):
            previousX = xResult[-1]
            previousY = yResult[-1]

            if not values_close(xPoint, previousX) and not values_close(yPoint, previousY):
                # Move along X first, then Y. Both legs remain on grid lines.
                xResult.append(xPoint)
                yResult.append(previousY)

            if not values_close(xPoint, xResult[-1]) or not values_close(yPoint, yResult[-1]):
                xResult.append(xPoint)
                yResult.append(yPoint)

        return xResult, yResult

    @staticmethod
    def spacingFromDistance(distance, xParts, yParts):
        """Convert a reference distance and axis divisions to dx and dy."""
        if distance <= 0:
            raise ValueError("distance must be greater than zero")
        if xParts < 1 or yParts < 1:
            raise ValueError("axis divisions must be at least one")
        return divide_distance(distance, xParts), divide_distance(distance, yParts)

    @staticmethod
    def subdivisionFactor(levels):
        if not isinstance(levels, int) or isinstance(levels, bool) or levels < 1:
            raise ValueError("subdivision levels must be a positive integer")
        return 2 ** levels

    @staticmethod
    def subdividePath(x, y, levels):
        """Bisect every path segment while retaining every original point."""
        if len(x) != len(y):
            raise ValueError("x and y must contain the same number of coordinates")
        if not x:
            return [], [], []

        factor = Mesh.subdivisionFactor(levels)
        xResult = [x[0]]
        yResult = [y[0]]
        originalIndexMap = [0]

        for index in range(1, len(x)):
            startX = x[index - 1]
            startY = y[index - 1]
            endX = x[index]
            endY = y[index]

            if not values_close(startX, endX) or not values_close(startY, endY):
                for subdivision in range(1, factor):
                    xResult.append(interpolate_value(startX, endX, subdivision, factor))
                    yResult.append(interpolate_value(startY, endY, subdivision, factor))

            # Keep the original value itself, rather than a recomputed endpoint.
            xResult.append(endX)
            yResult.append(endY)
            originalIndexMap.append(len(xResult) - 1)

        return xResult, yResult, originalIndexMap

    @staticmethod
    def subdivideUniformMeshInfo(meshInfo, levels):
        factor = Mesh.subdivisionFactor(levels)
        required = ("nx", "ny", "xmin", "ymin", "dx", "dy")
        if any(meshInfo.get(key) is None for key in required):
            raise ValueError("mesh metadata is incomplete")

        result = dict(meshInfo)
        result["nx"] = (int(meshInfo["nx"]) - 1) * factor + 1
        result["ny"] = (int(meshInfo["ny"]) - 1) * factor + 1
        result["dx"] = divide_distance(meshInfo["dx"], factor)
        result["dy"] = divide_distance(meshInfo["dy"], factor)
        return result


    """
    Retorna a coordenada do nó da malha onde o ponto informado está 
    """

    def getNode(xpoint, ypoint, xmin, ymin, dx, dy):
       return [
           snap_down_to_grid(xpoint, xmin, dx),
           snap_down_to_grid(ypoint, ymin, dy),
       ]


    """
    Percore x e y, obtendo os nós da malha para cada ponto com a função getNode, 
    e removendo nós irrelevantes
    """

    def getMesh(x, y, xmin, ymin, dx, dy, allowDiagonal=True):
        xResult = []
        yResult = []
        xmax = max(x)
        ymax = max(y)
        prevpoint = Mesh.getNode(x[0], y[0], xmin, ymin, dx, dy) 
        xResult.append(prevpoint[0])
        yResult.append(prevpoint[1])
        flagx = 0
        flagy = 0
        dirx = prevpoint[0] > x[-2]
        diry = prevpoint[1] > y[-2]
        tam = len(x)
        for i in range(1,tam):
            point = Mesh.getNode(x[i], y[i], xmin, ymin, dx, dy)
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
        if point[0] != prevpoint[0] or point[1] != prevpoint[1]:
            xResult.append(point[0])
            yResult.append(point[1])

        xAux = xResult
        yAux = yResult
        xResult = [xAux[0]]
        yResult = [yAux[0]]
        for i in range(1, len(xAux)):
            while True: 
                offsetX = 0
                offsetY = 0
                if xAux[i] - xResult[-1] > dx:
                    offsetX = dx
                elif xResult[-1] - xAux[i] > dx:
                    offsetX = - dx
                if yAux[i] - yResult[-1] > dy:
                    offsetY = dy
                elif yResult[-1] - yAux[i] > dy:
                    offsetY = - dy
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

        aux = max(xResult)
        if aux != xmax:
            xmax = aux
        nx = grid_count(xmin, xmax, dx)
        aux = max(yResult)
        if aux != ymax:
            ymax = aux
        ny = grid_count(ymin, ymax, dy)
        xResult = [nx, xmin, xmax, dx] + xResult
        yResult = [ny, ymin, ymax, dy] + yResult
        return xResult, yResult
        
    

    """
    Essa função é utilizada para converter o array das coordenadas em uma string para ser impressa no arquivo de texto. Retorna a string.
    """

    def converte_pointArray_to_string(x,y):
        content = ''
        i = 0
        while i < len(x):
            content = content + str(x[i]) + " " + str(y[i]) + "\n"
            i += 1
        return content


    """
    Função responsável por exportar as coordenadas dos nós da malha em um arquivo path
    """

    def export_coords_mesh(path, x, y, nx, ny, xmin, ymin, xmax, ymax, dx, dy, toggleOrderingFlag):
        if not toggleOrderingFlag:
            x = x[::-1]
            y = y[::-1]
        content = ''
        content = content + str(nx) + " " + str(ny) + "\n"
        content = content + str(xmin) + " " + str(ymin) + "\n"
        content = content + str(xmax) + " " + str(ymax) + "\n"
        content = content + str(dx) + " " + str(dy) + "\n"
        try:
            with open(path, "w") as dataFile:
                content += Mesh.converte_pointArray_to_string(x,y)
                dataFile.write(content)
        except:
            print('Path does not exist for mesh export')
            return


    """
    Utiliza um método descrito por Gauss para o cálculo da área de um poligono irregular convexo
    Utiliza como base: https://www.thecivilengineer.org/education/calculation-examples/item/1319-calculation-example-three-point-resection
    Para esse algoritmo funcionar ele precisa de uma lista ordenada de pontos. No caso, a própria lista de pontos que foi adquirida a partir da extração de contorno
    """

    def get_area(xarray,yarray):
        x = xarray[::-1]
        y = yarray[::-1]
        terms = [
            x[index] * y[index + 1] - y[index] * x[index + 1]
            for index in range(0, len(x) - 1)
        ]
        return fsum(terms) / 2

    def convert_matlab(y, ymax):
        yarray = []
        for i in range(len(y)):
            yarray.append(ymax - y[i])
        return yarray

    def change_scale(x, y, xmax, ymax, width, height, startXOffset, startYOffset):
        widthCoef = width / xmax
        heightCoef = height / ymax
        
        for i in range(len(y)):
            if width > 0:
                x[i] = x[i] * widthCoef
            x[i] = x[i] + startXOffset
            if height > 0:
                y[i] = y[i] * heightCoef
            y[i] = y[i] + startYOffset

        return x, y

    def insidePolygon(xarray, yarray, x, y):
        if len(xarray) != len(yarray) or len(xarray) < 4:
            return False
        point = Point((x,y))
        try:
            polygon = Polygon(list(zip(xarray,yarray)))
        except ValueError:
            return False
        if polygon.is_empty:
            return False
        return polygon.contains(point) or polygon.intersects(point)
    
    def getIndex(xarray, yarray, x, y):
        for i in range(len(xarray)):
            if values_close(x, xarray[i]) and values_close(y, yarray[i]):
                return i
        return -1
