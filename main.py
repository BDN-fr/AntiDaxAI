import brain
import time
import os
import ctypes
from PIL import Image, ImageDraw, ImageFont, ImageChops
import shutil

import numpy as np
import pyautogui as pg
import cv2

def GetWindowHWND(name:str):
    return ctypes.windll.user32.FindWindowW(0, name)

def GetWindowRegion(hwnd:int)-> tuple:
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.pointer(rect))
    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

###

hwnd = GetWindowHWND('Bluestacks App Player')
if hwnd:
    screen_region = GetWindowRegion(hwnd)
else:
    raise Exception("Window not found: 'Bluestacks App Player'")

###

def match_template_multi_scale(screenshot, template, threshold, scales=[0.4, 0.6, 0.8, 1, 1.2]):
    results = []
    for scale in scales:
        resized_template = cv2.resize(template, (0, 0), fx=scale, fy=scale)
        res = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            results.append((pt[0], pt[1], resized_template.shape[1], resized_template.shape[0]))
    return results

def getScreenState():
    return pg.screenshot('screenshot.png', region=screen_region)

def getCoordsAfterMove(pos, direction, moveDiff):
    if direction == 'left':
        new_pos = (pos[0] - moveDiff, pos[1])
    elif direction == 'right':
        new_pos = (pos[0] + moveDiff, pos[1])
    elif direction == 'up':
        new_pos = (pos[0], pos[1] - moveDiff)
    elif direction == 'down':
        new_pos = (pos[0], pos[1] + moveDiff)
    return new_pos

#############

decisions = ['left', 'right', 'up', 'down']
decisions_coords = {
    'left': None,
    'right': None,
    'up': None,
    'down': None
}
decisions_amount = {
    'left': 0,
    'right': 0,
    'up': 0,
    'down': 0
}

wait_time = 0.01

play_button_coords = pg.Point(screen_region[0] + screen_region[2]/2, screen_region[1] + screen_region[3]/2 + screen_region[3]*0.1)
pause_coords = pg.Point(screen_region[0] + screen_region[2]*0.07, screen_region[1] + screen_region[3]*0.07)
continue_coords = None
continue_region = None
close_coords = None

playerSize = None
moveDiff = None
moveDiffCoeff = None
colors = []

class Game:
    def __init__(self):
        print('Collection des coordonnées des boutons...')
        pg.click(play_button_coords)
        time.sleep(1)
        global decisions, decisions_coords
        for v in decisions:
            while decisions_coords[v] == None:
                try:
                    decisions_coords[v] = pg.locateCenterOnScreen(f'img/{v}.png', grayscale=True, region=screen_region)
                except pg.ImageNotFoundException:
                    print(f'Not found {v}.png')
        
        time.sleep(0.5)
        player = pg.locateOnScreen(f'img/player.png', region=screen_region, confidence=0.6)
        coords = pg.center(player)
        self.move(['right'], False)
        time.sleep(0.2)
        coords2 = pg.locateCenterOnScreen(f'img/player.png', region=screen_region, confidence=0.6)
        global moveDiff, moveDiffCoeff
        moveDiff = coords2[0] - coords[0]
        print('Différence de déplacement:', moveDiff)
        moveDiffCoeff = moveDiff / player.width
        global colors
        self.move(['up'], False)
        time.sleep(0.1)
        colors.append(pg.pixel(int(coords.x), int(coords.y-moveDiff)))
        colors.append(pg.pixel(int(coords.x-moveDiff), int(coords.y-moveDiff)))
        print('Couleurs:', colors)

        pg.click(pause_coords)
        time.sleep(0.1)
        global continue_coords, continue_region
        continue_region = pg.locateOnScreen(f'img/continue.png', grayscale=True, region=screen_region)
        continue_coords = pg.center(continue_region)
        continue_region = (
            int(continue_region[0] - screen_region[0]),
            int(continue_region[1] - screen_region[1]),
            int(continue_region[0] - screen_region[0] + continue_region[2]),
            int(continue_region[1] - screen_region[1] + continue_region[3])
        )
        pg.click(continue_coords)

        print('Attente de la fin de partie...')
        while True:
            try:
                global close_coords
                close_coords = pg.locateCenterOnScreen('img/close.png', grayscale=True, region=screen_region)
                pg.click(close_coords)
                time.sleep(0.5)
                break
            except pg.ImageNotFoundException:
                time.sleep(0.2)
                pass
        
        print('Oppérationnel')

    def move(self, actions, count=True):
        for d in actions:
            pg.click(decisions_coords[d])
            if count:
                decisions_amount[d] += 1
    
    def pause(self):
        pg.click(pause_coords)
    
    def resume(self):
        pg.click(continue_coords)

    def close(self):
        pg.click(close_coords)

    def start(self):
        pg.click(play_button_coords)
        time.sleep(1)

    def is_dead(self):
        try:
            pg.locateCenterOnScreen('img/close.png', grayscale=True, region=screen_region, confidence=0.8)
            return True
        except:
            return False
    
    def findGuns(self):
        guns = []
        try:
            screenshot = cv2.imread('screenshot.png', cv2.IMREAD_COLOR)
            template = cv2.imread('img/gun.png', cv2.IMREAD_COLOR)

            threshold = 0.87
            guns.extend(match_template_multi_scale(screenshot, template, threshold))
            guns.extend(match_template_multi_scale(screenshot, cv2.rotate(template, cv2.ROTATE_90_CLOCKWISE), threshold))
            guns.extend(match_template_multi_scale(screenshot, cv2.rotate(template, cv2.ROTATE_180), threshold))
            guns.extend(match_template_multi_scale(screenshot, cv2.rotate(template, cv2.ROTATE_90_COUNTERCLOCKWISE), threshold))
        except:
            pass
        return guns

    def findObjects(self):
        objects = []
        screenshot = cv2.imread('screenshot.png', cv2.IMREAD_COLOR)
        template_box = cv2.imread('img/box.png', cv2.IMREAD_COLOR)
        template_wall = cv2.imread('img/wall.png', cv2.IMREAD_COLOR)
        objects.extend(match_template_multi_scale(screenshot, template_box, 0.9))
        objects.extend(match_template_multi_scale(screenshot, template_wall, 0.7))
        return objects

    def findCoins(self):
        objects = []
        screenshot = cv2.imread('screenshot.png', cv2.IMREAD_COLOR)
        template_coin = cv2.imread('img/coin.png', cv2.IMREAD_COLOR)
        template_shield = cv2.imread('img/shield.png', cv2.IMREAD_COLOR)
        objects.extend(match_template_multi_scale(screenshot, template_coin, 0.9))
        objects.extend(match_template_multi_scale(screenshot, template_shield, 0.8))
        for obj in objects:
            if obj[0] < screen_region[0]*0.1:
                objects.remove(obj)
        return objects

    def findPlayer(self):
        player_image = cv2.imread('img/player.png', cv2.IMREAD_COLOR)
        screenshot = cv2.imread('screenshot.png', cv2.IMREAD_COLOR)

        locations = match_template_multi_scale(screenshot, player_image, 0.8)
        if locations:
            return locations[0]
        else:
            return None
    
    def computeFrame(self, img, predicted_pos):
        global moveDiff, moveDiffCoeff
        draw = ImageDraw.Draw(img)

        guns = self.findGuns()
        coins = self.findCoins()
        objects = self.findObjects()
        player = self.findPlayer()

        if not player:
            # print('Player not found')
            draw.font = ImageFont.load_default()
            draw.text((screen_region[2]*0.12, screen_region[3]*0.12), 'Player not found', fill='red')

        bonusAreas = []
        for box in coins:
            bonusAreas.append((box[0], box[1], box[0] + box[2], box[1] + box[3]))
        
        nonSafeAreas = []
        for box in guns:
            nonSafeAreas.append((0, box[1], screen_region[2], box[1] + box[3]))
            nonSafeAreas.append((box[0], 0, box[0] + box[2], screen_region[3]))

        for box in bonusAreas:
            draw.rectangle([(box[0], box[1]), (box[2], box[3])], fill='yellow')
        
        for box in nonSafeAreas:
            draw.rectangle([(box[0], box[1]), (box[2], box[3])], outline='red')
        
        for box in objects:
            draw.rectangle(
                [(box[0], box[1]), (box[0] + box[2], box[1] + box[3])],
                fill='blue'
            )
        
        if player:
            pos = pg.center(player)
            moveDiff = player[2] * moveDiffCoeff
            draw.rectangle(
                [(player[0], player[1]), (player[0] + player[2], player[1] + player[3])],
                fill='magenta'
            )
        else:
            pos = predicted_pos

        path, computedPaths = brain.calcPath(pos, nonSafeAreas, bonusAreas, moveDiff, colors, Image.open('screenshot.png'))

        for end_pos in computedPaths:
            draw_pos = pos
            for direction in computedPaths[end_pos]:
                new_pos = getCoordsAfterMove(draw_pos, direction, moveDiff)
                draw.line([draw_pos, new_pos], fill='green', width=3)
                draw_pos = new_pos

                if brain.isPosInAnyArea(draw_pos, nonSafeAreas):
                    color = 'red'
                else:
                    color = 'lime'
                draw.rectangle(
                    [(draw_pos[0] - 5, draw_pos[1] - 5), (draw_pos[0] + 5, draw_pos[1] + 5)],
                    fill=color
                )
        
        if path != None and len(path) > 0:
            # print('Moving:', path)
            draw_pos = pos
            for d in path:
                new_pos = getCoordsAfterMove(draw_pos, d, moveDiff)
                draw.line([draw_pos, new_pos], fill='blue', width=5)
                draw_pos = new_pos
            pos = draw_pos
            self.resume()
            self.move(path)
            self.pause()
        
        return pos
    
    def loop(self):
        i = 0
        predicted_pos = None
        while True:
            i+=1
            # print(f'Start computing frame {i}')
            if self.is_dead():
                quit()
            self.resume()
            while True:
                getScreenState()
                thresh = 45
                fn = lambda x : 255 if x > thresh else 0
                continue_image = Image.open('img/continue.png').convert('L').point(fn, mode='1')
                screenshot_crop = Image.open('screenshot.png').crop(continue_region).convert('L').point(fn, mode='1')
                diff = ImageChops.difference(continue_image, screenshot_crop)
                if diff.getbbox() is None:
                    continue
                else:
                    break
            self.pause()

            img = Image.open('screenshot.png')

            predicted_pos = self.computeFrame(img, predicted_pos)

            # print('Saving frame', i)
            img.save(f'ai-vision/frame-{i}.png')
            img.save('vision.png')

if __name__ == '__main__':
    os.system('title AntiDaxAI')
    os.system('cls')
    shutil.rmtree('ai-vision', ignore_errors=True)
    os.mkdir('ai-vision')
    time.sleep(1)

    game = Game()
    game.start()
    time.sleep(0.5)
    game.loop()