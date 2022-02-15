import uuid
import sys

from django.http import JsonResponse

from ttt.db import models

from .models import Desks, States, Players, Games

sys.path.append("../../")
sys.path.append("../../ttt")
from ttt import ttt_play, ttt_train_data_postgres, ttt_game_type


def load_desks(request):
    qs = Desks.objects.all().order_by('size')
    desks = {'desk_sizes': [rec.size for rec in qs]}
    return JsonResponse(desks)


def start_game(request):
    params = request.GET
    player_name = params['player_name']
    player = Players.objects.get_or_create(name=player_name)
    uuid = uuid.uuid4()
    p = ttt_play.TTTPlay(4, ttt_train_data_postgres.TTTTrainDataPostgres(4), ttt_game_type.TTTGameTypeHVsC, game_uuid=uuid, player_id=player.id)
    game_state = p.start_game()
    game = models.Games.objects.get(game_uuid=uuid, player_id=player.id)
    gd = {'game_data': {}}
    gd['game_data']['player_code'] = game.player_code
    gd['game_data']['next_ttt_player'] = game.next_player
    gd['game_data']['player_mark'] = game.player_mark
    gd['game_data']['game_uuid'] = uuid
    gd['game_data']['desk'] = p.desk.get_state()
    gd['game_data']['game_state'] = game_state
    print(gd)
    return JsonResponse(gd)


def make_move(request):
    return JsonResponse({'game_data': {} })
