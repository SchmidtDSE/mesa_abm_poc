from enum import IntEnum


class LifeStage(IntEnum):
    DEAD = 0
    SEED = 1
    SEEDLING = 2
    JUVENILE = 3
    ADULT = 4
    BREEDING = 5

    def __str__(self):
        return self.name
