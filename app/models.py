# Django imports
from django.db import models

# Python standard library imports
from datetime import date, timedelta


class game(models.Model):
    user_name = models.TextField(unique=True)
    status = models.TextField(default="inactive")
    elo_rating = models.IntegerField(default=1500)
    uncertainty = models.FloatField(default=1)
    playing = models.CharField(default="N", max_length=1)
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    last_played = models.DateField(auto_now=True)
    rating_changes = models.TextField(default="")
    unmatched_priority = models.IntegerField(default=0)
    password = models.TextField(default="")

    class Meta:
        managed = True
        db_table = 'player_details'

    def __str__(self):
        return self.user_name


class court(models.Model):
    court_name = models.TextField(unique=True)
    status = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'court_status'


class history(models.Model):
    player1 = models.ForeignKey(game, related_name='matchups_as_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(game, related_name='matchups_as_player2', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    class Meta:
        pass  # If not using any constraints or options, consider removing the whole Meta class

    def __str__(self):
        return f"Matchup between {self.player1} and {self.player2} on {self.date}"

    @staticmethod
    def has_recent_matchup(player1_id, player2_id):
        """Check if two players have had a matchup in the last `days_threshold` days."""
        cutoff_date = date.today()
        return history.objects.filter(
            models.Q(player1_id=player1_id, player2_id=player2_id) |
            models.Q(player1_id=player2_id, player2_id=player1_id),
            date__gte=cutoff_date
        ).exists()
    
