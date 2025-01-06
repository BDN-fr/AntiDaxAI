from main import decisions_amount, getCoordsAfterMove

def isPosValid(pos, colors, bonusAreas, img):
    color = img.getpixel(pos)  # Get the color of the pixel
    for i in range(len(colors)):
        red_diff = abs(color[0] - colors[i][0])
        green_diff = abs(color[1] - colors[i][1])
        blue_diff = abs(color[2] - colors[i][2])
        if red_diff < 10 and green_diff < 10 and blue_diff < 10:
            return True
    for area in bonusAreas:
        if pos[0] in range(area[0], area[2]) and pos[1] in range(area[1], area[3]):
            return True
    return False

def isPosInAnyArea(pos, areas):
    return any(area[0] <= pos[0] < area[2] and area[1] <= pos[1] < area[3] for area in areas)

def isPosSafeAndValid(pos, nonSafeAreas, colors, bonusAreas, img):
    validPos = isPosValid(pos, colors, bonusAreas, img)
    safePos = not isPosInAnyArea(pos, nonSafeAreas)
    return validPos and safePos

def FindPaths(pos, nonSafeAreas, bonusAreas, moveDiff, colors, img, max_length):
    computedPaths = {}
    safePaths = {}
    fullSafePaths = {}
    bonusPaths = {}

    computedPaths[pos] = []
    if not isPosInAnyArea(pos, nonSafeAreas):
        safePaths[pos] = []
        fullSafePaths[pos] = []

    for length in range(1, max_length+1):
        new_computedPaths = {}
        for coords in computedPaths.keys():
            for direction in sorted(decisions_amount.keys(), key=decisions_amount.get):
                new_pos = getCoordsAfterMove(coords, direction, moveDiff)
                oldPathSafe = fullSafePaths.get(coords) and True or False

                if not (new_pos in computedPaths) and not (new_pos in new_computedPaths):
                    if isPosValid(new_pos, colors, bonusAreas, img):
                        new_computedPaths[new_pos] = computedPaths[coords] + [direction]
                        if not isPosInAnyArea(new_pos, nonSafeAreas):
                            safePaths[new_pos] = new_computedPaths[new_pos]
                            if length == 1 or oldPathSafe:
                                fullSafePaths[new_pos] = new_computedPaths[new_pos]
                else:
                    if oldPathSafe and not (new_pos in fullSafePaths) and not isPosInAnyArea(new_pos, nonSafeAreas):
                        fullSafePaths[new_pos] = fullSafePaths[coords] + [direction]

        computedPaths.update(new_computedPaths)

    for coords in fullSafePaths.keys():
        for bonusArea in bonusAreas:
            if bonusArea[0] <= coords[0] < bonusArea[2] and bonusArea[1] <= coords[1] < bonusArea[3]:
                bonusPaths[coords] = fullSafePaths[coords]

    return fullSafePaths, safePaths, bonusPaths, computedPaths


def calcPath(pos, nonSafeAreas, bonusAreas, moveDiff, colors, img, max_length=10):
    if len(bonusAreas) == 0 and not isPosInAnyArea(pos, nonSafeAreas):
        return [], {}

    fullSafePaths, safePaths, bonusPaths, computedPaths = FindPaths(pos, nonSafeAreas, bonusAreas, moveDiff, colors, img, max_length)

    if len(bonusPaths) > 0:
        sorted_bonusPaths = sorted(bonusPaths.keys(), key=lambda x: len(bonusPaths[x]))
        return bonusPaths[sorted_bonusPaths[0]], computedPaths
    if len(fullSafePaths) > 0:
        sorted_fullSafePaths = sorted(fullSafePaths.keys(), key=lambda x: len(fullSafePaths[x]))
        return fullSafePaths[sorted_fullSafePaths[0]], computedPaths
    if len(safePaths) > 0:
        sorted_safePaths = sorted(safePaths.keys(), key=lambda x: len(safePaths[x]))
        return safePaths[sorted_safePaths[0]], computedPaths
    return [], computedPaths