import uuid
import sys
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.http import require_POST
# from django.views.decorators.csrf import csrf_exempt

from .models import Desks, Players, Games

sys.path.append("../../")
sys.path.append("../../ttt")
from ttt import ttt_play, ttt_train_data_postgres, ttt_game_type, ttt_data_encoder

@require_http_methods(["GET"])
def load_desks(request):
    qs = Desks.objects.all().order_by('size')
    desks = {'desk_sizes': [rec.size for rec in qs]}
    return JsonResponse(desks)


@ensure_csrf_cookie
def get_csrf(request):
    response = JsonResponse({'detail': 'CSRF cookie set', 'X-CSRFToken': get_token(request)})
    return response


@require_POST
def start_game(request):
    params = json.loads(request.body)
    player_name = params['player_name']
    player = Players.objects.get_or_create(name=player_name)
    uuid_ = uuid.uuid4()
    desk_size = int(params['desk_size'])
    p = ttt_play.TTTPlay(desk_size, ttt_train_data_postgres.TTTTrainDataPostgres(desk_size), ttt_game_type.TTTGameTypeHVsC, game_uuid=uuid_, player=player[0])
    game_state = p.start_game()
    gd = {'game_data': {}}
    gd['game_data']['player_code'] = p.get_player_code()
    gd['game_data']['next_player_code'] = p.get_next_player_code()
    gd['game_data']['desk_size'] = desk_size
    gd['game_data']['player_mark'] = p.get_player_mark()
    gd['game_data']['game_uuid'] = uuid_
    gd['game_data']['desk'] = p.desk.get_state_marks()
    gd['game_data']['game_state'] = game_state
    gd['game_data']['player_name'] = player_name
    return JsonResponse(gd)


@require_POST
def make_move(request):
    params = json.loads(request.body)
    uuid_ = params['game_uuid']
    desk_size = params['desk_size']
    next_move_idx = params['next_move_idx']
    p = ttt_play.TTTPlay(desk_size, ttt_train_data_postgres.TTTTrainDataPostgres(desk_size), ttt_game_type.TTTGameTypeHVsC, game_uuid=uuid_)
    game_state, win_player = p.make_move_stochastic(next_move_idx)
    game = Games.objects.get(game_uuid=uuid_)
    gd = {'game_data': {}}
    gd['game_data']['player_code'] = game.player_code
    gd['game_data']['next_player_code'] = game.next_player_code
    gd['game_data']['desk_size'] = desk_size
    gd['game_data']['player_mark'] = game.player_mark
    gd['game_data']['game_uuid'] = uuid_
    gd['game_data']['desk'] = p.desk.get_state_marks()
    gd['game_data']['game_state'] = game_state.get_code()
    gd['game_data']['win_player'] = win_player.get_code() if win_player is not None else None
    return JsonResponse(gd)

