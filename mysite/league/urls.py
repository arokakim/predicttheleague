from django.urls import path
from . import views

urlpatterns = [
    path('', views.standings, name='standings'),
    path('manager/', views.gameweek_builder, name='gameweek_builder'),
    path('manager/gw/<int:gw>/', views.gameweek_builder, name='gameweek_builder_gw'),
    path('match/<int:match_id>/', views.match_focus, name='match_focus'),
]