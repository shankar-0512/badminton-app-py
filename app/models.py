from django.db import models


class game(models.Model):
    user_name = models.TextField()
    status = models.TextField(default="inactive")
    elo_rating = models.IntegerField(default=1500)
    uncertainty = models.FloatField(default=1)
    playing = models.CharField(default="N")
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    # update the date automatically every time an entry is updated
    last_played = models.DateField(auto_now=True)
    # store the ELO changes as a comma-separated string
    rating_changes = models.TextField(default="")
    unmatched_priority = models.IntegerField(default=0)
    password = models.TextField(default="")

    class Meta:
        managed = False  # Tell Django not to manage this table with migrations
        db_table = 'player_details'

    def __str__(self):
        return self.user_name  # Return a meaningful representation of the model instance


class court(models.Model):
    court_name = models.TextField()
    status = models.BooleanField(default=True)

    class Meta:
        managed = False  # Tell Django not to manage this table with migrations
        db_table = 'court_status'
