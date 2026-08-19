from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core Application Routes
    path('', views.home_view, name='home'),
    path('standings/', views.standings, name='standings'),
    path('manager/', views.gameweek_builder, name='gameweek_builder'),
    path('manager/gw/<int:gw>/', views.gameweek_builder, name='gameweek_builder_gw'),
    path('match/<int:match_id>/', views.match_focus, name='match_focus'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/', views.profile_view, name='profile'),

    # Authentication Routes
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='league/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='standings'), name='logout'),
    path('official-standings/', views.official_standings, name='official_standings'),
]