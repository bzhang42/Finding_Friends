import logging
import numpy as np
from abc import ABCMeta, abstractmethod

class Mechanism(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def play(self, players, num_friends, levels, king, cap):
        pass


class Baseline_Mechanism(Mechanism):
    def __init__(self, p):
        self.p = p

    def play(self, players, num_friends, levels, king, cap):
        friends = players[king].pick_friends(num_friends, levels, cap)

        if np.random.random() < self.p:
            levels[king] += 1
            for friend in friends:
                levels[friend] += 1

        return levels


class Skill_Mechanism(Mechanism):
    def __init__(self, skill_levels):
        self.skill_levels = skill_levels

    def play(self, players, num_friends, levels, king, cap):
        friends = players[king].pick_friends(num_friends, levels, cap, self.skill_levels)

        p = (self.skill_levels[king] + np.sum([self.skill_levels[friend] for friend in friends])) / np.sum(self.skill_levels)

        if np.random.random() < p:
            levels[king] += 1
            for friend in friends:
                levels[friend] += 1

        return levels