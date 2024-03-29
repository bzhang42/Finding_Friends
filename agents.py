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
    def accept_reward(self, reward, done=False, levels=None, cap=None):
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

    def accept_reward(self, reward, done=False, levels=None, cap=None):
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

    def accept_reward(self, reward, done=False, levels=None, cap=None):
        pass

    def decide_sabotage(self, king, levels, cap, skill_levels=None):
        return False


class Strategic_Skilled_Agent(Agent):
    def pick_friends(self, levels, cap, skill_levels=None):
        assert (skill_levels.all() != None)

        # Method 1 - pick most skilled agent that is not currently ahead in levels, else pick least levelled
        candidates_levels = list(zip([i for i in range(len(levels))], levels))
        self_level = candidates_levels.pop(self.id)[1]
        # print("current level"+str(self_level))
        candidates_levels = sorted(candidates_levels, key=lambda t: t[1])

        candidates_skills = list(zip([j for j in range(len(skill_levels))], skill_levels))
        self_skill = candidates_skills.pop(self.id)[1]
        candidates_skills = sorted(candidates_skills, key=lambda t: t[1])

        for i in range(len(skill_levels) - 1):
            check = candidates_skills[len(skill_levels) - 2 - i][0]
            # print("check " + str(i)+ " other guy " + str(check)+ " skill = " +str(skill_levels[check])+" level = " + str(levels[check]))
            # possible idea:
            # k = (skill_levels[check] - self_skill)*10
            k = cap/10
            if levels[check] + k <= self_level:
                return check

        return candidates_levels[0][0]

    def accept_reward(self, reward, done=False, levels=None, cap=None):
        pass

    def decide_sabotage(self, king, levels, cap, skill_levels=None):
        return False


class Beta_Binomial_Agent(Strategic_Skilled_Agent):
    def __init__(self, id, level, skill, priors=(1, 1)):
        super(Beta_Binomial_Agent, self).__init__(id, level)
        self.skill = skill
        self.trials = {}
        self.successes = {}
        self.last_friend = None
        self.last_friend_level = None
        self.last_level = level
        self.priors = priors

    def map_probs(self, num_players):
        skill_levels_map = np.zeros(num_players)
        for i in self.trials.keys():
            prob_map = (self.successes[i] + self.priors[0]) / (self.trials[i] + self.priors[0] + self.priors[1])
            skill_levels_map[i] = prob_map - self.skill
        return skill_levels_map

    def pick_friends(self, levels, cap, skill_levels=None):
        if self.last_friend is not None and levels[self.last_friend] - self.last_friend_level > 0 and levels[self.id] - self.last_level > 0:
            self.successes[self.last_friend] += 1

        # Calculate the max a posteriori estimate for each other player
        skill_levels_map = self.map_probs(len(levels))

        # Use the skilled agent's algorithm for picking friend
        friend = super(Beta_Binomial_Agent, self).pick_friends(levels, cap, skill_levels=skill_levels_map)

        if friend not in self.trials.keys():
            self.trials[friend] = 1
        else:
            self.trials[friend] += 1

        if friend not in self.successes.keys():
            self.successes[friend] = 0

        self.last_friend = friend
        self.last_friend_level = levels[friend]
        self.last_level = levels[self.id]

        return friend

class Gamma_Poisson_Agent(Strategic_Skilled_Agent):
    def __init__(self, id, level, skill, priors=(1, 2)):
        super(Gamma_Poisson_Agent, self).__init__(id, level)
        self.skill = skill
        self.trials = {}
        self.successes = {}
        self.last_friend = None
        self.last_friend_level = None
        self.last_level = level
        self.priors = priors

    def map_probs(self, num_players):
        skill_levels_map = np.zeros(num_players)
        for i in self.trials.keys():
            r = self.priors[0] + self.successes[i]
            p = 1 / (1 + self.priors[1] + self.trials[i])
            prob_map = p * r / (1 - p)
            skill_levels_map[i] = prob_map - self.skill
        return skill_levels_map

    def pick_friends(self, levels, cap, skill_levels=None):
        if self.last_friend is not None and levels[self.last_friend] - self.last_friend_level > 0 and levels[self.id] - self.last_level > 0:
            self.successes[self.last_friend] += 1

        # Calculate the max a posteriori estimate for each other player
        skill_levels_map = self.map_probs(len(levels))

        # Use the skilled agent's algorithm for picking friend
        friend = super(Gamma_Poisson_Agent, self).pick_friends(levels, cap, skill_levels=skill_levels_map)

        if friend not in self.trials.keys():
            self.trials[friend] = 1
        else:
            self.trials[friend] += 1

        if friend not in self.successes.keys():
            self.successes[friend] = 0

        self.last_friend = friend
        self.last_friend_level = levels[friend]
        self.last_level = levels[self.id]

        return friend

class Q_Agent(Agent):
    def __init__(self, id, level, output_dim, epsilon=0.1, alpha=0.05, gamma=0.9):
        super(Q_Agent, self).__init__(id, level)

        self.last_state = None
        self.last_action = None
        self.last_reward = None
        self.step = 0

        self.actions = [i for i in range(output_dim)]
        self.q = {}

        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma


    def reset(self):
        self.last_state = None
        self.last_action = None
        self.last_reward = None
        self.step = 0

    #----------------------------------------------------------------
    # EVERYTHING BELOW IS Q-LEARNING

    def getQ(self, state, action):
        '''
        Return the q-value at the (state, action) pair, or 0 if not found
        '''
        return self.q.get((state, action), 0.0)

    def learnQ(self, state, action, reward, value):
        '''
        Given the latest reward as well as the newly calculated value, update the q-score to reflect this
        '''
        old_value = self.q.get((state, action), None)

        # If old value is not found, then initialize it to the given reward
        if old_value is None:
            self.q[(state, action)] = reward
        # Otherwise, calculate Q(s, a) += alpha * (reward(s,a) + max(Q(s') - Q(s,a))
        else:
            self.q[(state, action)] = old_value + self.alpha * (value - old_value)

    def chooseAction(self, state):
        '''
        Choose an action based on the Epsilon-Greedy policy
        '''

        if np.random.random() < self.epsilon:
            action = np.random.choice(self.actions)
        else:
            q_vals = [self.getQ(state, action) for action in self.actions]
            max_q = max(q_vals)
            actions = [i for i, x in enumerate(q_vals) if x == max_q]
            action = np.random.choice(actions)
        return action

    def learn(self, p_state, p_action, reward, n_state):
        '''
        Calculate the max q-value for q-learning (on policy)
        '''
        q_new = max([self.getQ(n_state, action) for action in self.actions])
        self.learnQ(p_state, p_action, reward, reward + self.gamma * q_new)

    def pick_friends(self, levels, cap, skill_levels=None):
        new_state = tuple(levels)
        self.step += 1

        new_action = self.chooseAction(new_state)

        # If there is something to learn from (a last iteration), learn from it
        if self.step > 1:
            self.learn(self.last_state, self.last_action, self.last_reward, new_state)

        # Update the new last action and state
        self.last_action = new_action
        self.last_state = new_state

        return self.last_action

    def accept_reward(self, reward, done=False, levels=None, cap=None):
        if done:
            self.learn(self.last_state, self.last_action, reward, (0))
            self.reset()
        else:
            self.last_reward = reward