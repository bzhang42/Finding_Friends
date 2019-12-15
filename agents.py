import logging
import numpy as np
from abc import ABCMeta, abstractmethod

class Agent(object):
    __metaclass__ = ABCMeta

    def __init__(self, id, level):
        '''
        The agent is responsible for selecting actions and accepting rewards from the game

        Parameters
        ----------
        id : int
            The id of the particular player
        level : int
            The starting level of the player
        '''
        self.id = id
        self.level = level
        self.last_action = None
        self.last_state = None
        self.last_reward = None

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
    def pick_friends(self, levels, cap, skill_levels=None):
        '''
        The player picks the friend(s) to be on the kingship with him/her

        Parameters
        ----------
        levels : list(int)
            The levels of all players
        cap : int
            The max level cap
        skill_levels: list(int)
            The skill levels of all players (optional)

        Returns
        -------
        The index of the player selected to be the friend

        '''
        pass

    @abstractmethod
    def decide_sabotage(self, king, levels, cap, skill_levels=None):
        '''
        The player decides whether to sabotage their team

        Parameters
        ----------
        king : int
            The index of the king who has chosen them as a friend
        levels : list(int)
            The levels of all players
        cap : int
            The max level cap
        skill_levels : list(int)
            The skill levels of all players (optional)

        Returns
        -------
        A boolean for whether to sabotage

        '''
        pass

    @abstractmethod
    def accept_reward(self, reward, done):
        '''
        Accept the reward assigned by the game

        Parameters
        ----------
        reward : int
            The reward that comes about from the agent's action
        done : bool
            Whether the game is now over or not
        '''
        pass

    def __str__(self):
        return f'ID {self.id}, {self.__class__.__name__}, Level {self.level}'

class Basic_Agent(Agent):
    def pick_friends(self, levels, cap, skill_levels=None):
        # Randomly pick an agent that is not itself (excluded when sampling)
        return (np.random.randint(1, len(levels)) + self.id) % len(levels)

    def accept_reward(self, reward, done):
        pass

    def decide_sabotage(self, king, levels, cap, skill_levels=None):
        return False

class Lowest_Level_Agent(Agent):
    def pick_friends(self, levels, cap, skill_levels=None):
        # Pick the agent besides itself that has the lowest level
        candidates = list(zip([i for i in range(len(levels))], levels))
        candidates.pop(self.id)

        candidates = sorted(candidates, key=lambda t: t[1])

        lowest = []
        i = 0
        while candidates[i][1] == candidates[i-1][1] or i == 0:
            lowest.append(candidates[i][0])
            i += 1
            if i == len(candidates):
                break

        return np.random.choice(lowest, size=1)[0]

    def accept_reward(self, reward, done):
        pass

    def decide_sabotage(self, king, levels, cap, skill_levels=None):
        return False


class Skilled_Agent(Agent):
    def pick_friends(self, levels, cap, skill_levels=None):
        assert(skill_levels.all() != None)
        
        
        # Method 1 - pick most skilled agent that is not currently ahead in levels, else pick least levelled
        candidates_levels = list(zip([i for i in range(len(levels))], levels))
        self_level = candidates_levels.pop(self.id)[1]
        #print("current level"+str(self_level))
        candidates_levels = sorted(candidates_levels, key = lambda t:t[1])

        candidates_skills = list(zip([j for j in range(len(skill_levels))], skill_levels))
        self_skill = candidates_skills.pop(self.id)[1]
        candidates_skills = sorted(candidates_skills, key = lambda t:t[1])
        
        
        for i in range(len(skill_levels)-1):
            check = candidates_skills[len(skill_levels)-2-i][0]
            #print("check " + str(i)+ " other guy " + str(check)+ " skill = " +str(skill_levels[check])+" level = " + str(levels[check]))
            # possible idea: 
            k = (skill_levels[check] - self_skill)*10
            #k = 10
            if levels[check]+k <= self_level:
                return check
            
        return candidates_levels[0][0]
    
    def accept_reward(self, reward, done):
        pass

    def decide_sabotage(self, king, levels, cap, skill_levels=None):
        return False
