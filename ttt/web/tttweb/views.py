import uuid
import sys
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
# from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from .models import Desks, Players, Games

sys.path.append("../../")
sys.path.append("../../ttt")
from ttt import ttt_play, ttt_train_data_postgres, ttt_game_type


@require_http_methods(["GET", "OPTIONS"])
@gzip_page
def load_desks(request):
    qs = Desks.objects.all().order_by('size')
    desks = {'desk_sizes': [rec.size for rec in qs]}
    response = JsonResponse(desks)
    # response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = ['GET', 'OPTIONS']
    return response


@require_http_methods(["GET", "OPTIONS"])
@ensure_csrf_cookie
@gzip_page
def get_csrf(request):
    response = JsonResponse({'detail': 'CSRF cookie set', 'X-CSRFToken': get_token(request)})
    # response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = ['GET', 'OPTIONS']
    return response


@require_http_methods(["POST", "OPTIONS"])
@gzip_page
def start_game(request):
    if request.method == 'OPTIONS':
        response = JsonResponse({'detail': 'CSRF cookie set', 'X-CSRFToken': get_token(request)})
        # response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = ['POST', 'OPTIONS']
        # response['Access-Control-Allow-Headers'] = ['Content-Type', 'X-CSRFToken']
        return response

    params = request.POST
    if params:
        params = params.dict()
    else:
        params = json.loads(request.body)

    player_name = params.get('player_name')
    player = Players.objects.get_or_create(name=player_name)
    uuid_ = uuid.uuid4()
    desk_size = int(params.get('desk_size'))
    p = ttt_play.TTTPlay(desk_size, ttt_train_data_postgres.TTTTrainDataPostgres(desk_size), ttt_game_type.TTTGameTypeHVsC, game_uuid=uuid_, player_id=player[0])
    game_state = p.start_game()

    gd = {'game_data': {}}
    gd['game_data']['player_code'] = p.get_player_code()
    gd['game_data']['next_player_code'] = p.get_next_player_code()
    gd['game_data']['player_mark'] = p.get_player_mark()
    gd['game_data']['game_uuid'] = uuid_
    gd['game_data']['desk'] = p.desk.get_state()
    gd['game_data']['game_state'] = game_state
    gd['game_data']['player_name'] = player_name
    gd['game_data']['desk_size'] = desk_size
    gd['game_data']['player_id'] = player[0].id

    response = JsonResponse(gd)
    # response['Access-Control-Allow-Origin'] = '*'
    # response['Access-Control-Allow-Methods'] = ['GET', 'POST', 'OPTIONS']
    return response


@require_http_methods(["POST", "OPTIONS"])
@gzip_page
def make_move(request):
    if request.method == 'OPTIONS':
        response = JsonResponse({'detail': 'CSRF cookie set', 'X-CSRFToken': get_token(request)})
        # response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = ['POST', 'OPTIONS']
        response['Access-Control-Allow-Headers'] = ['Content-Type', 'X-CSRFToken']
        return response

    params = request.POST
    if params:
        params = params.dict()
    else:
        params = json.loads(request.body)

    player_id = params.get('player_id')
    uuid_ = params.get('game_uuid')
    desk_size = params.get('desk_size')
    next_move_idx = params.get('next_move_idx')
    p = ttt_play.TTTPlay(desk_size, ttt_train_data_postgres.TTTTrainDataPostgres(desk_size), ttt_game_type.TTTGameTypeHVsC, game_uuid=uuid_, player_id=player_id)
    game_state, win_player = p.make_move_stochastic(next_move_idx)
    game = Games.objects.get(game_uuid=uuid, player_id=player_id)

    gd = {'game_data': {}}
    gd['game_data']['player_code'] = game.player_code
    gd['game_data']['next_player_code'] = game.next_player_code
    gd['game_data']['player_mark'] = game.player_mark
    gd['game_data']['game_uuid'] = uuid_
    gd['game_data']['desk'] = p.get_desk_state()
    gd['game_data']['game_state'] = game_state
    gd['game_data']['win_player'] = win_player
    gd['game_data']['desk_size'] = desk_size
    gd['game_data']['player_id'] = player_id

    response = JsonResponse(gd)
    # response['Access-Control-Allow-Origin'] = '*'
    # response['Access-Control-Allow-Methods'] = ['GET', 'POST', 'OPTIONS']
    return response

