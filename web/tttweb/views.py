from django.http import JsonResponse

import sys
sys.path.append("../") # Adds higher directory to python modules path.
sys.path.append("../ttt") # Adds higher directory to python modules path.

from .models import Desks, States, Players, Games

from ttt import ttt_play, ttt_train_data_postgres


def load_desks(request):
    qs = Desks.objects.all().order_by('size')
    desks = {'desk_sizes': [rec.size for rec in qs]}
    return JsonResponse(desks)


def start_game(request):
    # p = ttt_play.TTTPlay(4, ttt_train_data_postgres.TTTTrainDataPostgres(4))
    # logger.info(request)
    gd = {'game_data': {}}
    gd['game_data']['ttt_play_msg'] = '1212'
    gd['game_data']['ttt_player'] = "Player 1 (x)"
    gd['game_data']['game_data.game_uuid'] = "weqw4234234"
    gd['game_data']['game_data.desk_size'] = 4
    gd['game_data']['game_data.desk'] =  ""
    gd['game_data']['game_data.game_state'] = 1
    print(gd)
    return JsonResponse(gd)


def make_move(request):
    return JsonResponse({'game_data': {} })
