from shapely.geometry import Point, Polygon

class Mesh:


    """
    Retorna a coordenada do nó da malha onde o ponto informado está 
    """

    def getNode(xpoint, ypoint, xmin, ymin, dx, dy):
       point = []
       point.append((xpoint - xmin)//dx * dx + xmin)
       point.append((ypoint - ymin)//dy * dy + ymin)
       return point


    """
    Percore x e y, obtendo os nós da malha para cada ponto com a função getNode, 
    e removendo nós irrelevantes
    """

    def getMesh(x, y, xmin, ymin, dx, dy):
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
                    xResult.append(xResult[-1] + offsetX)
                    yResult.append(yResult[-1] + offsetY)
                else:
                    break
            xResult.append(xAux[i])
            yResult.append(yAux[i])

        aux = max(xResult)
        if aux != xmax:
            xmax = aux
        nx = round((xmax - xmin)/dx) + 1
        aux = max(yResult)
        if aux != ymax:
            ymax = aux
        ny = round((ymax - ymin)/dy) + 1
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
        area = 0

        x = xarray[::-1]
        y = yarray[::-1]
        for index in range(0, len(x) - 1):
            area += x[index] * y[index + 1] - y[index] * x[index + 1]
        #area += x[index - 1] * y[index] - y[index - 1] * x[index]
        area = area / 2
        return area

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
        point = Point((x,y))
        polygon = Polygon(list(zip(xarray,yarray)))
        return polygon.contains(point) or polygon.intersects(point)
    
    def getIndex(xarray, yarray, x, y):
        for i in range(len(xarray)):
            if x == xarray[i] and y == yarray[i]:
                return i
        return -1 