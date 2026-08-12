from django.contrib import admin
from .models import Team, MatchPrediction

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(MatchPrediction)
class MatchPredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'home_team', 'away_team', 'prediction')