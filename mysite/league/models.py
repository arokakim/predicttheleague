from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    stadium_name = models.CharField(max_length=150, default="Main Stadium")
    logo_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name


class MatchPrediction(models.Model):
    gameweek = models.IntegerField(default=0)  # 0 = Unassigned Pool, 1-38 = Scheduled
    home_team = models.ForeignKey(Team, related_name='home_matches', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_matches', on_delete=models.CASCADE)
    
    match_date = models.DateField(null=True, blank=True)
    kickoff_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=150, blank=True, null=True)
    
    PREDICTION_CHOICES = [
        ('H', 'Home Win'),
        ('D', 'Draw'),
        ('A', 'Away Win'),
    ]
    prediction = models.CharField(max_length=1, choices=PREDICTION_CHOICES, null=True, blank=True)

    class Meta:
        unique_together = ('home_team', 'away_team')

    def save(self, *args, **kwargs):
        # Auto-fill venue to home team's stadium if left blank
        if not self.venue and self.home_team:
            self.venue = self.home_team.stadium_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GW {self.gameweek}: {self.home_team.name} vs {self.away_team.name}"