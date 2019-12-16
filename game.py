import logging
import numpy as np


class Game(object):
    def __init__(self, players, mechanism, cap, reward_type='WINNERTAKEALL', logging_level='DEBUG'):
        """
        Given all the configurable settings, including players, mechanism, cap, create the game

        Parameters
        ----------
        players : list(Agent)
            The Agent objects who will play in the game, where play means choosing friends
        mechanism : Mechanism
            The mechanism for determining who levels up in each round
        cap : int
            The maximum level that signals end of game
        reward_type : str
            Type of reward to give when game ends
        logging_level : str
            How much text to be outputted by the game
        """
        logging.basicConfig(
            level=logging_level,
            filename='game.log',
            format='%(asctime)s - %(levelname)s - GAME - %(message)s'
        )
        logging.getLogger().setLevel(logging_level)

        self.num_players = len(players)

        logging.info(f'{self.num_players} currently playing.')
        logging.info(f'Players: {[str(player) for player in players]}')

        if self.num_players < 3:
            logging.critical("Not enough players.")
            print("Not enough players.")
            return

        # Initialize all levels to 0
        self.levels = [0 for i in range(self.num_players)]
        self.players = players

        # Randomly initialize the index of the player that starts king
        self.king = np.random.randint(0, self.num_players)

        self.mechanism = mechanism
        self.cap = cap
        self.reward_type = reward_type

        # Winning or losing results in 10 point reward
        self.lose_reward = float(-self.cap)
        self.win_reward = float(self.cap)

    def _is_game_over(self, levels):
        """
        Check if the game should finish

        Parameters
        ----------
        levels : list(int)
            The levels that the agents are currently on

        Returns
        -------
        True/False for if the game is over
        """
        for level in levels:
            if level >= self.cap:
                return True
        return False

    def reward(self, player, old_levels, new_levels):
        """
        Calculate the reward to give to each agent based on current levels

        Parameters
        ----------
        player : Agent
            The agent whose action resulted in these new levels
        new_levels : list(int)
            The most recent levels that the agents are on
        """
        if self._is_game_over(new_levels):
            # If game is over, assign win and lose rewards to each agent
            if self.reward_type == "WINNERTAKEALL":
                for p in self.players:
                    if new_levels[p.id] >= self.cap:
                        p.accept_reward(float(self.win_reward), done=True)
                    else:
                        p.accept_reward(float(self.lose_reward), done=True)
            elif self.reward_type == "PROPORTIONAL":
                sum_levels = sum(new_levels)
                for p in self.players:
                    p.accept_reward(float(new_levels[p.id]/sum_levels), done=True)
            elif self.reward_type == "RANKED":
                # Start with num_players points, lose 1 for every player ranked above
                for p in self.players:
                    curr_reward = self.num_players
                    for q in self.players:
                        if new_levels[q.id] > new_levels[p.id]:
                            curr_reward -= 1
                    p.accept_reward(float(curr_reward), done=True)

        else:
            # If game is not over, assign reward and continue
            # print(float(new_levels[player.id] - old_levels[player.id]))
            if self.reward_type == "WOT":
                player.accept_reward(float(new_levels[player.id] - old_levels[player.id]), done=False, levels=new_levels, cap=self.cap)
            else:
                player.accept_reward(0., done=False, levels=new_levels, cap=self.cap)


    def play(self):
        """
        Play the game in its entirety
        """
        logging.info('Game starting!')
        round = 0
        while not self._is_game_over(self.levels):
            round += 1
            logging.debug(f'Round {round}: Current Levels {self.levels}, Current King {self.king}')

            # The mechanism is used to determine the new levels of all players
            new_levels = self.mechanism.play(self.king , self.players, self.levels, self.cap)

            # The rewards are distributed based on these new levels
            self.reward(self.players[self.king], self.levels, new_levels)

            # New levels are assigned after rewards are computed
            self.levels = new_levels

            # The kingship moves forward
            self.king  = (self.king + 1) % self.num_players

        logging.info('Game results:')
        for i in range(self.num_players):
            logging.info(f'Player {i}: {self.players[i]}, Level {self.levels[i]}')

    # def step(self, friend):
    #     if not self._is_game_over(self.levels):
    #         done = False
    #
    #         curr_player = self.king
    #         curr_level = self.levels[curr_player]
    #
    #         self.levels = self.mechanism.step(self.levels, self.king, friend)
    #         self.king = (self.king + 1) % self.num_players
    #
    #         reward = self.levels[curr_player] - curr_level
    #
    #         if self._is_game_over(self.levels):
    #             done = True
    #             if self.levels[curr_player] >= self.cap:
    #                 reward += WIN_REWARD
    #             else:
    #                 reward += LOSE_REWARD
    #
    #         return reward, done
    #
    #     else:
    #         raise Exception('Game already over.')

    def reset(self):
        """
        Reset all the variables so the game can start over
        """
        self.levels = [0 for i in range(self.num_players)]
        self.king = np.random.randint(0, self.num_players)