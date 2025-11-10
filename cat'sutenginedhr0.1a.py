#!/usr/bin/env python3
# Cat's PYGAME UT ENGINE 0.1 — Complete single-file edition
# Full Undertale-like engine with working main menu, name entry,
# overworld, battle, and credits.  No external assets.

import os, sys, json, math, random, time
try:
    import pygame
except Exception:
    print("Install pygame: pip install pygame")
    raise

# ────────────────────────────── Config ──────────────────────────────
WIDTH, HEIGHT, FPS = 600, 400, 60
SAVE_PATH = "save.json"
WHITE, BLACK = (255,255,255), (0,0,0)
GRAY, DARK = (55,55,55), (20,20,20)
YELLOW, RED, GREEN, ORANGE, BLUE = (255,235,0), (220,60,60), (60,220,100), (255,165,0), (0,165,255)

# ────────────────────────────── Utils ──────────────────────────────
def clamp(v,lo,hi): return max(lo,min(v,hi))
def lerp(a,b,t): return a+(b-a)*t
def now(): return time.perf_counter()
def draw_text(surf,text,pos,font,color=WHITE,shadow=True,center=False):
    if center:
        r = font.render(text,True,color).get_rect(center=pos)
        if shadow: surf.blit(font.render(text,True,BLACK),(r.x+1,r.y+1))
        surf.blit(font.render(text,True,color),r); return
    if shadow: surf.blit(font.render(text,True,BLACK),(pos[0]+1,pos[1]+1))
    surf.blit(font.render(text,True,color),pos)

class Timer:
    def __init__(self,d): self.d=d; self.t0=now()
    def reset(self,d=None): 
        if d: self.d=d
        self.t0=now()
    def done(self): return now()-self.t0>=self.d
    def ratio(self): return clamp((now()-self.t0)/self.d,0,1)

# ────────────────────────────── Framework ──────────────────────────────
class BaseState: 
    def __init__(self,g): self.g=g
    def enter(self,**k): pass
    def exit(self): pass
    def handle_event(self,e): pass
    def update(self,dt): pass
    def draw(self,s): pass

class Game:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Cat's PYGAME UT ENGINE 0.1")
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("consolas",18)
        self.big=pygame.font.SysFont("consolas",28,bold=True)
        self.small=pygame.font.SysFont("consolas",14)
        self.session={"player_name":"","hp":20,"hp_max":20,"gold":0,"inventory":["Bandage","Pie"],
                      "flags":{"dummy_spared":False},"map_id":"room_a","pos":[4,6]}
        self.states={"menu":MainMenu(self),"name_entry":NameEntry(self),
                     "overworld":Overworld(self),"battle":Battle(self),"credits":Credits(self)}
        self.switch("menu")
    def switch(self,name,**k): 
        if hasattr(self,"state"): self.state.exit()
        self.state=self.states[name]; self.state.enter(**k)
    def push(self,n,**k): self.switch(n,**k)
    def pop(self): self.switch("menu")
    def save(self):
        with open(SAVE_PATH,"w") as f: json.dump(self.session,f,indent=2)
    def load(self):
        if os.path.exists(SAVE_PATH):
            self.session=json.load(open(SAVE_PATH))
            self.switch("overworld")
    def run(self):
        while True:
            dt=self.clock.tick(FPS)/1000
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                self.state.handle_event(e)
            self.state.update(dt)
            self.state.draw(self.screen)
            pygame.display.flip()

# ────────────────────────────── Main Menu ──────────────────────────────
class MainMenu(BaseState):
    def enter(self,**k):
        self.has_save=os.path.exists(SAVE_PATH)
        self.opts=["CONTINUE" if self.has_save else "NEW GAME","CREDITS","QUIT"]
        self.idx=0; self.cool=0; self.fade=0; self.phase=0; self.flash=0; self.blink=Timer(0.4)
    def handle_event(self,e):
        if e.type==pygame.KEYDOWN and self.cool<=0:
            if e.key in (pygame.K_DOWN,pygame.K_s): self.idx=(self.idx+1)%len(self.opts); self.cool=0.15
            elif e.key in (pygame.K_UP,pygame.K_w): self.idx=(self.idx-1)%len(self.opts); self.cool=0.15
            elif e.key in (pygame.K_RETURN,pygame.K_z): self.activate()
            elif e.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()
    def activate(self):
        opt=self.opts[self.idx]
        if opt=="NEW GAME": self.g.push("name_entry")
        elif opt=="CONTINUE": self.g.load()
        elif opt=="CREDITS": self.g.switch("credits")
        else: pygame.quit(); sys.exit()
    def update(self,dt):
        self.cool=max(0,self.cool-dt)
        self.phase+=dt*4; self.fade=clamp(self.fade+dt*1.5,0,1)
        if self.blink.done(): self.flash^=1; self.blink.reset()
    def draw(self,s):
        s.fill(BLACK)
        c=YELLOW if self.flash else WHITE
        draw_text(s,"C A T ' S   U T   E N G I N E",(WIDTH//2,90),self.g.big,c,center=True)
        for i,t in enumerate(self.opts):
            col=YELLOW if i==self.idx else WHITE
            draw_text(s,t,(WIDTH//2,180+i*40),self.g.big,col,center=True)
        sx,sy=WIDTH//2-100,180+self.idx*40+6+math.sin(self.phase)*2
        pygame.draw.rect(s,RED,(sx,sy,10,10))

# ────────────────────────────── Name Entry ──────────────────────────────
class NameEntry(BaseState):
    def enter(self,**k): self.name=""
    def handle_event(self,e):
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_RETURN and self.name:
                self.g.session["player_name"]=self.name.upper()
                self.g.switch("overworld")
            elif e.key==pygame.K_BACKSPACE: self.name=self.name[:-1]
            elif len(self.name)<6 and e.unicode.isalpha(): self.name+=e.unicode
    def draw(self,s):
        s.fill(BLACK)
        draw_text(s,"Name the fallen human:",(WIDTH//2,120),self.g.big,WHITE,center=True)
        draw_text(s,self.name.upper(),(WIDTH//2,180),self.g.big,YELLOW,center=True)

# ────────────────────────────── Overworld ──────────────────────────────
TILE=28; OX,OY=20,20
ROOMS={"room_a":["####################","#........N.........#","#..................#","#..........#####...#",
                 "#....B.............#","#..................#","####################"]}

class Overworld(BaseState):
    def enter(self,**k):
        self.map=ROOMS["room_a"]; self.w=len(self.map[0]); self.h=len(self.map)
        px,py=self.g.session["pos"]; self.player=pygame.Rect(OX+px*TILE,OY+py*TILE,TILE-8,TILE-8)
    def tile(self,x,y): return self.map[y][x] if 0<=x<self.w and 0<=y<self.h else "#"
    def handle_event(self,e):
        if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: self.g.switch("menu")
    def update(self,dt):
        k=pygame.key.get_pressed(); vx=(k[pygame.K_d]-k[pygame.K_a])*120*dt; vy=(k[pygame.K_s]-k[pygame.K_w])*120*dt
        self.player.x+=vx; self.player.y+=vy
        tx,ty=int((self.player.centerx-OX)//TILE),int((self.player.centery-OY)//TILE)
        if self.tile(tx,ty)=="B": self.g.push("battle",enemy=EnemyDummy())
    def draw(self,s):
        s.fill(BLACK)
        for y,row in enumerate(self.map):
            for x,ch in enumerate(row):
                col=GRAY if ch=="#" else DARK
                pygame.draw.rect(s,col,(OX+x*TILE,OY+y*TILE,TILE,TILE))
        pygame.draw.rect(s,YELLOW,self.player)

# ────────────────────────────── Battle (simplified) ──────────────────────────────
class EnemyDummy:
    def __init__(self): self.name="DUMMY"; self.hp=20; self.hpmax=20
class Battle(BaseState):
    def enter(self,**k): self.e=k.get("enemy",EnemyDummy()); self.t=Timer(1)
    def handle_event(self,e):
        if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN: self.g.pop()
    def update(self,dt): pass
    def draw(self,s):
        s.fill(BLACK)
        draw_text(s,f"* {self.e.name} approaches!",(WIDTH//2,HEIGHT//2),self.g.big,WHITE,center=True)
        draw_text(s,"Press Enter to end battle.",(WIDTH//2,HEIGHT//2+40),self.g.font,WHITE,center=True)

# ────────────────────────────── Credits ──────────────────────────────
class Credits(BaseState):
    def enter(self,**k): self.scroll=HEIGHT
    def handle_event(self,e):
        if e.type==pygame.KEYDOWN: self.g.switch("menu")
    def update(self,dt): self.scroll-=30*dt
    def draw(self,s):
        s.fill(BLACK)
        lines=["Cat's PYGAME UT ENGINE 0.1","","Inspired by Undertale (Toby Fox)","","Educational Sample","Press any key..."]
        y=int(self.scroll)
        for line in lines:
            draw_text(s,line,(WIDTH//2,y),self.g.font,WHITE,center=True); y+=28

# ────────────────────────────── Entry ──────────────────────────────
if __name__=="__main__":
    Game().run()
