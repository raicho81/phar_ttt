import logging 
import os
logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)

import sys

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
        return self.name

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
        return self.name
