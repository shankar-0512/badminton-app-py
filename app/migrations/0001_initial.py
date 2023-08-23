# Generated by Django 4.2.4 on 2023-08-22 21:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="court",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("court_name", models.TextField(unique=True)),
                ("status", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "court_status",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="game",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user_name", models.TextField(unique=True)),
                ("status", models.TextField(default="inactive")),
                ("elo_rating", models.IntegerField(default=1500)),
                ("uncertainty", models.FloatField(default=1)),
                ("playing", models.CharField(default="N")),
                ("played", models.IntegerField(default=0)),
                ("won", models.IntegerField(default=0)),
                ("lost", models.IntegerField(default=0)),
                ("last_played", models.DateField(auto_now=True)),
                ("rating_changes", models.TextField(default="")),
                ("unmatched_priority", models.IntegerField(default=0)),
                ("password", models.TextField(default="")),
            ],
            options={
                "db_table": "player_details",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="history",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(auto_now_add=True)),
                (
                    "player1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matchups_as_player1",
                        to="app.game",
                    ),
                ),
                (
                    "player2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matchups_as_player2",
                        to="app.game",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="history",
            constraint=models.UniqueConstraint(
                fields=("player1", "player2"), name="unique_matchup"
            ),
        ),
    ]