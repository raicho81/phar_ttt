# Generated by Django 4.0.2 on 2022-02-15 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0004_games_next_player_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='games',
            name='player1_path',
            field=models.BinaryField(default=None),
        ),
        migrations.AddField(
            model_name='games',
            name='player2_path',
            field=models.BinaryField(default=None),
        ),
    ]