from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.standings, name='standings'),
    path('manager/', views.gameweek_builder, name='gameweek_builder'),
    path('manager/gw/<int:gw>/', views.gameweek_builder, name='gameweek_builder_gw'),
    path('match/<int:match_id>/', views.match_focus, name='match_focus'),

    #authentication routes
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='league/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='standings'), name='logout'),

    path('leaderboard/', views.leaderboard, name='leaderboard'),

    path('profile/', views.profile_view, name='profile'),
]