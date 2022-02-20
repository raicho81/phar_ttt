import json
from sqlite3 import Date
import sys

from django.db import models
import django.utils.timezone


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
    
    class Meta:
        db_table = "Players"
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_players_name')
        ]


class Games(models.Model):
    game_uuid = models.UUIDField(null=False, db_column="game_uuid")
    player_id = models.ForeignKey(Players, on_delete=models.CASCADE, null=False, db_column="player_id")
    game_state = models.IntegerField(null=False)
    desk = models.BinaryField(null=False)
    player_code = models.IntegerField(null=False)
    player_mark = models.CharField(null=False, max_length=2)
    modified = models.DateTimeField(null=False, default=django.utils.timezone.now)
    next_player_code = models.IntegerField(null=False, default=1)
    player1_path = models.BinaryField(null=False, default=None)
    player2_path = models.BinaryField(null=False, default=None)
    
    class Meta:
        db_table = "Games"
        constraints = [
            models.UniqueConstraint(fields=['game_uuid'], name='unique_games_uuid')
        ]
