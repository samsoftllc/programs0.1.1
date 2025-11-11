#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cat's PunJedi's Safari – Wa Wa FX Edition
SNES-style rail shooter emulation using a pseudo-3D Mode 7 floor, now enhanced with elements from Yoshi's Safari.
Controls:
  ← → ↑ ↓ – Move
  SPACE – Fire plasma-egg barrage
  R – Restart after defeat
"""
import pygame, random, sys, math
pygame.init()
# ───────── SCREEN / CORE CONFIG ─────────
SCREEN_W, SCREEN_H = 640, 480
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Cat's PunJedi's Safari – Wa Wa FX Edition")
clock = pygame.time.Clock()
# ───────── COLORS ─────────
BLACK=(0,0,0); WHITE=(255,255,255)
RED=(255,0,0); GREEN=(0,255,0)
BLUE=(0,0,255); YELLOW=(255,255,0)
PURPLE=(128,0,128); ORANGE=(255,165,0)
BROWN=(165,42,42); GRAY=(128,128,128)
# ───────── FONTS ─────────
font = pygame.font.SysFont(None,36)
small_font = pygame.font.SysFont(None,24)
# ───────── WA WA FX CORE ─────────
class WaWaFX:
    """Fake Mode 7 floor renderer + CRT tint"""
    def __init__(self, screen):
        self.screen = screen
        self.scroll = 0
        self.floor_tex = self._make_floor_tex()
    def _make_floor_tex(self):
        surf = pygame.Surface((128,128))
        for x in range(128):
            for y in range(128):
                c = (x*2 ^ y*2) & 255
                surf.set_at((x,y),(0,c//2,0))
        return surf
    def draw_floor(self):
        w,h = self.screen.get_size()
        tex = self.floor_tex
        for y in range(h//2, h):
            p = (y-h/2)/(h/2)
            scale = 1.0/(p+0.001)
            row = pygame.transform.scale(tex,(int(w*scale),1))
            offset = int(self.scroll % row.get_width())
            self.screen.blit(row,(-offset,y))
        self.scroll += 2
    def crt_tint(self):
        arr = pygame.surfarray.pixels3d(self.screen)
        arr[...,1] = (arr[...,1]*0.95).astype('uint8')
        del arr
# ───────── ENTITIES ─────────
class PunJedi:
    def __init__(self):
        self.x=SCREEN_W//2; self.y=SCREEN_H-100
        self.w,self.h=40,40; self.speed=5
        self.health = 5  # Added health system
        self.invinc_timer = 0  # For star power-up
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self,keys):
        if keys[pygame.K_LEFT] and self.x>0:self.x-=self.speed
        if keys[pygame.K_RIGHT] and self.x<SCREEN_W-self.w:self.x+=self.speed
        if keys[pygame.K_UP] and self.y>0:self.y-=self.speed
        if keys[pygame.K_DOWN] and self.y<SCREEN_H-self.h:self.y+=self.speed
        self.rect.topleft=(self.x,self.y)
        if self.invinc_timer > 0: self.invinc_timer -= 1
    def draw(self):
        pygame.draw.rect(screen,GREEN,self.rect)
        pygame.draw.rect(screen,WHITE,self.rect,2)
        screen.blit(small_font.render("PJ",True,WHITE),(self.x+10,self.y+10))
class Yoshi:
    def __init__(self,x,y):
        self.x=x; self.y=y; self.w,self.h=60,40
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def draw(self):
        pygame.draw.ellipse(screen,GREEN,self.rect)
        pygame.draw.rect(screen,WHITE,self.rect,2)
        pygame.draw.rect(screen,RED,(self.x+20,self.y-20,20,20))
class Mario:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.w,self.h=30,40; self.timer=0
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self): self.timer+=1
    def draw(self):
        pygame.draw.rect(screen,RED,(self.x,self.y,self.w,10))
        pygame.draw.rect(screen,BLUE,(self.x+10,self.y+10,self.w,20))
        pygame.draw.rect(screen,ORANGE,(self.x+5,self.y+30,20,10))
        screen.blit(small_font.render("M",True,WHITE),(self.x+10,self.y+5))
class EggBullet:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.w,self.h=8,12; self.speed=12
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self):
        self.y-=self.speed; self.rect.y=self.y
    def draw(self): pygame.draw.ellipse(screen,YELLOW,self.rect)
class EnemyBullet:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.w,self.h=8,12; self.speed=8
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self):
        self.y+=self.speed; self.rect.y=self.y
    def draw(self): pygame.draw.ellipse(screen,RED,self.rect)
class Enemy:
    def __init__(self,level,etype="koopa"):
        self.etype=etype
        self.angle = 0  # For wavy movement
        etypes_info = {
            "koopa": {"w":40, "h":40, "color":BLUE, "health":1+level//2, "speed":random.randint(2+level,6+level), "shoot_prob":0.0, "wavy":False},
            "boshi": {"w":50, "h":35, "color":PURPLE, "health":2+level//3, "speed":random.randint(2+level,6+level), "shoot_prob":0.01, "wavy":False},
            "goomba": {"w":35, "h":35, "color":BROWN, "health":1, "speed":3+level//2, "shoot_prob":0.0, "wavy":False},
            "paratroopa": {"w":40, "h":40, "color":GREEN, "health":2, "speed":2+level//3, "shoot_prob":0.005, "wavy":True},
            "bulletbill": {"w":30, "h":20, "color":GRAY, "health":1, "speed":8+level, "shoot_prob":0.0, "wavy":False},
            "cheepcheep": {"w":30, "h":25, "color":RED, "health":1, "speed":4+level//2, "shoot_prob":0.0, "wavy":True},
            "bloober": {"w":35, "h":35, "color":BLUE, "health":2, "speed":3, "shoot_prob":0.0, "wavy":True},
            "spiny": {"w":30, "h":30, "color":RED, "health":3, "speed":4, "shoot_prob":0.0, "wavy":False},
            "bobomb": {"w":25, "h":25, "color":BLACK, "health":1, "speed":5, "shoot_prob":0.0, "wavy":False},
            # Bosses
            "lemmy": {"w":80, "h":80, "color":ORANGE, "health":20+level*5, "speed":1, "shoot_prob":0.05, "wavy":True},
            "ludwig": {"w":80, "h":80, "color":BLUE, "health":25+level*5, "speed":1, "shoot_prob":0.05, "wavy":False},
            "wendy": {"w":80, "h":80, "color":RED, "health":20+level*5, "speed":1, "shoot_prob":0.04, "wavy":True},
            "larry": {"w":80, "h":80, "color":GREEN, "health":22+level*5, "speed":1, "shoot_prob":0.05, "wavy":True},
            "morton": {"w":80, "h":80, "color":GRAY, "health":30+level*5, "speed":1, "shoot_prob":0.03, "wavy":False},
            "iggy": {"w":80, "h":80, "color":YELLOW, "health":25+level*5, "speed":1, "shoot_prob":0.05, "wavy":True},
            "roy": {"w":80, "h":80, "color":PURPLE, "health":28+level*5, "speed":1, "shoot_prob":0.04, "wavy":False},
            "magikoopa": {"w":90, "h":90, "color":BLUE, "health":35+level*5, "speed":1, "shoot_prob":0.06, "wavy":True},
            "bigboo": {"w":100, "h":100, "color":WHITE, "health":40+level*5, "speed":1, "shoot_prob":0.03, "wavy":True},
            "charginchuck": {"w":80, "h":80, "color":GREEN, "health":30+level*5, "speed":2, "shoot_prob":0.05, "wavy":False},
            "koopatroopa_boss": {"w":90, "h":90, "color":GREEN, "health":35+level*5, "speed":1, "shoot_prob":0.04, "wavy":True},
            "bowser": {"w":120, "h":120, "color":RED, "health":50+level*10, "speed":1, "shoot_prob":0.07, "wavy":True},
        }
        info = etypes_info.get(etype, etypes_info["koopa"])
        self.w, self.h = info["w"], info["h"]
        self.color = info["color"]
        self.health = info["health"]
        self.speed = info["speed"]
        self.shoot_prob = info["shoot_prob"]
        self.wavy = info["wavy"]
        self.x=random.randint(0,SCREEN_W-self.w)
        self.y=-self.h
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self, enemy_bullets):
        self.y+=self.speed
        if self.wavy:
            self.angle += 0.1
            self.x += math.sin(self.angle) * 2
            if self.x < 0 or self.x > SCREEN_W - self.w:
                self.x = max(0, min(SCREEN_W - self.w, self.x))
        else:
            self.x+=random.randint(-2,2) if self.etype not in ["koopa", "goomba", "bulletbill"] else 0
        self.rect.topleft=(self.x,self.y)
        if random.random() < self.shoot_prob:
            enemy_bullets.append(EnemyBullet(self.x + self.w//2, self.y + self.h))
    def draw(self):
        pygame.draw.rect(screen,self.color,self.rect)
        pygame.draw.rect(screen,WHITE,self.rect,2)
        label = self.etype[0].upper() if len(self.etype) > 1 else self.etype.upper()
        screen.blit(small_font.render(label,True,WHITE),(self.x+self.w//4,self.y+self.h//4))
class PowerUp:
    def __init__(self,x,y,ptype="egg"):
        self.x,self.y=x,y; self.ptype=ptype; self.w=self.h=20; self.speed=3
        self.rect=pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self): self.y+=self.speed; self.rect.y=self.y
    def draw(self):
        colors = {"egg": YELLOW, "flower": ORANGE, "mushroom": RED, "star": YELLOW, "coin": YELLOW}
        color = colors.get(self.ptype, YELLOW)
        pygame.draw.circle(screen,color,(self.x+10,self.y+10),10)
# ───────── MAIN GAME ─────────
def main():
    fx=WaWaFX(screen)
    punjedi=PunJedi(); yoshi=Yoshi(punjedi.x-10,punjedi.y+40)
    mario=None; bullets=[]; enemy_bullets=[]; enemies=[]; powerups=[]
    score=0; level=1; max_levels=12; wave_count=0
    enemies_per_wave=5+level*2; boss_active=False
    level_names = ["Grass Land", "Mushroom Land", "Pipe Island", "Crescent Coast", "Spirit Mountain", "Grand Bridge", 
                   "Float Castle I", "Cornice Cave", "Ghost Mansion", "Float Castle II", "Dark Sea", "Bowser's Castle"]
    koopalings = ["lemmy", "ludwig", "wendy", "larry", "morton", "iggy", "roy", "magikoopa", "bigboo", "charginchuck", "koopatroopa_boss", "bowser"]
    enemy_types = ["koopa", "boshi", "goomba", "paratroopa", "bulletbill", "cheepcheep", "bloober", "spiny", "bobomb"]
    game_over=False; running=True
    print("Wa Wa FX engine online. Dino-rails engaging… Enhanced with Yoshi's Safari elements.")
    while running:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type==pygame.QUIT:running=False
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_SPACE and not game_over:
                    for _ in range(1+level//3):
                        offset=random.randint(-10,10)
                        bullets.append(EggBullet(punjedi.x+punjedi.w//2+offset,punjedi.y))
                if e.key==pygame.K_r and game_over:return main()
        keys=pygame.key.get_pressed()
        if not game_over:
            punjedi.update(keys); yoshi.x=punjedi.x-10; yoshi.rect.x=yoshi.x
            # Enemy spawning
            if not boss_active:
                enemy_timer = enemy_timer + 1 if 'enemy_timer' in locals() else 1
                if enemy_timer>60-max(5*level,10):
                    if len(enemies)<enemies_per_wave:
                        et = random.choice(enemy_types[:2 + level//2]) if random.random() < 0.9 else "boshi"
                        enemies.append(Enemy(level,et))
                    enemy_timer=0
            # Power-up spawning
            power_timer = power_timer + 1 if 'power_timer' in locals() else 1
            if power_timer>300 and random.random()<0.05:
                pt = random.choice(["egg", "flower", "mushroom", "star", "coin"])
                powerups.append(PowerUp(random.randint(0,SCREEN_W-20),-20,pt))
                power_timer=0
            # Mario spawn chance
            if mario is None and random.random()<0.005*level:
                mario=Mario(punjedi.x+50,punjedi.y)
            # Update bullets
            for b in bullets[:]:
                b.update()
                if b.y<0: bullets.remove(b)
            for eb in enemy_bullets[:]:
                eb.update()
                if eb.y > SCREEN_H: enemy_bullets.remove(eb)
                elif eb.rect.colliderect(punjedi.rect) and punjedi.invinc_timer <= 0:
                    punjedi.health -= 1
                    enemy_bullets.remove(eb)
                    if punjedi.health <= 0: game_over = True
            # Update enemies
            for en in enemies[:]:
                en.update(enemy_bullets)
                if en.y>SCREEN_H:
                    enemies.remove(en); game_over=True
                if en.rect.colliderect(punjedi.rect) and punjedi.invinc_timer <= 0:
                    punjedi.health -= 1
                    enemies.remove(en)
                    if punjedi.health <= 0: game_over = True
                for b in bullets[:]:
                    if b.rect.colliderect(en.rect):
                        bullets.remove(b); en.health-=1
                        if en.health<=0:
                            enemies.remove(en); score+=10*level
                            if random.random()<0.1:
                                powerups.append(PowerUp(en.x,en.y,"egg"))
                            if random.random()<0.3:
                                powerups.append(PowerUp(en.x,en.y,"coin"))
                            if "boss" in en.etype or en.etype in koopalings:
                                boss_active = False
                        break
            # Power-up updates
            for p in powerups[:]:
                p.update()
                if p.y>SCREEN_H: powerups.remove(p)
                elif p.rect.colliderect(punjedi.rect):
                    powerups.remove(p); score+=20
                    if p.ptype=="flower": mario=Mario(punjedi.x+50,punjedi.y)
                    elif p.ptype=="mushroom": punjedi.health = min(punjedi.health + 1, 5)
                    elif p.ptype=="star": punjedi.invinc_timer = 300
                    elif p.ptype=="coin": score += 50
            # Mario update
            if mario:
                mario.update()
                mario.x = punjedi.x + 50; mario.y = punjedi.y; mario.rect.topleft = (mario.x, mario.y)
                if random.random()<0.02:
                    bullets.append(EggBullet(mario.x+mario.w//2,mario.y))
                if mario.timer>300: mario=None
            # Wave and boss logic
            if len(enemies)==0 and not boss_active:
                wave_count+=1
                if wave_count >= 3*level:
                    boss_active = True
                    boss_etype = koopalings[level-1]
                    enemies.append(Enemy(level, boss_etype))
                elif wave_count > 3*level:
                    level+=1; wave_count=0; boss_active=False
                    enemies_per_wave=5+level*2; score+=100*level
                    if level>max_levels: game_over=True
        # ───────── DRAW ─────────
        screen.fill(BLACK)
        fx.draw_floor() # Mode 7-like rail
        punjedi.draw(); yoshi.draw()
        if mario:mario.draw()
        for b in bullets:b.draw()
        for eb in enemy_bullets: eb.draw()
        for en in enemies:en.draw()
        for p in powerups:p.draw()
        fx.crt_tint() # slight CRT feel
        screen.blit(font.render(f"Score: {score}",True,WHITE),(10,10))
        screen.blit(small_font.render(f"Level: {level}/{max_levels} - {level_names[level-1]}",True,YELLOW),(10,50))
        screen.blit(small_font.render(f"Health: {punjedi.health}",True,RED),(10,80))
        if game_over:
            msg="Safari Conquered!" if level>max_levels else "Shell-Shocked!"
            c=GREEN if level>max_levels else RED
            screen.blit(font.render(f"{msg} Score:{score}",True,c),
                        (SCREEN_W//2-180,SCREEN_H//2-20))
            screen.blit(small_font.render("Press R to Raid Again",True,WHITE),
                        (SCREEN_W//2-100,SCREEN_H//2+30))
        pygame.display.flip()
    pygame.quit(); sys.exit()
if __name__=="__main__":
    main()
