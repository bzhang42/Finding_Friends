import logging
import numpy as np
from abc import ABCMeta, abstractmethod

class Mechanism(object):
    __metaclass__ = ABCMeta

    def __init__(self, num_players):
        """
        The mechanism queries actions from players and then determines who wins given the current set of levels

        Parameters
        ----------
        num_players : int
            The number of players in this mechanism
        """
        self.num_players = num_players

    def rotate_levels(self, levels, n):
        """
        Rotate the levels so that index n becomes index 0, for ease of feeding to agents
            ex. n = 1, levels = [0, 1, 2, 3] returns [1, 2, 3, 0]
            ex. n = -1, levels = [0, 1, 2, 3] returns [3, 0, 1, 2]

        Parameters
        ----------
        levels : list(int)
            The levels of all players by original index
        n : int
            The index to shift by, can be positive or negative

        Returns
        -------
        A rotated list of levels with index n at index 0
        """
        return levels[n:] + levels[:n]

    @abstractmethod
    def play(self, player, levels, cap):
        '''
        The main part of the mechanism which determines underlying logic for increasing levels

        Parameters
        ----------
        player : Agent
            The player whose turn it is to perform an action
        levels : list(int)
            The levels of all players currently
        cap : int
            The max level cap

        Returns
        -------
        The new levels that result from the player's action and the mechanism's logic
        '''
        pass

    @abstractmethod
    def step(self, levels, king, friend):
        pass

    @abstractmethod
    def input_dim(self):
        '''
        Return the number of dimensions in the required input vector
        '''
        pass

    @abstractmethod
    def output_dim(self):
        '''
        Return the number of dimensions in the required output vector
        '''
        pass

class Baseline_Mechanism(Mechanism):
    def __init__(self, num_players, p):
        '''
        A mechanism which levels up the king and chosen friend with probability p

        Parameters
        ----------
        p : float
            The probability of the selected pair leveling up successfully
        '''
        super(Baseline_Mechanism, self).__init__(num_players)
        self.p = p

    def play(self, player, levels, cap):
        # Let the player who is king pick the friend
        friend = player.pick_friends(levels, cap)
        assert(friend != player.id)

        # Sample and increase levels
        if np.random.random() < self.p:
            levels[player.id] += 1
            levels[friend] += 1

        return levels

    def step(self, levels, king, friend):
        if np.random.random() < self.p:
            levels[king] += 1
            levels[friend] += 1

        return levels

    def input_dim(self):
        # The only dimensions required are levels of players and cap
        return self.num_players + 1

    def output_dim(self):
        # The only dimensions required are probabilities of selecting each player as the friend
        return self.num_players - 1

class Skill_Mechanism(Mechanism):
    def __init__(self, num_players, skill_levels):
        '''
        A mechanism which levels up the players based on their combined skill levels

        Parameters
        ----------
        num_players : int
            The number of players in the game
        skill_levels : list(int)
            The relative skill levels of the players
        '''
        super(Skill_Mechanism, self).__init__(num_players)
        self.skill_levels = skill_levels

    def play(self, player, levels, cap):
        # Let the player who is king pick the friend, accounting for skill levels now
        friend = player.pick_friends(levels, cap, self.skill_levels)

        # The probability of leveling up is proportional to the sum of the skills of the players in the kingship
        p = (self.skill_levels[player.id] + self.skill_levels[friend]) / np.sum(self.skill_levels)

        if np.random.random() < p:
            levels[player.id] += 1
            levels[friend] += 1

        return levels

    def step(self, levels, king, friend):
        p = (self.skill_levels[king] + self.skill_levels[friend]) / np.sum(self.skill_levels)

        if np.random.random() < p:
            levels[king] += 1
            levels[friend] += 1

        return levels

    def input_dim(self):
        # Input now has to include the levels and skills of all players, along with max level cap
        return self.num_players + len(self.skill_levels) + 1

    def output_dim(self):
        # Output is still the probability of including each player in the kingship
        return self.num_players - 1