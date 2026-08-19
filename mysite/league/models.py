from django.contrib.auth.models import User
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100)
    logo_url = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return self.name


class MatchPrediction(models.Model):
    gameweek = models.IntegerField(default=1)
    home_team = models.ForeignKey(
        Team, related_name='home_matches', on_delete=models.CASCADE
    )
    away_team = models.ForeignKey(
        Team, related_name='away_matches', on_delete=models.CASCADE
    )

    # Date and Time Fields for Fixture Scheduling
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)

    # Goal & Status Fields
    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)

    prediction = models.CharField(
        max_length=1,
        choices=[('H', 'Home'), ('D', 'Draw'), ('A', 'Away')],
        null=True,
        blank=True,
    )
    is_live = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    minute = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return (
            f"GW{self.gameweek}: {self.home_team.name} vs {self.away_team.name}"
        )


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    favorite_team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True
    )
    points = models.IntegerField(default=0)  # Fixed FieldDoesNotExist error

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.points} pts)"


class Prediction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_predictions'
    )
    match = models.ForeignKey(
        MatchPrediction, on_delete=models.CASCADE, related_name='predictions'
    )
    home_goals = models.IntegerField()
    away_goals = models.IntegerField()
    is_scored = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'match')

    def __str__(self):
        return f"{self.user.username}: {self.match} ({self.home_goals}-{self.away_goals})"


class MatchCommentary(models.Model):
    match = models.ForeignKey(
        MatchPrediction, on_delete=models.CASCADE, related_name='commentary'
    )
    minute = models.IntegerField()
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-minute']

    def __str__(self):
        return f"{self.match} - {self.minute}' {self.event_type}"