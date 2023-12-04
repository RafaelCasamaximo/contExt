class Scope:
    def __init__(self, lower, upper) -> None:
        self.lower = lower
        self.upper = upper
    def __str__(self) -> str:
        return f"({self.lower}, {self.upper})"
class ScopeList:
    def __init__(self, startIndex, endIndex) -> None:
        scope = Scope(startIndex, endIndex)
        self.scopes = [scope]

    def getScopes(self):
        pairs = []
        for p in self.scopes:
            pairs.append((p.lower, p.upper))
        return pairs
    def getSize(self) -> int:
        return len(self.scopes)
    
    def createScope(self, a, b):
        i = 0
        while (not (self.scopes[i].lower <= a and b <= self.scopes[i].upper)):
            # print(self.scopes[i])
            i = i + 1
        # index i contains de Greater scope
        # Converts in 3 new scopes:
        #   [scopes[i].lower, a) U [a,b) U [b, scopes[i].upper)
        lowerScope = Scope(self.scopes[i].lower, a)
        midScope   = Scope(a, b)
        upperScope = Scope(b, self.scopes[i].upper)
        
        self.scopes.pop(i)
        if (upperScope.upper - upperScope.lower > 0):
            self.scopes.insert(i, upperScope)
        self.scopes.insert(i, midScope)
        if (lowerScope.upper - lowerScope.lower > 0):
            self.scopes.insert(i, lowerScope)

    def mergeScope(self, i, j):
            if (self.getSize() > 1              and
                (0 <= i and i < self.getSize()) and
                (0 <= j and j < self.getSize())):

                if (j == i+1):
                    self.scopes[i].upper = self.scopes[i+1].upper
                    self.scopes.pop(i+1)
                else:
                    if (j == i-1):
                        self.scopes[i].lower = self.scopes[i-1].lower
                        self.scopes.pop(i-1)