import pygame
import pickle
from os import path

pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption('Platformer')

#define game variables
tile_size=50
game_over=0
main_menu = True
level = 1
max_levels = 3

#load images
sun_img = pygame.image.load('./img/sun.png')
bg_img = pygame.image.load('./img/sky.png')
restart_img = pygame.image.load('./img/restart_btn.png')
start_img = pygame.image.load('./img/start_btn.png')
exit_img = pygame.image.load('./img/exit_btn.png')

def draw_grid():
    for line in range(0, 20):
        pygame.draw.line(screen, (255, 255, 255), (0, line * tile_size), (screen_width, line * tile_size))
        pygame.draw.line(screen, (255, 255, 255), (line * tile_size, 0), (line * tile_size, screen_height))

#function to reset level
def reset_level(level):
    player.reset(100,screen_height - 130)#reset player position
    blob_group.empty()#empty all the sprtie and enemy groups to prepare for new level
    lava_group.empty()
    exit_group.empty()

    #load in level data from files and create world
    if path.exists(f'level{level}_data'): #check if the level file exists in directory
        pickle_in = open(f'level{level}_data','rb')#rb stand for read binary, aka the data type of the level_data's
        world_data = pickle.load(pickle_in)
    world = World(world_data)

    return world


class Button():
    def __init__ (self, x,y,image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        #get mouse position
        pos = pygame.mouse.get_pos()

        #check mouseover and clicked conditions
        if self.rect.collidepoint(pos):#checks for collision between point (the mouse is a point) and rect of the button
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False: #[0] checks for left click, and if left click is clicked then returns 1
                #self.clicked == False is so that only one left click is detected, or else if left click is held down then it counts all those
                action = True#we clicked the button
                self.clicked = True
        if pygame.mouse.get_pressed()[0] == 0: #if left click button is released
            self.clicked = False #set back to False
        #draw button
        screen.blit(self.image, self.rect)
        return action

class Player():
    def __init__ (self,x,y):
        self.reset(x,y)
    
    def update(self, game_over):

        dx = 0
        dy =0
        walk_cooldown = 5

        if game_over == 0:
            #get keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False: #if space button isnt pressed/held down
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1 #adds to animation counter
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1 
            if key[pygame.K_RIGHT]==False and key[pygame.K_LEFT]==False:
                self.counter=0
                self.index=0 #if not moving, use only first png
                if self.direction == 1:#these handle idle animation, if hes facing left or right
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]
            
            #handle animation
            if self.counter > walk_cooldown: #only goes to next png of the animation after 5 iterations of update() cus walk_cooldown = 5, so slows down animation speed
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):#aka if we get to the 4th png for animation, put the index back to 0 to reset animation
                    self.index = 0
                if self.direction == 1: #loads in the flipped or regular imgs based on which direction hes going
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]
            

            # add gravity
            self.vel_y += 1 #always adds 1 so this is force of gravity always present
            if self.vel_y > 10:
                self.vel_y = 10 #doesn't allow velocity to exceed 10
            dy += self.vel_y
            
            #check for collision with world
            self.in_air = True
            for tile in world.tile_list:
                #predict/check for collision in x-direction
                if tile[1].colliderect(self.rect.x + dx,self.rect.y, self.width, self.height):
                    dx=0

                #predict/check for collision in y-direction
                if tile[1].colliderect(self.rect.x,self.rect.y + dy, self.width, self.height):
                    #check if below the ground (e.g. jumping and hit bottom of ground)
                    if self.vel_y < 0: #aka if moving upwards while hitting bottom of ground
                        dy = tile[1].bottom - self.rect.top #sets the amount player moves in y direction to max, aka current distance between player and block before he collides
                        self.vel_y = 0 #puts his velocity to 0
                    #check if above ground e.g. falling
                    elif self.vel_y >= 0: 
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False #player is on top of something

            #check for collision with enemies

            #checks for collision with built in sprite methods, e.g. checks for collision between self(player) and blob_group
            if pygame.sprite.spritecollide(self, blob_group, False):#keep False, or else deletes those enemies/things
                game_over = -1
            if pygame.sprite.spritecollide(self, lava_group, False):#keep False, or else deletes those enemies/things
                game_over = -1
            if pygame.sprite.spritecollide(self, exit_group, False):#keep False, or else deletes those enemies/things
                game_over = 1

            #update player coordinates
            self.rect.x += dx
            self.rect.y += dy

        #if dead
        elif game_over == -1: 
            self.image = self.dead_image
            #if self.rect.y > 200:
            self.rect.y -= 5 #decrease by 5 pixels each time we update, so ghost/image moves upwards

        #draws player on screen
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255,255,255), self.rect, 2)#draw hitbox

        return game_over

    def reset(self,x,y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0 #handles speed of animation

        #below for loop just initializes/loads in our 4 pngs for the animation, doesnt actually update it
        for num in range (1,5):#for loop goes from 1 to 4 cus we have 4 pngs that make up the walk animation
            img_right = pygame.image.load(f'./img/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40,80))
            img_left = pygame.transform.flip(img_right, True, False)#true for flip img in x-axis, false for y-axis
            self.images_right.append(img_right)#adds the current img_right to our list of images_right
            self.images_left.append(img_left)
        
        self.dead_image = pygame.image.load('./img/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0 #y-axis velocity e.g. for jumping
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    
    def __init__(self, data):
        self.tile_list = []

        #load images
        dirt_img = pygame.image.load('img/dirt.png')
        grass_img = pygame.image.load('img/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))#makes img a certain size (tile_size by tile_square here)
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect) #creates a rectangle with important info of tile
                    self.tile_list.append(tile)#adds info from rectangle into list
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    #below line adjusts where the blob shows up on screen, + 15 px is to make them appear on the ground cus they were too high before
                    blob = Enemy(col_count * tile_size, row_count * tile_size+15)
                    blob_group.add(blob)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size+(tile_size // 2))#its // so we get an int, float would give us error
                    lava_group.add(lava)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size //2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            pygame.draw.rect(screen, (255,255,255), tile[1], 2) #draw hitbox

#pygame.sprite.Sprite class is built in, has good properies that we use
#has a built draw and update method but we can overwrite
class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('./img/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1#change direction of slime after a set period of time
            self.move_counter *= -1 #allows them to move to the left of their origin as well

class Lava(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('./img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size //2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Exit(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('./img/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
"""""
world_data = [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1], 
[1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 2, 2, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 7, 0, 5, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 1], 
[1, 7, 0, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 
[1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 7, 0, 0, 0, 0, 1], 
[1, 0, 2, 0, 0, 7, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 
[1, 0, 0, 2, 0, 0, 4, 0, 0, 0, 0, 3, 0, 0, 3, 0, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 7, 0, 0, 0, 0, 2, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 2, 2, 2, 2, 2, 1], 
[1, 0, 0, 0, 0, 0, 2, 2, 2, 6, 6, 6, 6, 6, 1, 1, 1, 1, 1, 1], 
[1, 0, 0, 0, 0, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 
[1, 0, 0, 0, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 
[1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]
"""""

player = Player(100,screen_height - 130)

#pygame.sprite.Sprite acts like a list, so we initialize an empty sprite list that we can fill in
blob_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#load in level data from files and create world
if path.exists(f'level{level}_data'): #check if the level file exists in directory
    pickle_in = open(f'level{level}_data','rb')#rb stand for read binary, aka the data type of the level_data's
    world_data = pickle.load(pickle_in)
world = World(world_data)

#create buttons
restart_button = Button(screen_width //2 -50, screen_height//2 + 100, restart_img)
start_button = Button(screen_width // 2 -350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)

run = True
#to keep code/game always running (and window doesn't close immediatley), 
# we have this while loop always running until we decide to end the game
while run:

    clock.tick(fps)#controls framerate
    screen.blit(bg_img, (0,0))
    screen.blit(sun_img, (100,100))

    #if in main menu
    if main_menu:
        if exit_button.draw():#returns false or true if button is pressed
            run = False
        if start_button.draw():
            main_menu=False
        
    #if not in main menu, generate world and play game
    else:
        world.draw()

        #stops animation/updating for blob group when gameover
        if game_over == 0:
            blob_group.update()

        blob_group.draw(screen)
        lava_group.draw(screen)
        exit_group.draw(screen)
        game_over = player.update(game_over)
        draw_grid();

        #if player had died
        if game_over == -1:
            if restart_button.draw(): #checks if variable "action" returned is true or false; if true that means button was clicked
                world_data = [] #empties the world_data from current level
                world = reset_level(level) #save the world reset and generated from reset_level
                game_over = 0

        #if player completed level
        if game_over == 1:
            #reset and go to next level
            level += 1
            if level <= max_levels:
                #reset level
                world_data = [] #empties the world_data from current level
                world = reset_level(level) #save the world reset and generated from reset_level
                game_over = 0
            else:
                #restart game
                if restart_button.draw():
                    level = 1
                    world_data = [] #empties the world_data from current level
                    world = reset_level(level) #save the world reset and generated from reset_level
                    game_over = 0

    #event is any input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:#pygame.QUIT means u press close buton on window
            run = False #stops the while loop and quits game

    pygame.display.update()