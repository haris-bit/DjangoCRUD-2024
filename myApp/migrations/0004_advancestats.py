# Generated by Django 4.2 on 2023-10-04 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0003_drink'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvanceStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=None, max_length=200, null=True)),
                ('minutes_played', models.PositiveIntegerField(default=0)),
                ('games_played', models.PositiveIntegerField(default=0)),
                ('three_point_attempt_rate', models.FloatField(default=0.0)),
                ('total_rebound_percentage', models.CharField(default='', max_length=200)),
                ('win_shares', models.FloatField(default=0.0)),
                ('win_shares_per_48_minutes', models.FloatField(default=0.0)),
                ('box_plus_minus', models.FloatField(default=0.0)),
                ('value_over_replacement_player', models.FloatField(default=0.0)),
            ],
        ),
    ]