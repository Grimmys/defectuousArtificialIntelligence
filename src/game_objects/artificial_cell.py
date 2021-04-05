
import pygame

from src.configuration import TWEAKING_MODE, MOVEMENT_FRAMES, STAY_FRAMES, TELEPORT_FRAMES
from src.game_objects.action import Action
from src.game_objects.entity import Entity


class ArtificialCell(Entity):
    CELL_IMAGE = pygame.image.load("imgs/round_cell.png")

    def __init__(self, artificial_engine, is_the_intruder=False):
        super().__init__(artificial_engine.compute_size())

        self.artificial_engine = artificial_engine
        self.is_intruder = is_the_intruder

        cell_resized = pygame.transform.scale(ArtificialCell.CELL_IMAGE, self.rect.size)
        self.image.blit(cell_resized, (0, 0))
        color_filter = pygame.Surface(self.rect.size).convert_alpha()
        color_filter.fill(self.artificial_engine.compute_color())
        self.image.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.teleport_cross = pygame.transform.scale(pygame.image.load("imgs/teleportation.png"), self.rect.size)
        self.teleport_cross.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.teleport_cross_position = None

        if TWEAKING_MODE and self.is_intruder:
            indicator = pygame.Surface((self.rect.width // 5, self.rect.height // 5))
            indicator.fill(pygame.Color("white"))
            self.image.blit(indicator, (self.rect.width // 2.5, self.rect.height // 2.5))

    def start_move(self, other_entities, bounds):
        initial_rect = self.rect.copy()
        direction = self.artificial_engine.compute_movement_direction()
        self.move(direction)
        if self.position_is_valid(other_entities, bounds):
            self.current_action = Action(Action.action_types.MOVE, MOVEMENT_FRAMES, move_direction=direction)
            return
        self.rect = initial_rect.copy()

    def start_teleport(self, other_entities, bounds):
        initial_rect = self.rect.copy()
        max_attemps_to_teleport = 5
        nb_tries = 0
        while nb_tries < max_attemps_to_teleport:
            endpoint = self.artificial_engine.compute_teleport_endpoint(self.rect)
            teleport_entity = Entity(self.rect.size, endpoint)
            other_entities.add(teleport_entity)
            if teleport_entity.position_is_valid(other_entities, bounds):
                self.current_action = Action(Action.action_types.TELEPORT, TELEPORT_FRAMES, endpoint=endpoint)
                break
            other_entities.remove(teleport_entity)
            self.rect = initial_rect.copy()
            nb_tries += 1

    def start_new_action(self, other_entities, bounds):
        action = self.artificial_engine.compute_action_decision()
        if action is Action.action_types.MOVE:
            self.start_move(other_entities, bounds)
        elif action is Action.action_types.TELEPORT:
            self.start_teleport(other_entities, bounds)
        elif action is Action.action_types.NOTHING:
            self.current_action = Action(action, STAY_FRAMES)

    def continue_current_action(self, other_entities, bounds):
        if self.current_action.nature is Action.action_types.MOVE:
            if self.current_action.progress():
                self.current_action = None
                return
            initial_rect = self.rect.copy()
            self.move(self.current_action.move_direction)
            if not self.position_is_valid(other_entities, bounds):
                self.rect = initial_rect
                self.current_action = None
        elif self.current_action.nature is Action.action_types.TELEPORT:
            if self.current_action.progress():
                self.current_action = None
                return
            if self.current_action.current_frame == 1:
                self.teleport_cross_position = self.rect.x, self.rect.y
            elif self.current_action.current_frame == self.current_action.nb_frames // 2:
                self.teleport_cross_position = self.current_action.endpoint
            elif self.current_action.current_frame == self.current_action.nb_frames - 1:
                self.teleport_cross_position = None
                self.rect.x, self.rect.y = self.current_action.endpoint
        elif self.current_action.nature is Action.action_types.NOTHING:
            if self.current_action.progress():
                self.current_action = None

    def update(self, other_entities, bounds):
        if self.current_action:
            self.continue_current_action(other_entities, bounds)
        else:
            self.start_new_action(other_entities, bounds)

    def draw(self, screen):
        super().draw(screen)
        if self.teleport_cross_position:
            screen.blit(self.teleport_cross, self.teleport_cross_position)

