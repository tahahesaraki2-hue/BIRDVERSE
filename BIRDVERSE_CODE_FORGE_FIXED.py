#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FLAPPY BIRD X
Single-file Flappy Bird-style game made with Pygame.
No external assets are required.

Install:
    pip install pygame

Run:
    python flappy_bird.py

Controls:
    SPACE / UP / Mouse click / Touch-like mouse press = flap
    ESC = quit
    P = pause
    R = restart after game over
    M = mute/unmute

Everything is contained in this one .py file.
"""

import pygame
import random
import math
import json
import os
import time

# ============================================================
# CONFIG
# ============================================================

WIDTH = 480
HEIGHT = 800
FPS = 60
GROUND_H = 105
GROUND_Y = HEIGHT - GROUND_H

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".flappy_bird_x_save.json")

pygame.init()
pygame.mixer.init()

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Flappy Bird X")
CLOCK = pygame.time.Clock()

FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 26)
BIG_FONT = pygame.font.Font(None, 72)
HUGE_FONT = pygame.font.Font(None, 96)

# ============================================================
# COLORS
# ============================================================

WHITE = (255, 255, 255)
BLACK = (15, 18, 25)
DARK = (24, 29, 42)
GRAY = (120, 130, 145)
LIGHT_GRAY = (205, 215, 225)
GREEN = (70, 205, 100)
DARK_GREEN = (35, 135, 70)
YELLOW = (255, 220, 70)
ORANGE = (255, 155, 45)
RED = (235, 70, 80)
BLUE = (75, 170, 255)
CYAN = (70, 235, 235)
PURPLE = (170, 105, 245)
PINK = (245, 105, 180)

# ============================================================
# UTILITY
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def text(surface, message, font, color, x, y, center=True):
    img = font.render(str(message), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    surface.blit(img, rect)
    return rect


def rounded_rect(surface, color, rect, radius=14, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


# ============================================================
# SAVE SYSTEM
# ============================================================

DEFAULT_SAVE = {
    "coins": 0,
    "best": 0,
    "level": 1,
    "xp": 0,
    "games": 0,
    "total_score": 0,
    "total_coins": 0,
    "flaps": 0,
    "muted": False,
    "selected_skin": 0,
    "selected_theme": 0,
    "skins": [0],
    "themes": [0],
    "achievements": [],
    "missions": {
        "score_10": 0,
        "coins_25": 0,
        "games_10": 0,
        "score_25": 0,
    },
}


def load_save():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = DEFAULT_SAVE.copy()
            result.update(data)
            if not isinstance(result.get("skins"), list):
                result["skins"] = [0]
            if not isinstance(result.get("themes"), list):
                result["themes"] = [0]
            if not isinstance(result.get("achievements"), list):
                result["achievements"] = []
            if not isinstance(result.get("missions"), dict):
                result["missions"] = DEFAULT_SAVE["missions"].copy()
            return result
    except Exception:
        pass
    return json.loads(json.dumps(DEFAULT_SAVE))


def save_game(data):
    try:
        temp = SAVE_FILE + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp, SAVE_FILE)
    except Exception:
        pass


DATA = load_save()

# ============================================================
# PROCEDURAL SOUND
# ============================================================

# The game works even when the audio mixer is unavailable.
AUDIO_OK = True


def make_beep(freq=500, duration=0.06, volume=0.18):
    """Create a tiny procedural sound without an external asset."""
    if not AUDIO_OK:
        return None
    try:
        sample_rate = 22050
        count = int(sample_rate * duration)
        buf = bytearray()
        for i in range(count):
            t = i / sample_rate
            fade = min(1.0, i / max(1, count * 0.08),
                       (count - i) / max(1, count * 0.12))
            value = int(127 * math.sin(2 * math.pi * freq * t) * volume * fade)
            buf.extend((128 + value, 128 + value))
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None


SND_FLAP = make_beep(760, 0.055, 0.28)
SND_POINT = make_beep(1050, 0.08, 0.25)
SND_COIN = make_beep(1300, 0.055, 0.22)
SND_HIT = make_beep(120, 0.16, 0.30)
SND_POWER = make_beep(520, 0.18, 0.25)


def play_sound(sound):
    if sound and not DATA.get("muted", False):
        try:
            sound.play()
        except Exception:
            pass

# ============================================================
# SKINS / THEMES / SHOP
# ============================================================

SKINS = [
    {"name": "Classic", "price": 0, "body": YELLOW, "wing": ORANGE},
    {"name": "Ruby", "price": 60, "body": RED, "wing": (255, 190, 190)},
    {"name": "Ocean", "price": 100, "body": BLUE, "wing": CYAN},
    {"name": "Royal", "price": 150, "body": PURPLE, "wing": (225, 190, 255)},
    {"name": "Candy", "price": 220, "body": PINK, "wing": (255, 220, 240)},
    {"name": "Emerald", "price": 300, "body": GREEN, "wing": (185, 255, 195)},
]

THEMES = [
    {"name": "Day", "price": 0, "sky": (105, 190, 250), "cloud": (245, 250, 255)},
    {"name": "Sunset", "price": 120, "sky": (235, 125, 105), "cloud": (255, 215, 175)},
    {"name": "Night", "price": 180, "sky": (35, 45, 90), "cloud": (95, 105, 150)},
    {"name": "Space", "price": 350, "sky": (12, 12, 35), "cloud": (70, 70, 120)},
]

POWERUPS = [
    "shield",
    "coin",
    "slow",
]

ACHIEVEMENTS = [
    ("first_flight", "First Flight", "Play your first game"),
    ("score_10", "Getting Good", "Reach 10 points"),
    ("score_25", "Pro Flyer", "Reach 25 points"),
    ("score_50", "Sky Legend", "Reach 50 points"),
    ("coins_100", "Coin Hunter", "Collect 100 coins total"),
    ("games_10", "Regular", "Play 10 games"),
]


def achievement_unlocked(key):
    return key in DATA["achievements"]


def unlock(key):
    if not achievement_unlocked(key):
        DATA["achievements"].append(key)
        save_game(DATA)
        return True
    return False


# ============================================================
# PARTICLES
# ============================================================

class Particle:
    def __init__(self, x, y, color, size=4, life=0.6, vx=None, vy=None):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(1.5, size)
        self.life = life
        self.max_life = life
        self.vx = random.uniform(-80, 80) if vx is None else vx
        self.vy = random.uniform(-100, 30) if vy is None else vy
        self.gravity = 130

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.size *= 0.992
        return self.life > 0

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = clamp(self.life / self.max_life, 0, 1)
        r = max(1, int(self.size * alpha))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)


class ParticleSystem:
    def __init__(self):
        self.items = []

    def burst(self, x, y, color, amount=14):
        for _ in range(amount):
            self.items.append(Particle(x, y, color))

    def trail(self, x, y, color):
        self.items.append(
            Particle(
                x, y, color, size=3, life=0.3,
                vx=random.uniform(-35, 0),
                vy=random.uniform(-15, 15)
            )
        )

    def update(self, dt):
        self.items = [p for p in self.items if p.update(dt)]

    def draw(self, surface):
        for p in self.items:
            p.draw(surface)

# ============================================================
# CLOUDS / STARS
# ============================================================

class Cloud:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(60, 330)
        self.speed = random.uniform(12, 30)
        self.scale = random.uniform(0.65, 1.4)

    def update(self, dt):
        self.x -= self.speed * dt
        if self.x < -120 * self.scale:
            self.x = WIDTH + random.randint(20, 160)
            self.y = random.randint(50, 320)

    def draw(self, surface, color):
        s = self.scale
        x, y = int(self.x), int(self.y)
        pygame.draw.ellipse(surface, color,
                            (x, y + int(10*s), int(95*s), int(34*s)))
        pygame.draw.circle(surface, color,
                           (x + int(30*s), y + int(14*s)), int(23*s))
        pygame.draw.circle(surface, color,
                           (x + int(55*s), y), int(31*s))
        pygame.draw.circle(surface, color,
                           (x + int(78*s), y + int(15*s)), int(22*s))


class Star:
    def __init__(self):
        self.x = random.randrange(WIDTH)
        self.y = random.randrange(20, GROUND_Y - 100)
        self.radius = random.choice([1, 1, 1, 2])
        self.twinkle = random.random() * 6.28

    def draw(self, surface):
        a = 0.45 + 0.55 * ((math.sin(self.twinkle + time.time() * 2) + 1) / 2)
        c = int(150 + 105 * a)
        pygame.draw.circle(surface, (c, c, min(255, c + 15)),
                           (self.x, self.y), self.radius)

# ============================================================
# PLAYER
# ============================================================

class Bird:
    def __init__(self):
        self.x = 120
        self.y = HEIGHT * 0.43
        self.vel = 0
        self.angle = 0
        self.radius = 20
        self.wing_phase = 0
        self.alive = True
        self.shield = False
        self.shield_time = 0
        self.invincible = 0
        self.flap_count = 0

    def flap(self):
        if not self.alive:
            return
        self.vel = -390
        self.angle = 28
        self.wing_phase += 1
        self.flap_count += 1
        DATA["flaps"] += 1
        play_sound(SND_FLAP)

    def update(self, dt):
        self.vel += 980 * dt
        self.vel = min(self.vel, 620)
        self.y += self.vel * dt
        self.angle -= 85 * dt
        self.angle = clamp(self.angle, -90, 30)
        self.wing_phase += dt * 12

        if self.shield_time > 0:
            self.shield_time -= dt
            if self.shield_time <= 0:
                self.shield = False

        if self.invincible > 0:
            self.invincible -= dt

    def hitbox(self):
        return pygame.Rect(
            int(self.x - self.radius + 4),
            int(self.y - self.radius + 4),
            self.radius * 2 - 8,
            self.radius * 2 - 8
        )

    def draw(self, surface):
        skin = SKINS[DATA["selected_skin"]]
        temp = pygame.Surface((90, 90), pygame.SRCALPHA)
        cx, cy = 45, 45

        # tail
        pygame.draw.polygon(
            temp, skin["wing"],
            [(18, 43), (5, 30), (12, 49), (5, 62), (25, 54)]
        )

        # wing animation
        wing_y = 50 + int(math.sin(self.wing_phase) * 7)
        pygame.draw.ellipse(temp, skin["wing"], (25, wing_y - 7, 27, 20))

        # body
        pygame.draw.ellipse(temp, skin["body"], (20, 20, 52, 42))
        pygame.draw.ellipse(temp, (255, 245, 220), (51, 29, 22, 22))

        # eye
        pygame.draw.circle(temp, WHITE, (57, 28), 7)
        pygame.draw.circle(temp, BLACK, (59, 28), 3)

        # beak
        pygame.draw.polygon(
            temp, ORANGE,
            [(68, 39), (84, 44), (68, 49)]
        )

        # small shine
        pygame.draw.circle(temp, WHITE, (34, 29), 3)

        rotated = pygame.transform.rotate(temp, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)

        if self.shield:
            pulse = int(3 * math.sin(time.time() * 8))
            pygame.draw.circle(
                surface, CYAN, (int(self.x), int(self.y)),
                self.radius + 13 + pulse, 3
            )

# ============================================================
# PIPE
# ============================================================

class Pipe:
    WIDTH = 78

    def __init__(self, x, gap_y, gap_size):
        self.x = float(x)
        self.gap_y = gap_y
        self.gap_size = gap_size
        self.passed = False

    @property
    def top_rect(self):
        return pygame.Rect(int(self.x), 0, self.WIDTH, int(self.gap_y - self.gap_size / 2))

    @property
    def bottom_rect(self):
        y = int(self.gap_y + self.gap_size / 2)
        return pygame.Rect(int(self.x), y, self.WIDTH, GROUND_Y - y)

    def update(self, dt, speed):
        self.x -= speed * dt

    def collides(self, bird):
        b = bird.hitbox()
        return b.colliderect(self.top_rect) or b.colliderect(self.bottom_rect)

    def draw(self, surface):
        theme = DATA["selected_theme"]
        pipe_color = GREEN if theme != 3 else (75, 180, 150)
        dark = DARK_GREEN if theme != 3 else (35, 100, 100)

        for rect in (self.top_rect, self.bottom_rect):
            pygame.draw.rect(surface, dark, rect.inflate(5, 0))
            pygame.draw.rect(surface, pipe_color, rect)
            cap = rect.copy()
            cap.height = 25
            if rect.top == 0:
                cap.y = rect.bottom - 25
            pygame.draw.rect(surface, pipe_color, cap)
            pygame.draw.rect(surface, dark, cap, 3)

# ============================================================
# COIN
# ============================================================

class Coin:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 11
        self.collected = False
        self.phase = random.random() * 6.28

    def update(self, dt, speed):
        self.x -= speed * dt
        self.phase += dt * 7

    def rect(self):
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    def draw(self, surface):
        pulse = 1 + 0.10 * math.sin(self.phase)
        r = int(self.radius * pulse)
        pygame.draw.circle(surface, (180, 120, 20),
                           (int(self.x), int(self.y)), r + 3)
        pygame.draw.circle(surface, YELLOW,
                           (int(self.x), int(self.y)), r)
        text(surface, "$", SMALL_FONT, (160, 105, 10),
             self.x, self.y + 1)

# ============================================================
# POWERUP
# ============================================================

class PowerUp:
    def __init__(self, x, y, kind):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.phase = random.random() * 6.28
        self.collected = False

    def update(self, dt, speed):
        self.x -= speed * dt
        self.phase += dt * 5

    def rect(self):
        return pygame.Rect(int(self.x - 16), int(self.y - 16), 32, 32)

    def draw(self, surface):
        colors = {"shield": CYAN, "coin": YELLOW, "slow": PURPLE}
        labels = {"shield": "S", "coin": "2X", "slow": "T"}
        c = colors[self.kind]
        r = int(16 + 3 * math.sin(self.phase))
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), r, 2)
        text(surface, labels[self.kind], SMALL_FONT, BLACK,
             self.x, self.y)

# ============================================================
# GAME
# ============================================================

class Game:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    SHOP = "shop"
    SETTINGS = "settings"
    ACHIEVEMENTS = "achievements"

    def __init__(self):
        self.state = self.MENU
        self.bird = Bird()
        self.pipes = []
        self.coins = []
        self.powerups = []
        self.particles = ParticleSystem()
        self.clouds = [Cloud() for _ in range(7)]
        self.stars = [Star() for _ in range(70)]
        self.score = 0
        self.run_coins = 0
        self.speed = 190
        self.spawn_timer = 0
        self.coin_timer = 0
        self.power_timer = 0
        self.screen_shake = 0
        self.flash = 0
        self.banner = ""
        self.banner_time = 0
        self.menu_bob = 0
        self.last_time = time.time()

    # --------------------------------------------------------
    # State management
    # --------------------------------------------------------

    def start(self):
        self.state = self.PLAYING
        self.bird = Bird()
        self.pipes.clear()
        self.coins.clear()
        self.powerups.clear()
        self.particles.items.clear()
        self.score = 0
        self.run_coins = 0
        self.speed = 190
        self.spawn_timer = 0.8
        self.coin_timer = 0.5
        self.power_timer = random.uniform(5, 9)
        DATA["games"] += 1
        unlock("first_flight")
        save_game(DATA)

    def game_over(self):
        if self.state != self.PLAYING:
            return
        self.state = self.GAME_OVER
        self.bird.alive = False
        self.screen_shake = 10
        self.flash = 0.25
        play_sound(SND_HIT)

        DATA["coins"] += self.run_coins
        DATA["total_coins"] += self.run_coins
        DATA["best"] = max(DATA["best"], self.score)
        DATA["total_score"] += self.score
        DATA["missions"]["score_10"] = max(
            DATA["missions"].get("score_10", 0), self.score
        )
        DATA["missions"]["score_25"] = max(
            DATA["missions"].get("score_25", 0), self.score
        )
        DATA["missions"]["coins_25"] = min(
            25, DATA["missions"].get("coins_25", 0) + self.run_coins
        )
        DATA["missions"]["games_10"] = min(
            10, DATA["games"]
        )

        if self.score >= 10:
            unlock("score_10")
        if self.score >= 25:
            unlock("score_25")
        if self.score >= 50:
            unlock("score_50")
        if DATA["total_coins"] >= 100:
            unlock("coins_100")
        if DATA["games"] >= 10:
            unlock("games_10")

        self.add_xp(self.score * 3 + self.run_coins)
        save_game(DATA)

    def add_xp(self, amount):
        DATA["xp"] += amount
        while DATA["xp"] >= DATA["level"] * 100:
            DATA["xp"] -= DATA["level"] * 100
            DATA["level"] += 1
            DATA["coins"] += 25
            self.banner = "LEVEL UP! +25 COINS"
            self.banner_time = 2.0
        save_game(DATA)

    # --------------------------------------------------------
    # Gameplay
    # --------------------------------------------------------

    def spawn_pipe(self):
        difficulty = min(self.score, 40)
        gap = max(135, 205 - difficulty * 1.5)
        min_y = 170
        max_y = GROUND_Y - 170
        gap_y = random.randint(int(min_y), int(max_y))
        self.pipes.append(Pipe(WIDTH + 40, gap_y, gap))

    def spawn_coin(self):
        if not self.pipes:
            return
        pipe = self.pipes[-1]
        y = pipe.gap_y + random.randint(
            -int(pipe.gap_size / 3), int(pipe.gap_size / 3)
        )
        self.coins.append(Coin(pipe.x + 120, y))

    def spawn_powerup(self):
        if not self.pipes:
            return
        pipe = self.pipes[-1]
        kind = random.choice(POWERUPS)
        y = pipe.gap_y + random.randint(
            -int(pipe.gap_size / 4), int(pipe.gap_size / 4)
        )
        self.powerups.append(PowerUp(pipe.x + 190, y, kind))

    def collect_coin(self, coin):
        if coin.collected:
            return
        coin.collected = True
        self.run_coins += 1
        self.particles.burst(coin.x, coin.y, YELLOW, 12)
        play_sound(SND_COIN)

    def collect_powerup(self, power):
        if power.collected:
            return
        power.collected = True
        if power.kind == "shield":
            self.bird.shield = True
            self.bird.shield_time = 7
        elif power.kind == "coin":
            self.run_coins += 3
        elif power.kind == "slow":
            self.bird.invincible = max(self.bird.invincible, 5)
        self.particles.burst(power.x, power.y, CYAN, 18)
        play_sound(SND_POWER)

    def update_playing(self, dt):
        self.bird.update(dt)

        self.spawn_timer -= dt
        self.coin_timer -= dt
        self.power_timer -= dt

        if self.spawn_timer <= 0:
            self.spawn_pipe()
            self.spawn_timer = max(
                1.05, 1.65 - min(self.score, 30) * 0.012
            )

        if self.coin_timer <= 0:
            self.spawn_coin()
            self.coin_timer = random.uniform(1.0, 2.0)

        if self.power_timer <= 0:
            self.spawn_powerup()
            self.power_timer = random.uniform(8, 13)

        current_speed = self.speed
        if self.bird.invincible > 0:
            current_speed *= 0.72

        self.speed = min(330, 190 + self.score * 2.4)
        for pipe in self.pipes:
            pipe.update(dt, current_speed)
        for coin in self.coins:
            coin.update(dt, current_speed)
        for power in self.powerups:
            power.update(dt, current_speed)

        # Score
        for pipe in self.pipes:
            if not pipe.passed and pipe.x + Pipe.WIDTH < self.bird.x:
                pipe.passed = True
                self.score += 1
                play_sound(SND_POINT)
                self.particles.burst(
                    self.bird.x, self.bird.y, WHITE, 8
                )

        # Collision
        for pipe in self.pipes:
            if pipe.collides(self.bird):
                if self.bird.shield:
                    self.bird.shield = False
                    self.bird.shield_time = 0
                    self.bird.invincible = 1.0
                    self.particles.burst(
                        self.bird.x, self.bird.y, CYAN, 25
                    )
                    self.screen_shake = 7
                elif self.bird.invincible <= 0:
                    self.game_over()
                    return

        if self.bird.y + self.bird.radius >= GROUND_Y:
            if self.bird.invincible <= 0:
                self.bird.y = GROUND_Y - self.bird.radius
                self.game_over()
                return

        if self.bird.y - self.bird.radius <= 0:
            self.bird.y = self.bird.radius
            self.bird.vel = 30

        # Coins
        br = self.bird.hitbox()
        for coin in self.coins:
            if not coin.collected and br.colliderect(coin.rect()):
                self.collect_coin(coin)

        for power in self.powerups:
            if not power.collected and br.colliderect(power.rect()):
                self.collect_powerup(power)

        # Clean up
        self.pipes = [p for p in self.pipes if p.x > -100]
        self.coins = [c for c in self.coins if c.x > -40 and not c.collected]
        self.powerups = [
            p for p in self.powerups if p.x > -50 and not p.collected
        ]

        self.particles.trail(
            self.bird.x - 18, self.bird.y + 5, SKINS[DATA["selected_skin"]]["wing"]
        )
        self.particles.update(dt)

        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - 25 * dt)
        if self.flash > 0:
            self.flash = max(0, self.flash - dt)

    # --------------------------------------------------------
    # Drawing
    # --------------------------------------------------------

    def draw_background(self, surface):
        theme = THEMES[DATA["selected_theme"]]
        surface.fill(theme["sky"])

        if DATA["selected_theme"] == 3:
            for star in self.stars:
                star.draw(surface)
            # planet
            pygame.draw.circle(surface, (70, 70, 120), (390, 130), 65)
            pygame.draw.circle(surface, (105, 105, 165), (370, 110), 20)
        else:
            # sun/moon
            if DATA["selected_theme"] == 2:
                pygame.draw.circle(surface, (225, 225, 190), (390, 105), 43)
            else:
                pygame.draw.circle(surface, (255, 230, 115), (390, 105), 48)

            for cloud in self.clouds:
                cloud.update(1 / FPS)
                cloud.draw(surface, theme["cloud"])

        # distant hills
        hill_color = (
            (20, 30, 70)
            if DATA["selected_theme"] in (2, 3)
            else (100, 190, 130)
        )
        pygame.draw.polygon(
            surface, hill_color,
            [(0, GROUND_Y), (0, 520), (90, 440), (170, 520),
             (250, 420), (340, 520), (430, 450), (WIDTH, 520),
             (WIDTH, GROUND_Y)]
        )

    def draw_ground(self, surface):
        ground = (205, 170, 85)
        if DATA["selected_theme"] == 3:
            ground = (55, 60, 80)
        pygame.draw.rect(surface, ground, (0, GROUND_Y, WIDTH, GROUND_H))
        pygame.draw.rect(surface, (85, 180, 75),
                         (0, GROUND_Y, WIDTH, 12))
        for x in range(-20, WIDTH + 40, 45):
            pygame.draw.rect(
                surface, (175, 140, 70),
                (x, GROUND_Y + 35, 23, 7)
            )

    def draw_game(self, surface):
        self.draw_background(surface)

        for pipe in self.pipes:
            pipe.draw(surface)
        for coin in self.coins:
            coin.draw(surface)
        for power in self.powerups:
            power.draw(surface)

        self.draw_ground(surface)
        self.particles.draw(surface)
        self.bird.draw(surface)

        # Score
        text(surface, self.score, HUGE_FONT, WHITE, WIDTH / 2, 70)
        text(surface, f"🪙 {self.run_coins}", SMALL_FONT,
             WHITE, 62, 38)

        if self.bird.shield:
            text(surface, f"SHIELD {self.bird.shield_time:.1f}",
                 SMALL_FONT, CYAN, WIDTH - 90, 38)

        if self.bird.invincible > 0:
            text(surface, f"SLOW {self.bird.invincible:.1f}",
                 SMALL_FONT, PURPLE, WIDTH - 75, 68)

    def draw_button(self, surface, label, rect, active=False):
        c = (65, 75, 100) if not active else (90, 110, 150)
        rounded_rect(surface, c, rect, 16, 2, LIGHT_GRAY)
        text(surface, label, FONT, WHITE, rect.centerx, rect.centery)

    def draw_menu(self, surface):
        self.draw_background(surface)

        bob = math.sin(self.menu_bob) * 9
        text(surface, "FLAPPY", HUGE_FONT, WHITE, WIDTH/2, 130 + bob)
        text(surface, "BIRD X", HUGE_FONT, YELLOW, WIDTH/2, 205 + bob)

        # Decorative bird
        preview = Bird()
        preview.x = WIDTH / 2
        preview.y = 305 + bob
        preview.angle = 0
        preview.wing_phase = self.menu_bob
        preview.draw(surface)

        self.draw_button(
            surface, "PLAY",
            pygame.Rect(125, 385, 230, 62), True
        )
        self.draw_button(
            surface, "SHOP",
            pygame.Rect(125, 460, 110, 52)
        )
        self.draw_button(
            surface, "STATS",
            pygame.Rect(245, 460, 110, 52)
        )
        self.draw_button(
            surface, "SETTINGS",
            pygame.Rect(125, 525, 230, 52)
        )

        text(surface, f"BEST  {DATA['best']}", FONT, WHITE,
             WIDTH/2, 615)
        text(surface, f"COINS  {DATA['coins']}    LEVEL {DATA['level']}",
             SMALL_FONT, WHITE, WIDTH/2, 655)
        text(surface, "SPACE / CLICK TO FLY",
             SMALL_FONT, LIGHT_GRAY, WIDTH/2, 735)

    def draw_pause(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        surface.blit(overlay, (0, 0))
        text(surface, "PAUSED", HUGE_FONT, WHITE, WIDTH/2, 270)
        self.draw_button(surface, "RESUME",
                         pygame.Rect(125, 380, 230, 58), True)
        self.draw_button(surface, "MENU",
                         pygame.Rect(125, 450, 230, 58))

    def draw_game_over(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        rounded_rect(surface, (35, 42, 62),
                     pygame.Rect(55, 180, 370, 360), 25, 2, LIGHT_GRAY)
        text(surface, "GAME OVER", BIG_FONT, RED, WIDTH/2, 230)

        text(surface, f"SCORE  {self.score}", FONT, WHITE,
             WIDTH/2, 300)
        text(surface, f"BEST   {DATA['best']}", FONT, YELLOW,
             WIDTH/2, 345)
        text(surface, f"COINS  +{self.run_coins}", FONT, YELLOW,
             WIDTH/2, 390)

        self.draw_button(surface, "PLAY AGAIN",
                         pygame.Rect(110, 435, 260, 55), True)
        self.draw_button(surface, "MENU",
                         pygame.Rect(110, 500, 260, 55))

    def draw_shop(self, surface):
        self.draw_background(surface)
        text(surface, "SHOP", BIG_FONT, WHITE, WIDTH/2, 65)
        text(surface, f"🪙 {DATA['coins']}", FONT, YELLOW,
             WIDTH - 75, 65)

        # skins
        text(surface, "SKINS", FONT, WHITE, WIDTH/2, 125)
        for i, skin in enumerate(SKINS):
            x = 45 + (i % 3) * 145
            y = 160 + (i // 3) * 135
            r = pygame.Rect(x, y, 120, 110)
            owned = i in DATA["skins"]
            selected = DATA["selected_skin"] == i
            rounded_rect(
                surface,
                (55, 65, 90) if not selected else (75, 95, 125),
                r, 15, 2, YELLOW if selected else GRAY
            )
            # miniature bird
            pygame.draw.ellipse(
                surface, skin["body"], (x+38, y+25, 48, 34)
            )
            pygame.draw.ellipse(
                surface, skin["wing"], (x+34, y+45, 25, 15)
            )
            text(surface, skin["name"], SMALL_FONT, WHITE,
                 x+60, y+78)
            if owned:
                text(surface, "OWNED", SMALL_FONT, GREEN,
                     x+60, y+98)
            else:
                text(surface, f"{skin['price']} 🪙", SMALL_FONT,
                     YELLOW, x+60, y+98)

        # themes
        text(surface, "THEMES", FONT, WHITE, WIDTH/2, 450)
        for i, theme in enumerate(THEMES):
            x = 45 + i * 108
            y = 485
            r = pygame.Rect(x, y, 95, 100)
            owned = i in DATA["themes"]
            selected = DATA["selected_theme"] == i
            rounded_rect(
                surface, theme["sky"], r, 14, 3,
                YELLOW if selected else WHITE
            )
            text(surface, theme["name"], SMALL_FONT, WHITE,
                 x+47, y+30)
            if owned:
                text(surface, "✓", BIG_FONT, GREEN, x+47, y+68)
            else:
                text(surface, str(theme["price"]), SMALL_FONT,
                     YELLOW, x+47, y+70)

        self.draw_button(surface, "BACK",
                         pygame.Rect(125, 710, 230, 55))

    def draw_settings(self, surface):
        self.draw_background(surface)
        text(surface, "SETTINGS", BIG_FONT, WHITE, WIDTH/2, 100)

        mute = "ON" if DATA.get("muted") else "OFF"
        self.draw_button(
            surface, f"SOUND: {mute}",
            pygame.Rect(105, 220, 270, 60)
        )
        self.draw_button(
            surface, "ACHIEVEMENTS",
            pygame.Rect(105, 295, 270, 60)
        )
        self.draw_button(
            surface, "BACK",
            pygame.Rect(105, 370, 270, 60)
        )

        text(surface, "P = Pause     M = Mute     ESC = Quit",
             SMALL_FONT, LIGHT_GRAY, WIDTH/2, 500)

    def draw_achievements(self, surface):
        self.draw_background(surface)
        text(surface, "ACHIEVEMENTS", BIG_FONT, WHITE, WIDTH/2, 65)

        y = 125
        for key, name, desc in ACHIEVEMENTS:
            unlocked_now = achievement_unlocked(key)
            rounded_rect(
                surface,
                (50, 70, 90) if unlocked_now else (35, 40, 55),
                pygame.Rect(35, y, 410, 78),
                13, 2, GREEN if unlocked_now else GRAY
            )
            text(surface, "✓" if unlocked_now else "?", FONT,
                 GREEN if unlocked_now else GRAY, 62, y+39)
            text(surface, name, FONT, WHITE, 95, y+25, False)
            text(surface, desc, SMALL_FONT, LIGHT_GRAY,
                 95, y+50, False)
            y += 88

        self.draw_button(surface, "BACK",
                         pygame.Rect(125, 690, 230, 55))

    def draw_stats(self, surface):
        self.draw_background(surface)
        text(surface, "STATISTICS", BIG_FONT, WHITE, WIDTH/2, 90)

        stats = [
            ("Best Score", DATA["best"]),
            ("Games Played", DATA["games"]),
            ("Total Score", DATA["total_score"]),
            ("Coins Collected", DATA["total_coins"]),
            ("Flaps", DATA["flaps"]),
            ("Level", DATA["level"]),
        ]
        y = 170
        for label, value in stats:
            rounded_rect(surface, (45, 55, 80),
                         pygame.Rect(70, y, 340, 55), 12)
            text(surface, label, SMALL_FONT, LIGHT_GRAY,
                 90, y+28, False)
            text(surface, value, FONT, WHITE,
                 380, y+28)
            y += 70

        self.draw_button(surface, "BACK",
                         pygame.Rect(125, 630, 230, 55))

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------

    def click(self, pos):
        x, y = pos

        if self.state == self.MENU:
            if pygame.Rect(125, 385, 230, 62).collidepoint(pos):
                self.start()
            elif pygame.Rect(125, 460, 110, 52).collidepoint(pos):
                self.state = self.SHOP
            elif pygame.Rect(245, 460, 110, 52).collidepoint(pos):
                self.state = "stats"
            elif pygame.Rect(125, 525, 230, 52).collidepoint(pos):
                self.state = self.SETTINGS

        elif self.state == self.PLAYING:
            self.bird.flap()

        elif self.state == self.PAUSED:
            if pygame.Rect(125, 380, 230, 58).collidepoint(pos):
                self.state = self.PLAYING
            elif pygame.Rect(125, 450, 230, 58).collidepoint(pos):
                self.state = self.MENU

        elif self.state == self.GAME_OVER:
            if pygame.Rect(110, 435, 260, 55).collidepoint(pos):
                self.start()
            elif pygame.Rect(110, 500, 260, 55).collidepoint(pos):
                self.state = self.MENU

        elif self.state == self.SHOP:
            # skin cards
            for i in range(len(SKINS)):
                x0 = 45 + (i % 3) * 145
                y0 = 160 + (i // 3) * 135
                if pygame.Rect(x0, y0, 120, 110).collidepoint(pos):
                    self.buy_skin(i)
            # themes
            for i in range(len(THEMES)):
                x0 = 45 + i * 108
                if pygame.Rect(x0, 485, 95, 100).collidepoint(pos):
                    self.buy_theme(i)
            if pygame.Rect(125, 710, 230, 55).collidepoint(pos):
                self.state = self.MENU

        elif self.state == self.SETTINGS:
            if pygame.Rect(105, 220, 270, 60).collidepoint(pos):
                DATA["muted"] = not DATA.get("muted", False)
                save_game(DATA)
            elif pygame.Rect(105, 295, 270, 60).collidepoint(pos):
                self.state = self.ACHIEVEMENTS
            elif pygame.Rect(105, 370, 270, 60).collidepoint(pos):
                self.state = self.MENU

        elif self.state == self.ACHIEVEMENTS:
            if pygame.Rect(125, 690, 230, 55).collidepoint(pos):
                self.state = self.SETTINGS

        elif self.state == "stats":
            if pygame.Rect(125, 630, 230, 55).collidepoint(pos):
                self.state = self.MENU

    def buy_skin(self, i):
        if i in DATA["skins"]:
            DATA["selected_skin"] = i
            save_game(DATA)
            return
        price = SKINS[i]["price"]
        if DATA["coins"] >= price:
            DATA["coins"] -= price
            DATA["skins"].append(i)
            DATA["selected_skin"] = i
            save_game(DATA)

    def buy_theme(self, i):
        if i in DATA["themes"]:
            DATA["selected_theme"] = i
            save_game(DATA)
            return
        price = THEMES[i]["price"]
        if DATA["coins"] >= price:
            DATA["coins"] -= price
            DATA["themes"].append(i)
            DATA["selected_theme"] = i
            save_game(DATA)

    def key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state in (self.SHOP, self.SETTINGS,
                              self.ACHIEVEMENTS, "stats"):
                self.state = self.MENU
            elif self.state == self.PLAYING:
                self.state = self.PAUSED
            elif self.state == self.PAUSED:
                self.state = self.PLAYING
            else:
                pygame.quit()
                raise SystemExit

        if key == pygame.K_p:
            if self.state == self.PLAYING:
                self.state = self.PAUSED
            elif self.state == self.PAUSED:
                self.state = self.PLAYING

        if key == pygame.K_m:
            DATA["muted"] = not DATA.get("muted", False)
            save_game(DATA)

        if key in (pygame.K_SPACE, pygame.K_UP):
            if self.state == self.MENU:
                self.start()
            elif self.state == self.PLAYING:
                self.bird.flap()
            elif self.state == self.GAME_OVER:
                self.start()
            elif self.state == self.PAUSED:
                self.state = self.PLAYING

    # --------------------------------------------------------
    # Main loop
    # --------------------------------------------------------

    def update(self, dt):
        self.menu_bob += dt * 3

        if self.state == self.PLAYING:
            self.update_playing(dt)
        elif self.state == self.GAME_OVER:
            self.particles.update(dt)
            if self.bird.y + self.bird.radius < GROUND_Y:
                self.bird.vel += 1100 * dt
                self.bird.y += self.bird.vel * dt
                self.bird.angle -= 120 * dt
                self.bird.angle = max(-90, self.bird.angle)
        elif self.state == self.MENU:
            for cloud in self.clouds:
                cloud.update(dt)

    def draw(self):
        world = pygame.Surface((WIDTH, HEIGHT))
        self.draw_background(world)

        if self.state == self.MENU:
            self.draw_menu(world)
        elif self.state == self.PLAYING:
            self.draw_game(world)
        elif self.state == self.PAUSED:
            self.draw_game(world)
            self.draw_pause(world)
        elif self.state == self.GAME_OVER:
            self.draw_game(world)
            self.draw_game_over(world)
        elif self.state == self.SHOP:
            self.draw_shop(world)
        elif self.state == self.SETTINGS:
            self.draw_settings(world)
        elif self.state == self.ACHIEVEMENTS:
            self.draw_achievements(world)
        elif self.state == "stats":
            self.draw_stats(world)

        if self.banner_time > 0:
            self.banner_time -= 1 / FPS
            rounded_rect(
                world, (30, 35, 50),
                pygame.Rect(75, 115, 330, 48), 15, 2, YELLOW
            )
            text(world, self.banner, SMALL_FONT, YELLOW,
                 WIDTH/2, 139)

        # Screen shake
        ox = oy = 0
        if self.screen_shake > 0:
            ox = random.randint(
                -int(self.screen_shake), int(self.screen_shake)
            )
            oy = random.randint(
                -int(self.screen_shake), int(self.screen_shake)
            )

        SCREEN.fill(BLACK)
        SCREEN.blit(world, (ox, oy))

        if self.flash > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = int(160 * self.flash / 0.25)
            flash.fill((255, 255, 255, alpha))
            SCREEN.blit(flash, (0, 0))

        pygame.display.flip()

    def run(self):
        while True:
            dt = min(CLOCK.tick(FPS) / 1000.0, 0.035)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(DATA)
                    pygame.quit()
                    return

                if event.type == pygame.KEYDOWN:
                    self.key(event.key)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click(event.pos)

            self.update(dt)
            self.draw()



# ============================================================
# BIRDVERSE / CODE FORGE PROFESSIONAL EXPANSION
# ============================================================
# The original systems above remain intact. This section extends
# the same Game, Bird, save data, worlds, UI and gameplay systems
# without removing the original capabilities.

GAME_TITLE = "BIRDVERSE"
BRAND_TEXT = "ساخت : CODE FORGE"
PROJECT_VERSION = "BIRDVERSE 2.0 • CODE FORGE"

ADMIN_PASSWORD = "10071007tahah"

WORLD_DEFINITIONS = [
    {"name": "DAY", "sky": (105, 190, 250), "cloud": (245, 250, 255),
     "accent": (255, 230, 115), "mode": "day"},
    {"name": "SUNSET", "sky": (235, 125, 105), "cloud": (255, 215, 175),
     "accent": (255, 205, 110), "mode": "sunset"},
    {"name": "NIGHT", "sky": (35, 45, 90), "cloud": (95, 105, 150),
     "accent": (225, 225, 190), "mode": "night"},
    {"name": "SPACE", "sky": (12, 12, 35), "cloud": (70, 70, 120),
     "accent": (145, 125, 255), "mode": "space"},
    {"name": "VOID NEBULA", "sky": (12, 5, 28), "cloud": (75, 35, 115),
     "accent": (220, 90, 255), "mode": "nebula"},
    {"name": "CYBER STORM", "sky": (5, 16, 30), "cloud": (20, 80, 105),
     "accent": (40, 245, 235), "mode": "cyber"},
    {"name": "VOLCANIC SKY", "sky": (48, 10, 10), "cloud": (105, 38, 20),
     "accent": (255, 105, 35), "mode": "volcanic"},
    {"name": "ICE KINGDOM", "sky": (80, 165, 205), "cloud": (225, 250, 255),
     "accent": (170, 245, 255), "mode": "ice"},
    {"name": "GOLDEN CLOUDS", "sky": (245, 185, 75), "cloud": (255, 240, 185),
     "accent": (255, 250, 180), "mode": "golden"},
    {"name": "GALAXY RIFT", "sky": (15, 7, 45), "cloud": (90, 55, 150),
     "accent": (110, 200, 255), "mode": "rift"},
]

# Keep the original theme records usable while making the six new
# worlds available through the same theme/shop mechanism.
for _i, _w in enumerate(WORLD_DEFINITIONS):
    if _i < len(THEMES):
        THEMES[_i]["name"] = _w["name"]
        THEMES[_i]["sky"] = _w["sky"]
        THEMES[_i]["cloud"] = _w["cloud"]
    else:
        THEMES.append({
            "name": _w["name"],
            "price": [0, 120, 180, 350, 500, 650, 800, 950, 1100, 1300][_i],
            "sky": _w["sky"],
            "cloud": _w["cloud"],
        })

PRO_WORLD_COUNT = len(WORLD_DEFINITIONS)

# Extra progression content. Existing achievements and missions are
# deliberately retained and only extended.
EXTRA_ACHIEVEMENTS = [
    ("score_100", "Century Flyer", "Reach 100 points"),
    ("score_250", "Sky Master", "Reach 250 points"),
    ("coins_250", "Treasure Wing", "Collect 250 coins total"),
    ("level_5", "Rising Star", "Reach level 5"),
    ("level_10", "Sky Captain", "Reach level 10"),
    ("world_6", "World Walker", "Visit every new world"),
    ("flaps_1000", "Wing Machine", "Flap 1000 times"),
]
ACHIEVEMENTS.extend(EXTRA_ACHIEVEMENTS)

DEFAULT_SAVE.update({
    "xp": DEFAULT_SAVE.get("xp", 0),
    "level": DEFAULT_SAVE.get("level", 1),
    "selected_theme": DEFAULT_SAVE.get("selected_theme", 0),
    "world_visits": [],
    "powerups_enabled": True,
    "random_world": False,
    "performance_mode": False,
    "custom_speed": 190,
    "admin_actions": 0,
    "total_play_time": 0.0,
    "best_combo": 0,
    "missions_extended": {
        "score_50": 0, "score_100": 0, "coins_50": 0,
        "coins_100": 0, "worlds": 0
    },
})

def _bv_merge_defaults():
    """Migrate old save files safely while preserving every old key."""
    fresh = json.loads(json.dumps(DEFAULT_SAVE))
    fresh.update(DATA)
    if not isinstance(fresh.get("world_visits"), list):
        fresh["world_visits"] = []
    if not isinstance(fresh.get("missions_extended"), dict):
        fresh["missions_extended"] = json.loads(
            json.dumps(DEFAULT_SAVE["missions_extended"])
        )
    for key, value in DEFAULT_SAVE.items():
        if key not in fresh:
            fresh[key] = json.loads(json.dumps(value))
    fresh["selected_theme"] = int(clamp(
        int(fresh.get("selected_theme", 0)), 0, PRO_WORLD_COUNT - 1
    ))
    fresh["selected_skin"] = int(clamp(
        int(fresh.get("selected_skin", 0)), 0, len(SKINS) - 1
    ))
    DATA.clear()
    DATA.update(fresh)

_bv_merge_defaults()
save_game(DATA)

def _bv_world_index():
    return int(clamp(int(DATA.get("selected_theme", 0)), 0, PRO_WORLD_COUNT - 1))

def _bv_world():
    return WORLD_DEFINITIONS[_bv_world_index()]

def _bv_record_visit():
    idx = _bv_world_index()
    visits = DATA.setdefault("world_visits", [])
    if idx not in visits:
        visits.append(idx)
    DATA["missions_extended"]["worlds"] = len(visits)

def _bv_unlock_progress():
    checks = [
        ("score_100", DATA.get("best", 0) >= 100),
        ("score_250", DATA.get("best", 0) >= 250),
        ("coins_250", DATA.get("total_coins", 0) >= 250),
        ("level_5", DATA.get("level", 1) >= 5),
        ("level_10", DATA.get("level", 1) >= 10),
        ("world_6", len(DATA.get("world_visits", [])) >= 10),
        ("flaps_1000", DATA.get("flaps", 0) >= 1000),
    ]
    changed = False
    for key, ok in checks:
        if ok and not achievement_unlocked(key):
            DATA["achievements"].append(key)
            changed = True
    return changed

# ---------- lightweight cached visuals ----------
_BV_BG_CACHE = {}
_BV_LAST_PARTICLE_TIME = 0.0

def _bv_gradient(surface, top, bottom):
    key = (tuple(top), tuple(bottom), WIDTH, HEIGHT)
    cached = _BV_BG_CACHE.get(key)
    if cached is None:
        cached = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / max(1, HEIGHT - 1)
            c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            pygame.draw.line(cached, c, (0, y), (WIDTH, y))
        if len(_BV_BG_CACHE) > 12:
            _BV_BG_CACHE.pop(next(iter(_BV_BG_CACHE)))
        _BV_BG_CACHE[key] = cached
    surface.blit(cached, (0, 0))

def _bv_poly(surface, color, points):
    pygame.draw.polygon(surface, color, points)

def _bv_draw_world(self, surface):
    w = _bv_world()
    mode = w["mode"]
    top = w["sky"]
    bottom = tuple(max(0, int(v * 0.38)) for v in top)
    _bv_gradient(surface, top, bottom)

    # Original Day/Sunset/Night/Space worlds keep their visual identity,
    # while the professional worlds receive their own atmosphere.
    if mode in ("day", "sunset", "night", "space"):
        theme = THEMES[_bv_world_index()]
        if mode == "space":
            for star in self.stars:
                star.draw(surface)
            pygame.draw.circle(surface, (70, 70, 120), (390, 130), 65)
            pygame.draw.circle(surface, (105, 105, 165), (370, 110), 20)
        else:
            sun = (225, 225, 190) if mode == "night" else (255, 230, 115)
            pygame.draw.circle(surface, sun, (390, 105), 48 if mode != "night" else 43)
            for cloud in self.clouds:
                cloud.draw(surface, theme["cloud"])
        hill_color = (20, 30, 70) if mode in ("night", "space") else (100, 190, 130)
        _bv_poly(surface, hill_color, [
            (0, GROUND_Y), (0, 520), (90, 440), (170, 520),
            (250, 420), (340, 520), (430, 450), (WIDTH, 520),
            (WIDTH, GROUND_Y)
        ])
        return

    now = time.time()
    if mode == "nebula":
        for i in range(6):
            cx = int(55 + i * 95 + math.sin(now * 0.25 + i) * 18)
            cy = int(125 + (i % 3) * 105)
            pygame.draw.circle(surface, (55, 20 + i * 7, 90 + i * 12), 72, 0)
            pygame.draw.circle(surface, (115, 30, 150), (cx, cy), 28, 2)
        for star in self.stars:
            star.draw(surface)
        _bv_poly(surface, (28, 12, 55), [
            (0, GROUND_Y), (0, 545), (90, 475), (180, 535),
            (280, 455), (390, 525), (WIDTH, 470), (WIDTH, GROUND_Y)
        ])
    elif mode == "cyber":
        for y in range(70, GROUND_Y, 55):
            pygame.draw.line(surface, (10, 85, 105), (0, y), (WIDTH, y), 1)
        for x in range(-40, WIDTH + 80, 55):
            pygame.draw.line(surface, (15, 65, 90), (x, 420), (x + 130, GROUND_Y), 1)
        for i in range(14):
            x = int((i * 71 + now * (18 + i % 3 * 7)) % (WIDTH + 50)) - 25
            pygame.draw.line(surface, (40, 210, 205), (x, 70), (x - 35, 135), 2)
        _bv_poly(surface, (7, 35, 48), [
            (0, GROUND_Y), (0, 510), (80, 450), (150, 500),
            (230, 435), (315, 500), (400, 440), (WIDTH, 500),
            (WIDTH, GROUND_Y)
        ])
    elif mode == "volcanic":
        for i in range(9):
            x = int((i * 67 + now * (8 + i)) % (WIDTH + 70)) - 35
            y = int(90 + ((i * 73) % 260))
            pygame.draw.circle(surface, (150, 48, 20), (x, y), 4)
        _bv_poly(surface, (75, 18, 15), [
            (0, GROUND_Y), (0, 540), (80, 430), (150, 515),
            (245, 405), (335, 515), (420, 435), (WIDTH, 520),
            (WIDTH, GROUND_Y)
        ])
        pygame.draw.circle(surface, (255, 95, 25), (390, 125), 45)
    elif mode == "ice":
        for i in range(9):
            x = 25 + i * 58
            h = 45 + (i % 4) * 20
            _bv_poly(surface, (190, 235, 250), [
                (x, GROUND_Y), (x + 25, GROUND_Y - h),
                (x + 50, GROUND_Y)
            ])
        _bv_poly(surface, (150, 215, 240), [
            (0, GROUND_Y), (0, 500), (80, 440), (170, 510),
            (250, 450), (350, 510), (WIDTH, 460), (WIDTH, GROUND_Y)
        ])
        for cloud in self.clouds:
            cloud.draw(surface, w["cloud"])
    elif mode == "golden":
        pygame.draw.circle(surface, (255, 238, 155), (385, 115), 58)
        for cloud in self.clouds:
            cloud.draw(surface, w["cloud"])
        _bv_poly(surface, (175, 125, 45), [
            (0, GROUND_Y), (0, 505), (95, 450), (185, 505),
            (280, 440), (375, 505), (WIDTH, 450), (WIDTH, GROUND_Y)
        ])
    elif mode == "rift":
        for i in range(5):
            pts = []
            for j in range(9):
                x = j * 60 + math.sin(now * .5 + j + i) * 10
                y = 110 + i * 70 + math.cos(now * .7 + j) * 14
                pts.append((x, y))
            if len(pts) > 1:
                pygame.draw.lines(surface, (70, 125, 230), False, pts, 2)
        for star in self.stars:
            star.draw(surface)
        pygame.draw.ellipse(surface, (45, 20, 100), (300, 60, 170, 120), 3)
        _bv_poly(surface, (22, 14, 65), [
            (0, GROUND_Y), (0, 525), (90, 465), (180, 520),
            (270, 450), (360, 520), (WIDTH, 470), (WIDTH, GROUND_Y)
        ])

def _bv_draw_ground(self, surface):
    mode = _bv_world()["mode"]
    grounds = {
        "day": (205, 170, 85), "sunset": (190, 135, 65),
        "night": (55, 60, 80), "space": (40, 40, 70),
        "nebula": (35, 20, 60), "cyber": (12, 55, 65),
        "volcanic": (70, 28, 18), "ice": (150, 205, 220),
        "golden": (195, 145, 45), "rift": (35, 22, 80)
    }
    ground = grounds.get(mode, (70, 90, 90))
    pygame.draw.rect(surface, ground, (0, GROUND_Y, WIDTH, GROUND_H))
    pygame.draw.rect(surface, _bv_world()["accent"], (0, GROUND_Y, WIDTH, 10))
    step = 45 if not DATA.get("performance_mode") else 60
    for x in range(-20, WIDTH + 40, step):
        pygame.draw.rect(surface, tuple(max(0, c - 35) for c in ground),
                         (x, GROUND_Y + 35, 23, 7))

# Cache menu preview bird rather than creating work-heavy objects every frame.
def _bv_draw_button(self, surface, label, rect, active=False, accent=None):
    c = (65, 75, 100) if not active else (90, 110, 150)
    rounded_rect(surface, c, rect, 14, 2, accent or LIGHT_GRAY)
    text(surface, label, SMALL_FONT if len(str(label)) > 18 else FONT,
         WHITE, rect.centerx, rect.centery)

def _bv_draw_menu(self, surface):
    self.draw_background(surface)
    bob = math.sin(self.menu_bob) * 8
    text(surface, GAME_TITLE, HUGE_FONT, WHITE, WIDTH / 2, 100 + bob)
    text(surface, "CODE FORGE EDITION", SMALL_FONT, _bv_world()["accent"],
         WIDTH / 2, 157 + bob)
    preview = Bird()
    preview.x, preview.y = WIDTH / 2, 245 + bob
    preview.angle, preview.wing_phase = 0, self.menu_bob
    preview.draw(surface)

    self.draw_button(surface, "PLAY", pygame.Rect(115, 315, 250, 56), True)
    self.draw_button(surface, "SHOP", pygame.Rect(115, 382, 120, 50))
    self.draw_button(surface, "STATS", pygame.Rect(245, 382, 120, 50))
    self.draw_button(surface, "SETTINGS", pygame.Rect(115, 444, 250, 50))
    _bv_draw_button(self, surface, "⚙ ADMIN PANEL",
                    pygame.Rect(115, 506, 250, 52), False, _bv_world()["accent"])

    text(surface, f"BEST  {DATA['best']}    COINS  {DATA['coins']}",
         SMALL_FONT, WHITE, WIDTH / 2, 595)
    text(surface, f"LEVEL {DATA['level']}  •  WORLD: {_bv_world()['name']}",
         SMALL_FONT, LIGHT_GRAY, WIDTH / 2, 628)
    text(surface, BRAND_TEXT, SMALL_FONT, _bv_world()["accent"],
         WIDTH / 2, 690)
    text(surface, "SPACE / CLICK TO FLY", SMALL_FONT, LIGHT_GRAY,
         WIDTH / 2, 730)

def _bv_draw_stats(self, surface):
    self.draw_background(surface)
    text(surface, "STATISTICS", BIG_FONT, WHITE, WIDTH / 2, 55)
    stats = [
        ("Best Score", DATA["best"]), ("Games Played", DATA["games"]),
        ("Total Score", DATA["total_score"]), ("Coins Collected", DATA["total_coins"]),
        ("Flaps", DATA["flaps"]), ("Level", DATA["level"]),
        ("XP", DATA["xp"]), ("Worlds Visited", len(DATA.get("world_visits", []))),
        ("Play Time", f"{DATA.get('total_play_time', 0):.1f}s"),
        ("Achievements", f"{len(DATA.get('achievements', []))}/{len(ACHIEVEMENTS)}"),
    ]
    y = 105
    for label, value in stats:
        rounded_rect(surface, (45, 55, 80), pygame.Rect(35, y, 410, 43), 10)
        text(surface, label, SMALL_FONT, LIGHT_GRAY, 55, y + 21, False)
        text(surface, value, SMALL_FONT, WHITE, 425, y + 21)
        y += 48
    self.draw_button(surface, "BACK", pygame.Rect(125, 635, 230, 52))

def _bv_draw_shop(self, surface):
    self.draw_background(surface)
    text(surface, "SHOP", BIG_FONT, WHITE, WIDTH / 2, 48)
    text(surface, f"COINS  {DATA['coins']}", SMALL_FONT, YELLOW, WIDTH - 75, 50)
    text(surface, "BIRDS", FONT, WHITE, WIDTH / 2, 100)
    for i, skin in enumerate(SKINS):
        x = 28 + (i % 3) * 145
        y = 125 + (i // 3) * 100
        r = pygame.Rect(x, y, 125, 88)
        owned = i in DATA["skins"]
        selected = DATA["selected_skin"] == i
        rounded_rect(surface, (55, 65, 90) if not selected else (75, 95, 125),
                      r, 12, 2, YELLOW if selected else GRAY)
        pygame.draw.ellipse(surface, skin["body"], (x + 38, y + 13, 45, 31))
        pygame.draw.ellipse(surface, skin["wing"], (x + 34, y + 34, 24, 14))
        text(surface, skin["name"], SMALL_FONT, WHITE, x + 62, y + 61)
        text(surface, "OWNED" if owned else f"{skin['price']} C",
             SMALL_FONT, GREEN if owned else YELLOW, x + 62, y + 78)
    text(surface, "WORLDS", FONT, WHITE, WIDTH / 2, 355)
    for i, world in enumerate(WORLD_DEFINITIONS):
        x = 20 + (i % 3) * 150
        y = 380 + (i // 3) * 88
        r = pygame.Rect(x, y, 140, 72)
        owned = i in DATA["themes"]
        selected = _bv_world_index() == i
        rounded_rect(surface, world["sky"], r, 11, 3,
                     YELLOW if selected else WHITE)
        text(surface, world["name"], SMALL_FONT, WHITE, x + 70, y + 22)
        text(surface, "OWNED" if owned else f"{THEMES[i]['price']} C",
             SMALL_FONT, GREEN if owned else YELLOW, x + 70, y + 49)
    self.draw_button(surface, "BACK", pygame.Rect(125, 700, 230, 50))

def _bv_draw_settings(self, surface):
    self.draw_background(surface)
    text(surface, "SETTINGS", BIG_FONT, WHITE, WIDTH / 2, 80)
    mute = "ON" if DATA.get("muted") else "OFF"
    self.draw_button(surface, f"SOUND: {mute}", pygame.Rect(105, 165, 270, 52))
    self.draw_button(surface, "ACHIEVEMENTS", pygame.Rect(105, 228, 270, 52))
    self.draw_button(surface, "WORLD SELECT", pygame.Rect(105, 291, 270, 52))
    self.draw_button(surface, "PERFORMANCE MODE", pygame.Rect(105, 354, 270, 52),
                     bool(DATA.get("performance_mode")))
    self.draw_button(surface, "BACK", pygame.Rect(105, 417, 270, 52))
    text(surface, f"Random World: {'ON' if DATA.get('random_world') else 'OFF'}",
         SMALL_FONT, LIGHT_GRAY, WIDTH / 2, 505)
    text(surface, "P = Pause   M = Mute   ESC = Back/Quit",
         SMALL_FONT, LIGHT_GRAY, WIDTH / 2, 550)
    text(surface, PROJECT_VERSION, SMALL_FONT, _bv_world()["accent"],
         WIDTH / 2, 610)
    text(surface, BRAND_TEXT, SMALL_FONT, WHITE, WIDTH / 2, 650)

def _bv_draw_world_select(self, surface):
    self.draw_background(surface)
    text(surface, "WORLD SELECT", BIG_FONT, WHITE, WIDTH / 2, 55)
    for i, world in enumerate(WORLD_DEFINITIONS):
        x = 18 + (i % 2) * 232
        y = 105 + (i // 2) * 93
        r = pygame.Rect(x, y, 215, 78)
        selected = i == _bv_world_index()
        rounded_rect(surface, world["sky"], r, 12, 3,
                     YELLOW if selected else WHITE)
        text(surface, world["name"], SMALL_FONT, WHITE, x + 107, y + 22)
        status = "SELECTED" if selected else ("OWNED" if i in DATA["themes"] else f"{THEMES[i]['price']} C")
        text(surface, status, SMALL_FONT, GREEN if status in ("SELECTED", "OWNED") else YELLOW,
             x + 107, y + 52)
    self.draw_button(surface, "BACK", pygame.Rect(125, 710, 230, 52))

def _bv_draw_achievements(self, surface):
    self.draw_background(surface)
    text(surface, "ACHIEVEMENTS", BIG_FONT, WHITE, WIDTH / 2, 52)
    y = 108
    for key, name, desc in ACHIEVEMENTS:
        unlocked_now = achievement_unlocked(key)
        rounded_rect(surface, (50, 70, 90) if unlocked_now else (35, 40, 55),
                     pygame.Rect(25, y, 430, 62), 11, 2,
                     GREEN if unlocked_now else GRAY)
        text(surface, "✓" if unlocked_now else "?", SMALL_FONT,
             GREEN if unlocked_now else GRAY, 48, y + 31)
        text(surface, name, SMALL_FONT, WHITE, 75, y + 20, False)
        text(surface, desc, SMALL_FONT, LIGHT_GRAY, 75, y + 43, False)
        y += 69
        if y > 680:
            break
    self.draw_button(surface, "BACK", pygame.Rect(125, 715, 230, 48))

def _bv_draw_admin_login(self, surface):
    self.draw_background(surface)
    rounded_rect(surface, (25, 32, 50), pygame.Rect(35, 175, 410, 330), 22, 2,
                 _bv_world()["accent"])
    text(surface, "ADMIN PANEL", BIG_FONT, WHITE, WIDTH / 2, 225)
    text(surface, "ENTER ADMIN PASSWORD", SMALL_FONT, LIGHT_GRAY, WIDTH / 2, 275)
    box = pygame.Rect(65, 305, 350, 55)
    rounded_rect(surface, (10, 15, 25), box, 12, 2, _bv_world()["accent"])
    shown = "*" * len(getattr(self, "admin_input", ""))
    text(surface, shown or "PASSWORD", FONT, WHITE, box.centerx, box.centery)
    if getattr(self, "admin_error", ""):
        text(surface, self.admin_error, SMALL_FONT, RED, WIDTH / 2, 385)
    text(surface, "ENTER = LOGIN   ESC = BACK", SMALL_FONT, LIGHT_GRAY, WIDTH / 2, 435)
    self.draw_button(surface, "BACK", pygame.Rect(125, 465, 230, 45))

def _bv_admin_action(self, action):
    if action == "add_coins":
        DATA["coins"] += 100
        self.banner, self.banner_time = "+100 COINS", 1.5
    elif action == "zero_coins":
        DATA["coins"] = 0
        self.banner, self.banner_time = "COINS RESET", 1.5
    elif action == "reset_best":
        DATA["best"] = 0
        self.banner, self.banner_time = "BEST SCORE RESET", 1.5
    elif action == "random_world":
        DATA["selected_theme"] = random.randrange(PRO_WORLD_COUNT)
        if DATA["selected_theme"] not in DATA["themes"]:
            DATA["themes"].append(DATA["selected_theme"])
        _bv_record_visit()
    elif action == "next_world":
        DATA["selected_theme"] = (_bv_world_index() + 1) % PRO_WORLD_COUNT
        if DATA["selected_theme"] not in DATA["themes"]:
            DATA["themes"].append(DATA["selected_theme"])
        _bv_record_visit()
    elif action == "next_bird":
        DATA["selected_skin"] = (DATA["selected_skin"] + 1) % len(SKINS)
    elif action == "powerups":
        DATA["powerups_enabled"] = not DATA.get("powerups_enabled", True)
    elif action == "random_toggle":
        DATA["random_world"] = not DATA.get("random_world", False)
    elif action == "speed_down":
        DATA["custom_speed"] = max(120, DATA.get("custom_speed", 190) - 10)
    elif action == "speed_up":
        DATA["custom_speed"] = min(360, DATA.get("custom_speed", 190) + 10)
    elif action == "performance":
        DATA["performance_mode"] = not DATA.get("performance_mode", False)
    elif action == "save":
        save_game(DATA)
        self.banner, self.banner_time = "DATA SAVED", 1.5
    DATA["admin_actions"] = DATA.get("admin_actions", 0) + 1
    save_game(DATA)

def _bv_draw_admin(self, surface):
    self.draw_background(surface)
    text(surface, "⚙ ADMIN PANEL", BIG_FONT, WHITE, WIDTH / 2, 50)
    text(surface, f"{PROJECT_VERSION}  •  {BRAND_TEXT}", SMALL_FONT,
         _bv_world()["accent"], WIDTH / 2, 88)
    rounded_rect(surface, (25, 32, 50), pygame.Rect(20, 110, 440, 555), 18, 2, GRAY)
    text(surface, f"RECORD: {DATA['best']}", SMALL_FONT, WHITE, 42, 140, False)
    text(surface, f"COINS: {DATA['coins']}", SMALL_FONT, YELLOW, 42, 170, False)
    text(surface, f"WORLD: {_bv_world()['name']}", SMALL_FONT, WHITE, 42, 200, False)
    text(surface, f"BIRD: {SKINS[DATA['selected_skin']]['name']}", SMALL_FONT, WHITE, 42, 230, False)
    text(surface, f"LEVEL: {DATA['level']}   XP: {DATA['xp']}", SMALL_FONT, WHITE, 42, 260, False)
    text(surface, f"Games: {DATA['games']}   Total Score: {DATA['total_score']}",
         SMALL_FONT, LIGHT_GRAY, 42, 290, False)
    buttons = [
        ("+100 COINS", "add_coins"), ("ZERO COINS", "zero_coins"),
        ("RESET RECORD", "reset_best"), ("NEXT WORLD", "next_world"),
        ("RANDOM WORLD", "random_world"), ("NEXT BIRD", "next_bird"),
        ("POWERUPS: " + ("ON" if DATA.get("powerups_enabled") else "OFF"), "powerups"),
        ("RANDOM: " + ("ON" if DATA.get("random_world") else "OFF"), "random_toggle"),
        ("SPEED -", "speed_down"), ("SPEED +", "speed_up"),
        ("PERFORMANCE: " + ("ON" if DATA.get("performance_mode") else "OFF"), "performance"),
        ("SAVE DATA", "save"),
    ]
    for i, (label, action) in enumerate(buttons):
        x = 35 + (i % 2) * 215
        y = 315 + (i // 2) * 50
        _bv_draw_button(self, surface, label, pygame.Rect(x, y, 200, 42),
                        False, _bv_world()["accent"])
    text(surface, f"GAME SPEED: {DATA.get('custom_speed', 190)}",
         SMALL_FONT, _bv_world()["accent"], WIDTH / 2, 625)
    self.draw_button(surface, "BACK TO MENU", pygame.Rect(125, 680, 230, 50))

# ---------- upgraded gameplay hooks ----------
_old_start = Game.start
_old_game_over = Game.game_over
_old_spawn_powerup = Game.spawn_powerup
_old_update_playing = Game.update_playing

def _bv_start(self):
    self.screen_shake = 0
    self.flash = 0
    if DATA.get("random_world"):
        DATA["selected_theme"] = random.randrange(PRO_WORLD_COUNT)
        if DATA["selected_theme"] not in DATA["themes"]:
            DATA["themes"].append(DATA["selected_theme"])
    _bv_record_visit()
    _old_start(self)
    self.speed = DATA.get("custom_speed", 190)
    self.session_start = time.time()

def _bv_game_over(self):
    _old_game_over(self)
    _bv_unlock_progress()
    save_game(DATA)

def _bv_spawn_powerup(self):
    if DATA.get("powerups_enabled", True):
        _old_spawn_powerup(self)

def _bv_update_playing(self, dt):
    if getattr(self, "session_start", None):
        DATA["total_play_time"] = DATA.get("total_play_time", 0.0) + dt
    # Keep the original difficulty curve but let Admin choose the base speed.
    _old_update_playing(self, dt)
    base = DATA.get("custom_speed", 190)
    self.speed = min(360, base + self.score * 2.4)
    if not DATA.get("powerups_enabled", True):
        self.powerups.clear()

Game.start = _bv_start
Game.game_over = _bv_game_over
Game.spawn_powerup = _bv_spawn_powerup
Game.update_playing = _bv_update_playing

# ---------- professional drawing overrides ----------
Game.draw_background = _bv_draw_world
Game.draw_ground = _bv_draw_ground
Game.draw_button = _bv_draw_button
Game.draw_menu = _bv_draw_menu
Game.draw_shop = _bv_draw_shop
Game.draw_settings = _bv_draw_settings
Game.draw_achievements = _bv_draw_achievements
Game.draw_stats = _bv_draw_stats
Game.draw_admin_login = _bv_draw_admin_login
Game.draw_admin = _bv_draw_admin
Game.draw_world_select = _bv_draw_world_select

# ---------- admin state ----------
Game.ADMIN_LOGIN = "admin_login"
Game.ADMIN = "admin"
Game.WORLD_SELECT = "world_select"

_old_init = Game.__init__
def _bv_init(self):
    _old_init(self)
    self.admin_input = ""
    self.admin_error = ""
    self.admin_text_input_active = False
    self.session_start = None
Game.__init__ = _bv_init

def _bv_start_admin_text_input(self):
    self.admin_text_input_active = True
    try:
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(pygame.Rect(65, 305, 350, 55))
    except (AttributeError, pygame.error):
        # Older pygame builds may not expose SDL text-input helpers.
        pass

def _bv_stop_admin_text_input(self):
    self.admin_text_input_active = False
    try:
        pygame.key.stop_text_input()
    except (AttributeError, pygame.error):
        pass

def _bv_draw(self):
    world = pygame.Surface((WIDTH, HEIGHT))
    self.draw_background(world)
    if self.state == self.MENU:
        self.draw_menu(world)
    elif self.state == self.PLAYING:
        self.draw_game(world)
    elif self.state == self.PAUSED:
        self.draw_game(world)
        self.draw_pause(world)
    elif self.state == self.GAME_OVER:
        self.draw_game(world)
        self.draw_game_over(world)
    elif self.state == self.SHOP:
        self.draw_shop(world)
    elif self.state == self.SETTINGS:
        self.draw_settings(world)
    elif self.state == self.ACHIEVEMENTS:
        self.draw_achievements(world)
    elif self.state == "stats":
        self.draw_stats(world)
    elif self.state == self.ADMIN_LOGIN:
        self.draw_admin_login(world)
    elif self.state == self.ADMIN:
        self.draw_admin(world)
    elif self.state == self.WORLD_SELECT:
        self.draw_world_select(world)

    if self.banner_time > 0:
        self.banner_time -= 1 / FPS
        rounded_rect(world, (30, 35, 50), pygame.Rect(55, 115, 370, 48),
                     15, 2, _bv_world()["accent"])
        text(world, self.banner, SMALL_FONT, _bv_world()["accent"],
             WIDTH / 2, 139)

    ox = oy = 0
    if self.screen_shake > 0:
        ox = random.randint(-int(self.screen_shake), int(self.screen_shake))
        oy = random.randint(-int(self.screen_shake), int(self.screen_shake))
    SCREEN.fill(BLACK)
    SCREEN.blit(world, (ox, oy))
    if self.flash > 0:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((255, 255, 255, int(160 * self.flash / 0.25)))
        SCREEN.blit(flash, (0, 0))
    pygame.display.flip()

Game.draw = _bv_draw

def _bv_click(self, pos):
    if self.state == self.MENU:
        if pygame.Rect(115, 315, 250, 56).collidepoint(pos):
            self.start()
        elif pygame.Rect(115, 382, 120, 50).collidepoint(pos):
            self.state = self.SHOP
        elif pygame.Rect(245, 382, 120, 50).collidepoint(pos):
            self.state = "stats"
        elif pygame.Rect(115, 444, 250, 50).collidepoint(pos):
            self.state = self.SETTINGS
        elif pygame.Rect(115, 506, 250, 52).collidepoint(pos):
            self.state = self.ADMIN_LOGIN
            self.admin_input = ""
            self.admin_error = ""
            _bv_start_admin_text_input(self)
    elif self.state == self.ADMIN_LOGIN:
        if pygame.Rect(125, 465, 230, 45).collidepoint(pos):
            _bv_stop_admin_text_input(self)
            self.state = self.MENU
            self.admin_input = ""
    elif self.state == self.ADMIN:
        buttons = [
            "add_coins", "zero_coins", "reset_best", "next_world",
            "random_world", "next_bird", "powerups", "random_toggle",
            "speed_down", "speed_up", "performance", "save"
        ]
        for i, action in enumerate(buttons):
            x = 35 + (i % 2) * 215
            y = 315 + (i // 2) * 50
            if pygame.Rect(x, y, 200, 42).collidepoint(pos):
                _bv_admin_action(self, action)
                return
        if pygame.Rect(125, 680, 230, 50).collidepoint(pos):
            self.state = self.MENU
    elif self.state == self.WORLD_SELECT:
        for i in range(PRO_WORLD_COUNT):
            x = 18 + (i % 2) * 232
            y = 105 + (i // 2) * 93
            if pygame.Rect(x, y, 215, 78).collidepoint(pos):
                if i in DATA["themes"]:
                    DATA["selected_theme"] = i
                    _bv_record_visit()
                    save_game(DATA)
                elif DATA["coins"] >= THEMES[i]["price"]:
                    DATA["coins"] -= THEMES[i]["price"]
                    DATA["themes"].append(i)
                    DATA["selected_theme"] = i
                    _bv_record_visit()
                    save_game(DATA)
                return
        if pygame.Rect(125, 710, 230, 52).collidepoint(pos):
            self.state = self.SETTINGS
    elif self.state == self.SETTINGS:
        if pygame.Rect(105, 165, 270, 52).collidepoint(pos):
            DATA["muted"] = not DATA.get("muted", False)
            save_game(DATA)
        elif pygame.Rect(105, 228, 270, 52).collidepoint(pos):
            self.state = self.ACHIEVEMENTS
        elif pygame.Rect(105, 291, 270, 52).collidepoint(pos):
            self.state = self.WORLD_SELECT
        elif pygame.Rect(105, 354, 270, 52).collidepoint(pos):
            DATA["performance_mode"] = not DATA.get("performance_mode", False)
            save_game(DATA)
        elif pygame.Rect(105, 417, 270, 52).collidepoint(pos):
            self.state = self.MENU
    elif self.state == self.SHOP:
        for i in range(len(SKINS)):
            x0, y0 = 28 + (i % 3) * 145, 125 + (i // 3) * 100
            if pygame.Rect(x0, y0, 125, 88).collidepoint(pos):
                self.buy_skin(i)
                return
        for i in range(PRO_WORLD_COUNT):
            x0, y0 = 20 + (i % 3) * 150, 380 + (i // 3) * 88
            if pygame.Rect(x0, y0, 140, 72).collidepoint(pos):
                self.buy_theme(i)
                return
        if pygame.Rect(125, 700, 230, 50).collidepoint(pos):
            self.state = self.MENU
    elif self.state == "stats":
        if pygame.Rect(125, 635, 230, 52).collidepoint(pos):
            self.state = self.MENU
    elif self.state == self.ACHIEVEMENTS:
        if pygame.Rect(125, 715, 230, 48).collidepoint(pos):
            self.state = self.SETTINGS
    elif self.state == self.PLAYING:
        self.bird.flap()
    elif self.state == self.PAUSED:
        if pygame.Rect(125, 380, 230, 58).collidepoint(pos):
            self.state = self.PLAYING
        elif pygame.Rect(125, 450, 230, 58).collidepoint(pos):
            self.state = self.MENU
    elif self.state == self.GAME_OVER:
        if pygame.Rect(110, 435, 260, 55).collidepoint(pos):
            self.start()
        elif pygame.Rect(110, 500, 260, 55).collidepoint(pos):
            self.state = self.MENU
            self.screen_shake = 0
            self.flash = 0

Game.click = _bv_click

def _bv_key(self, key):
    if self.state == self.ADMIN_LOGIN:
        if key == pygame.K_ESCAPE:
            _bv_stop_admin_text_input(self)
            self.state = self.MENU
            self.admin_input = ""
            self.admin_error = ""
            self.screen_shake = 0
            self.flash = 0
            return
        if key == pygame.K_BACKSPACE:
            self.admin_input = self.admin_input[:-1]
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.admin_input == ADMIN_PASSWORD:
                _bv_stop_admin_text_input(self)
                self.state = self.ADMIN
                self.admin_error = ""
                self.admin_input = ""
                self.banner, self.banner_time = "ADMIN ACCESS GRANTED", 1.5
            else:
                self.admin_error = "INVALID PASSWORD"
                self.admin_input = ""
            return
        return

    if self.state == self.ADMIN:
        if key == pygame.K_ESCAPE:
            self.state = self.MENU
            return
        # Numeric keyboard shortcuts make admin controls fast without
        # replacing the visible buttons.
        shortcuts = {
            pygame.K_1: "add_coins", pygame.K_2: "zero_coins",
            pygame.K_3: "reset_best", pygame.K_4: "next_world",
            pygame.K_5: "random_world", pygame.K_6: "next_bird",
            pygame.K_7: "powerups", pygame.K_8: "random_toggle",
            pygame.K_9: "performance", pygame.K_0: "save",
        }
        if key in shortcuts:
            _bv_admin_action(self, shortcuts[key])
            return
        return

    if self.state == self.WORLD_SELECT and key == pygame.K_ESCAPE:
        self.state = self.SETTINGS
        return
    if self.state == self.SETTINGS and key == pygame.K_ESCAPE:
        self.state = self.MENU
        return

    # Preserve every original keyboard control by delegating all
    # non-admin keys to the original implementation.
    original_key = _ORIGINAL_GAME_KEY
    original_key(self, key)

_ORIGINAL_GAME_KEY = Game.key
Game.key = _bv_key

# pygame TEXTINPUT provides clean password entry on mobile/desktop
# keyboards. KEYDOWN remains as a fallback for environments without it.
_old_run = Game.run
def _bv_run(self):
    while True:
        dt = min(CLOCK.tick(FPS) / 1000.0, 0.035)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _bv_stop_admin_text_input(self)
                save_game(DATA)
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if self.state == self.ADMIN_LOGIN:
                    if event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                         pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        if event.unicode and event.unicode.isprintable():
                            self.admin_input += event.unicode
                    self.key(event.key)
                else:
                    self.key(event.key)
            elif event.type == pygame.TEXTINPUT and self.state == self.ADMIN_LOGIN:
                if event.text:
                    self.admin_input += event.text
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.click(event.pos)
        self.update(dt)
        self.draw()

Game.run = _bv_run

# Extend update with progression maintenance while preserving the
# original update state machine.
_ORIGINAL_UPDATE = Game.update
def _bv_update(self, dt):
    _ORIGINAL_UPDATE(self, dt)
    if self.state == self.MENU:
        # Clouds were already updated by the original menu updater.
        pass
    if not DATA.get("performance_mode"):
        _bv_unlock_progress()
    # Prevent particle buildup on long sessions.
    if len(self.particles.items) > 500:
        self.particles.items = self.particles.items[-500:]

Game.update = _bv_update

# Professional title and a few safe runtime settings.
pygame.display.set_caption(GAME_TITLE + " • " + BRAND_TEXT)

# Final migration/save after all expansion keys are registered.
_bv_record_visit()
_bv_unlock_progress()
save_game(DATA)

# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    try:
        Game().run()
    except KeyboardInterrupt:
        save_game(DATA)
        pygame.quit()
