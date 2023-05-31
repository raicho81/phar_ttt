from django.urls import path

from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    path('start_game/', views.start_game, name='start_game'),
    path('make_move/', views.make_move, name='make_move'),
    path('load_desks/', views.load_desks, name='load_desks'),
    path('get_csrf/', views.get_csrf, name='get_csrf'),
]
