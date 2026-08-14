from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=100)
    logo_url = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return self.name


#i could learn the syntax but that thing will only slow me down. I need to learn the logic and the syntax will follow.
class MatchPrediction(models.Model):
    gameweek = models.IntegerField(default=1)
    home_team = models.ForeignKey(Team, related_name='home_matches', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_matches', on_delete=models.CASCADE)
    
    # NEW: Goal Tracking Fields
    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)
    
    # Legacy/Fallback Prediction Tag
    prediction = models.CharField(
        max_length=1, 
        choices=[('H', 'Home'), ('D', 'Draw'), ('A', 'Away')], 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"GW{self.gameweek}: {self.home_team.name} vs {self.away_team.name}"



# look I have AI helping me. Use it and don't be ashamed

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    favorite_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"