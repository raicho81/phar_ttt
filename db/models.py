from asyncio import constants
import logging 
import os
import json
import sys


logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)

try:
    from django.db import models
except Exception:
    logger.exception('Exception: Django Not Found, please install it with "pip install django".')
    sys.exit()


class Desks(models.Model):
    size = models.IntegerField(null=False)
    total_games_played = models.IntegerField(null=False)

    class Meta:
        db_table = "Desks"
        constraints = [
            models.UniqueConstraint(fields=['size'], name='unique_size')
        ]

    def __str__(self):
        return "Desks(size={}, total_games_played={})".format(self.size, self.total_games_played)


class States(models.Model):
    desk_id = models.ForeignKey(Desks, on_delete=models.CASCADE, null=False, db_column="desk_id")
    state = models.BigIntegerField(null=False)
    moves = models.BinaryField(null=False)
    
    class Meta:
        db_table = "States"
        constraints = [
            models.UniqueConstraint(fields=['desk_id', 'state'], name='unique_desk_id_states')
        ]
    
    def __str__(self):
        return "States(desk_id={}, state={}, moves={}".format(self.desk_id, self.state, json.loads(self.moves))


class Players(models.Model):
    name = models.CharField(max_length=255, null=False)
    wins = models.IntegerField(null=False, default=0)
    draws = models.IntegerField(null=False, default=0)
    looses = models.IntegerField(null=False, default=0)
    player_uuid = models.UUIDField(null=False, db_column="player_uuid")
    
    class Meta:
        db_table = "Players"
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_players_name')
        ]


class Games(models.Model):
    game_uuid = models.UUIDField(null=False, db_column="game_uuid")
    player_id = models.ForeignKey(Players, on_delete=models.CASCADE, null=False, db_column="player_id")
    desk_size = models.ForeignKey(Desks, on_delete=models.CASCADE, null=False, db_column="desk_size")
    cur_state = models.BigIntegerField(null=False)
    desk = models.BinaryField(null=False)
    
    class Meta:
        db_table = "Games"
        constraints = [
            models.UniqueConstraint(fields=['game_uuid'], name='unique_games_uuid')
        ]
