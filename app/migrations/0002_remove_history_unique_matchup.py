# Generated by Django 4.2.4 on 2023-08-22 21:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="history",
            name="unique_matchup",
        ),
    ]
