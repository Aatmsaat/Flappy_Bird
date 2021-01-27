import pygame
import neat
import os
import time
import random
import sys
from threading import Thread
pygame.init()#for sound

BREADTH, HEIGHT = 288, 500
BASE_Y = HEIGHT*.8
PIPE_DIST = BREADTH*.68
PIPE_GAP = HEIGHT*.2
DEATH = False #Bird dies :(
RESTART = 0
START = False #
 

#Window
WIN = pygame.display.set_mode((BREADTH, HEIGHT))#, pygame.SCALED | pygame.FULLSCREEN)


#Text On Screen
pygame.font.init()#initializing font
def textize(text):
	if isinstance(text, int):
		Score = pygame.font.SysFont('Aerial',round(HEIGHT*.08)).render(str(text), True, (255, 223, 0))#golden yellow
		
		WIN.blit(Score, ((BREADTH-Score.get_width())/2, HEIGHT*.1))
	
	else:
		Game_Over = pygame.font.SysFont('Aerial',round(HEIGHT*.1)).render(text, True, (255, 0, 0))#red
		
		WIN.blit(Game_Over, ((BREADTH - Game_Over.get_width())/2, (HEIGHT - Game_Over.get_height())/2))
		

#Images
Load_Image = lambda x: pygame.image.load(os.path.join('imgs',x+'.png')).convert_alpha()

#Background
BG = Load_Image('bg')
BG_Width = BG.get_width()

#Base
BASE = Load_Image('base')
BASE_Width = BASE.get_width()

#Bird
BIRDS = [Load_Image('bird1'), Load_Image('bird2'), Load_Image('bird3'), Load_Image('bird2')]
Brd_Height = BIRDS[0].get_height()
Brd_Width = BIRDS[0].get_width()

#Pipe
PIPE_UP = pygame.transform.flip(Load_Image('pipe'),False, True)
PIPE_DOWN = Load_Image('pipe')
Pipe_Width = PIPE_UP.get_height()


#Sounds
#Load_Sound = lambda x: pygame.mixer.Sound(os.path.join('sounds', x+'.wav'))

#Wings Flap
#FLAP = Load_Sound('flap')#.play

#Hit
#HIT = Load_Sound('hit')#.play

#Point Scoring
#POINT = Load_Sound('point')#.play

#Game End
#END = Load_Sound('game_over')#.play


class BackGround:
	def __init__(self, y):
		self.y = y
		self.vel = .95#background moving Velocity
		self.x1 = 0 #first background position
		self.x2 = BG_Width#second background position
		
	def move(self):
		self.x1 -= self.vel
		self.x2 -= self.vel
		if self.x1 + BG_Width < 0:
			self.x1 = self.x2 + BG_Width
		if self.x2 + BG_Width < 0:
			self.x2 = self.x1+ BG_Width
			
	def draw(self):
		WIN.blit(BG, (self.x1, self.y))
		WIN.blit(BG, (self.x2, self.y))
		

class Pipe:
	def __init__(self):
		self.vel = 5#background moving Velocity
		self.x = BREADTH+10
		self.score = 0
		self.pipes = []
		self.count = 0
	
	def add_pipe(self):
		y = random.randrange(HEIGHT*.06, HEIGHT*.56)
		x=self.x
		self.pipes.append([x, y+PIPE_GAP, y-Pipe_Width, False])
		self.x += PIPE_DIST
		self.count += 1
		
	def is_collide(self,x , y1, y2, PipeDown, PipeUp, bird):
		bird_mask = bird.get_mask()
		up_mask = pygame.mask.from_surface(PipeUp)
		down_mask = pygame.mask.from_surface(PipeDown)
		offset_up = (round(x - bird.x), round(y2 - bird.y))
		offset_down = (round(x - bird.x), round(y1 - bird.y))
		f_down = bird_mask.overlap(down_mask, offset_down)
		f_up = bird_mask.overlap(up_mask,offset_up)
		return f_up or f_down
		
		
		
	def move(self):
		for i in range(self.count):
			self.pipes[i][0] -= self.vel
	
		first_pipe_x = self.pipes[0][0]
		last_pipe_x = self.pipes[-1][0]
		self.x = last_pipe_x+PIPE_DIST	
		if  (first_pipe_x+Pipe_Width < 0):#if total pipes are 4
			self.pipes.pop(0)
			self.add_pipe()
			self.count -= 1
			
	def draw(self, bird):
		global DEATH
		for i in range(self.count):
			x, y1, y2, passed = self.pipes[i]
			WIN.blit(PIPE_DOWN, (x, y1))
			WIN.blit(PIPE_UP, (x, y2))
			if DEATH: continue	
			#if bird lyes b/w pipes
			if bird.BaseTouch:
				DEATH=True
				#END()
			elif (x < (bird.x+Brd_Width) < (x+Pipe_Width)) or (x < bird.x < (x+Pipe_Width)):
				if self.is_collide(x, y1, y2, PIPE_DOWN, PIPE_UP, bird):
					DEATH=True
					#HIT.play()
					time.sleep(.1)
					#END.play()
				#scoring if mid of bird > mid of pipe
				elif not passed and bird.x > x:
					self.score+=1
					self.pipes[i][-1]=True
					#POINT.play()
				#pygame.quit()
				#sys.exit()
		


	
class Base:
	def __init__(self, y):
		self.y = y
		self.vel = 5#base moving Velocity
		self.x1 = 0 #first base position
		self.x2 = BASE_Width#second base position
		
	def move(self):
		self.x1 -= self.vel
		self.x2 -= self.vel
		if self.x1 + BASE_Width < 0:
			self.x1 = self.x2 + BASE_Width
		if self.x2 + BASE_Width < 0:
			self.x2 = self.x1+ BASE_Width
			
	def draw(self):
		WIN.blit(BASE, (self.x1, self.y))
		WIN.blit(BASE, (self.x2, self.y))
		

class Bird:
	global DEATH
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.BaseTouch = False
		self.Index = 0
		self.Tilt_Bird = None
		self.flapped=False
		self.vel = -10.5#bird moving Velocity
		self.maxvel = 12#max velocity
		self.minvel = -10.5#min velocity
		self.g = 1.5 # acceleration
		self.wings = 5#wing's movement velocity
		self.rotacc = -3#rotation acceleration
		self.rotvel = 22#rotation velocity
		self.maxrot = 22#maximum rotation
		self.minrot = -90#minimum rotation
		self.count=0
		
	def move(self):
		if self.y> Brd_Height:
			self.vel = self.minvel
			self.flapped = True
			#FLAP.play()
			
	def get_mask(self):
		return pygame.mask.from_surface(BIRDS[self.Index])
		
		
	def draw_start(self):
		textize('TAP')
		self.count += 1
		self.Index = int(self.count/self.wings)
		if self.Index>3: self.Index=0; self.count=0
		WIN.blit(BIRDS[self.Index], (self.x, self.y))
		
			
	def draw(self):
		global DEATH
		#if not DEATH:
		
		
		#Bird Movemet
		if self.flapped:
			self.flapped=False
			self.rotvel = self.maxrot
		else:
			self.vel = max(min(self.vel + self.g, self.maxvel), self.minvel)
			self.rotvel = min(self.rotvel+self.rotacc, self.maxrot)
		
		GroundBirdDist = BASE_Y - Brd_Height - self.y
		self.y += min(self.vel, GroundBirdDist)
		#Bird Rotation
		self.rotvel = max(self.minrot, self.rotvel)
		if not DEATH:
			self.count += 1
			self.Index = int(self.count/self.wings)
			if self.Index>3: self.Index=0; self.count=0
		#if self.y >= self.GroundTouch:
			#self.rotvel = max(self.minrot, self.rotvel)
		if GroundBirdDist > 0:	
			self.Tilt_Bird = pygame.transform.rotate(BIRDS[self.Index], self.rotvel)
		else: self.BaseTouch = True
		WIN.blit(self.Tilt_Bird, (self.x, self.y))


def All_Draw(bg, pipe, base, bird):
		global DEATH, RESTART, START
		bg.draw()
		pipe.draw(bird)
		base.draw()
		textize(pipe.score)
		if START:
			bird.draw()
		else:
			bird.draw_start()
		if DEATH:
			textize('Game Over')
			if RESTART:
				#Thread(target=animate()).run()
				animate()
		pygame.display.update()
		pygame.time.Clock().tick(35)
	
	

def animate():
	global DEATH, RESTART, START
	RESTART = 0
	BREADTH, HEIGHT = 288, 500
	BASE_Y = HEIGHT*.8
	PIPE_DIST = BREADTH*.68
	PIPE_GAP = HEIGHT*.2
	DEATH = False #Bird dies :(
	START = False #
	bg = BackGround(-80)
	pipe = Pipe()
	for _ in range(4):
		pipe.add_pipe()#make extra pipes
	base = Base(HEIGHT*.8)
	bird = Bird(BREADTH*.2, (HEIGHT-Brd_Height)>>1)
	while True:
		if not DEATH and START:
			bg.move()
			pipe.move()
			base.move()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit(1)
			#if DEATH: continue
			elif event.type  == pygame.MOUSEBUTTONDOWN  or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
				if not START:
					START = True
				elif not DEATH:
					bird.move()
				else:
					RESTART = True
				#bird.x+=10
		All_Draw(bg, pipe, base, bird)

if __name__ == '__main__':
	#animate()
	Thread(target=animate).run()