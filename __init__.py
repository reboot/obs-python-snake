import os
import sys
import time
import threading
import libobs
import pygame
import random

class EventProcessor(threading.Thread):

    def __init__(self, source):
        threading.Thread.__init__(self)

        self.source = source

        self.stopped = False

    def run(self):
        source = self.source
        joystick = pygame.joystick.Joystick(0)

        while not self.stopped:
            event = pygame.event.wait()
            if event.type == pygame.JOYAXISMOTION:
                if joystick.get_axis(0) < -0.8 and source.movement != SnakeSource.RIGHT:
                    source.direction = SnakeSource.LEFT
                if joystick.get_axis(0) > 0.8 and source.movement != SnakeSource.LEFT:
                    source.direction = SnakeSource.RIGHT
                if joystick.get_axis(1) < -0.8 and source.movement != SnakeSource.DOWN:
                    source.direction = SnakeSource.UP
                if joystick.get_axis(1) > 0.8 and source.movement != SnakeSource.UP:
                    source.direction = SnakeSource.DOWN

    def stop(self):
        self.stopped = True

class SnakeSource():

    RIGHT = 0
    LEFT = 1
    DOWN = 2
    UP = 3

    def __init__(self):
        super()

        self.tile_size = 8

        self.width = 60
        self.height = 32
        self.bpp = 4

        self.initGame()

        pixelbuffer = bytearray(self.tile_size * self.tile_size * self.bpp)

        libobs.obs_enter_graphics()
        self.SetColour(pixelbuffer, 255, 96, 96, 192)
        self.snake_texture = libobs.gs_texture_create(self.tile_size, self.tile_size, libobs.GS_BGRA, 1, pixelbuffer, libobs.GS_DYNAMIC)
        self.SetColour(pixelbuffer, 96, 255, 96, 192)
        self.block_texture = libobs.gs_texture_create(self.tile_size, self.tile_size, libobs.GS_BGRA, 1, pixelbuffer, libobs.GS_DYNAMIC)
        libobs.obs_leave_graphics()

        self.tick = time.time()

        self.eventProcessor = EventProcessor(self)
        self.eventProcessor.start()

    @staticmethod
    def create(settings, source):
        return SnakeSource()

    def initGame(self):
        self.snake = [ [15, 7], [14, 7], [13, 7], [12, 7], [11, 7], [10, 7] ]
        self.blocks = [ ]
        self.addBlock()
        self.addBlock()
        self.addBlock()
        self.movement = SnakeSource.RIGHT
        self.direction = None

    def addBlock(self):
        while True:
            newblock = [ random.randint(0, self.width - 1), random.randint(0, self.height - 1) ]
            if newblock in self.snake:
                continue
            if newblock in self.blocks:
                continue;
            self.blocks.insert(0, newblock)
            break

    def render(self, effect):
        t = time.time()
        if (t - self.tick > 0.05):
            gameOver = False
            if self.direction != None:
                self.movement = self.direction
            x = self.snake[0][0] + (self.movement == SnakeSource.RIGHT and 1 or self.movement == SnakeSource.LEFT and -1)
            if x < 0 or x >= self.width:
                gameOver = True
            y = self.snake[0][1] + (self.movement == SnakeSource.DOWN and 1 or self.movement == SnakeSource.UP and -1)
            if y < 0 or y >= self.height:
                gameOver = True
            pos = [x, y]
            if pos in self.snake:
                gameOver = True
            elif pos in self.blocks:
                self.blocks.remove(pos)
                self.addBlock()
            else:
                self.snake.pop()
            if gameOver:
                self.initGame()
            else:
                self.snake.insert(0, pos)
            self.tick = t

        libobs.obs_enter_graphics()
        libobs.gs_reset_blend_state()

        libobs.gs_effect_set_texture(libobs.gs_effect_get_param_by_name(effect, "image"), self.snake_texture)
        for part in self.snake:
            libobs.gs_matrix_push();
            libobs.gs_matrix_translate3f(part[0] * self.tile_size, part[1] * self.tile_size, 0.0);
            libobs.gs_draw_sprite(self.snake_texture, 0, 0, 0);
            libobs.gs_matrix_pop();

        libobs.gs_effect_set_texture(libobs.gs_effect_get_param_by_name(effect, "image"), self.block_texture)
        for block in self.blocks:
            libobs.gs_matrix_push();
            libobs.gs_matrix_translate3f(block[0] * self.tile_size, block[1] * self.tile_size, 0.0);
            libobs.gs_draw_sprite(self.block_texture, 0, 0, 0);
            libobs.gs_matrix_pop();

        libobs.obs_leave_graphics()
        pass

    def tick(self):
        pass

    def get_width(self):
        return self.width * self.tile_size

    def get_height(self):
        return self.height * self.tile_size

    def destroy(self):
        libobs.obs_enter_graphics()
        libobs.gs_texture_destroy(self.snake_texture)
        libobs.gs_texture_destroy(self.block_texture)
        libobs.obs_leave_graphics()

        self.eventProcessor.stop()
        pygame.event.post(pygame.event.Event(pygame.USEREVENT))
        self.eventProcessor.join()

    def SetColour(self, pixelbuffer, r, g, b, a):
        for i in range(0, self.tile_size * self.tile_size * self.bpp, self.bpp):
            pixelbuffer[i] = b  #blue
            pixelbuffer[i + 1] = g #green
            pixelbuffer[i + 2] = r #red
            pixelbuffer[i + 3] = a #alpha

def register():
    pygame.init()
    pygame.joystick.init()

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    src = libobs.Source()
    src.create = SnakeSource.create
    src.video_render = SnakeSource.render
    src.video_tick = SnakeSource.tick
    src.get_height = SnakeSource.get_height
    src.get_width = SnakeSource.get_width
    src.destroy = SnakeSource.destroy
    libobs.obs_register_source(src)
    libobs.log("Registered Snake")
