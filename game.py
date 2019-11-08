import logging
import numpy as np

class Game(object):
    def __init__(self, players, logging_level='DEBUG'):
        logging.basicConfig(
            level=logging_level,
            filename='game.log',
            format='%(asctime)s - %(levelname)s - GAME - %(message)s'
        )
        logging.getLogger().setLevel(logging_level)

        self.num_players = len(players)
        self.num_friends = len(players) // 2 - 1

        logging.info(f'{self.num_players} currently playing.')
        logging.info(f'Players: {players}')
        if self.num_players < 4:
            logging.critical("Not enough players.")
            print("Not enough players.")
            return

        self.levels = [0 for i in range(self.num_players)]
        self.players = [players[i](i, self.levels[i]) for i in range(self.num_players)]
        self.king = np.random.randint(0, self.num_players)

    def _is_game_over(self, cap):
        for level in self.levels:
            if level >= cap:
                return True
        return False

    def play(self, cap, mechanism):
        logging.info('Game starting!')
        round = 0
        while not self._is_game_over(cap):
            round += 1
            logging.debug(f'Round {round}: Current Levels {self.levels}, Current King {self.king}')

            self.levels = mechanism.play(self.players, self.num_friends, self.levels, self.king, cap)
            self.king  = (self.king + 1) % self.num_players

        logging.info('Game results:')
        for i in range(self.num_players):
            logging.info(f'Player {i}: {self.players[i]}, Level {self.levels[i]}')

    def reset(self):
        self.levels = [0 for i in range(self.num_players)]
        self.king = np.random.randint(0, self.num_players)