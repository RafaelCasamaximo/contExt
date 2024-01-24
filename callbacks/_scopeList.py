import random

class Scope:
    _idCounter = 0
    _openIDs   = []
    def __init__(self, lower, upper) -> None:
        self.lower = lower
        self.upper = upper
        self.id = self._getScopeID()
        self.color = (random.randint(0,255),random.randint(0,255),random.randint(0,255),255)
    
    def _getScopeID(self) -> int:
        if (len(Scope._openIDs) == 0):
            Scope._idCounter += 1
            return Scope._idCounter - 1
        else:
            return Scope._openIDs.pop(0)
            
    def __str__(self) -> str:
        return f"({self.lower}, {self.upper})"
    
class ScopeList:
    def __init__(self, startIndex, endIndex) -> None:
        scope = Scope(startIndex, endIndex)
        self.scopes = [scope]
        self.originalScope = scope

    def getScopes(self):
        pairs = []
        for p in self.scopes:
            pairs.append({
                "id":    p.id,
                "color": p.color,
                "lower": p.lower,
                "upper": p.upper
            })
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

    def mergeScopeDeprecated(self, i, j):
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
    
    def mergeScope(self, scopeID_1, scopeID_2):

        # Find Index of scopes
        allIndexesMatches_1 = [i for i, d in enumerate(self.scopes) if d.id == scopeID_1]
        allIndexesMatches_2 = [i for i, d in enumerate(self.scopes) if d.id == scopeID_2]

        # Get first occourence
        scopeIndex_1 = allIndexesMatches_1[0]
        scopeIndex_2 = allIndexesMatches_2[0]

        if (scopeIndex_1 < scopeIndex_2):
            scope_2 = self.scopes.pop(scopeIndex_2)
            scope_1 = self.scopes.pop(scopeIndex_1)

            Scope._openIDs.append(scope_2.id)
            Scope._openIDs.append(scope_1.id)

            self.scopes.append(Scope(scope_1.lower, scope_2.upper))
        else:
            scope_1 = self.scopes.pop(scopeIndex_1)
            scope_2 = self.scopes.pop(scopeIndex_2)

            Scope._openIDs.append(scope_1.id)
            Scope._openIDs.append(scope_2.id)

            self.scopes.append(Scope(scope_2.lower, scope_1.upper))
        






    def resetScopeList(self):
        for sc in self.scopes:
            Scope._openIDs.append(sc.id)
        self.scopes = [self.originalScope]