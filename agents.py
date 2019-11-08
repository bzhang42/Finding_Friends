import logging
import numpy as np
from abc import ABCMeta, abstractmethod

class Agent(object):
    __metaclass__ = ABCMeta

    def __init__(self, id, level):
        self.id = id
        self.level = level

    @abstractmethod
    def pick_friends(self, num_friends, levels, cap, skill_levels=None):
        pass


class Basic_Agent(Agent):
    def pick_friends(self, num_friends, levels, cap, skill_levels=None):
        candidates = [i for i in range(len(levels))]
        candidates.pop(self.id)

        return np.random.choice(candidates, size=num_friends, replace=False)


class Lowest_Level_Agent(Agent):
    def pick_friends(self, num_friends, levels, cap, skill_levels=None):
        candidates = list(zip([i for i in range(len(levels))], levels))
        candidates.pop(self.id)

        candidates = sorted(candidates, key=lambda t: t[1])

        friends = [candidates[i][0] for i in range(num_friends)]
        return friends