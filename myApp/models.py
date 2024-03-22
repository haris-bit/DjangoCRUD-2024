from django.db import models

# Create your models here.


class Drink(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY = (
        ("Indoor", "Indoor"),
        ("Out Door", "Out Door"),
    )
    name = models.CharField(max_length=200, null=True)
    price = models.FloatField(null=True)
    category = models.CharField(max_length=200, null=True, choices=CATEGORY)
    description = models.CharField(max_length=200, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS = (
        ("Pending", "Pending"),
        ("Out for Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
    )

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=200, null=True, choices=STATUS)


# model for advanced statistics
class AdvanceStats(models.Model):
    name = models.CharField(max_length=200, null=True, default=None)  # Allow null values and set a default if needed
    minutes_played = models.PositiveIntegerField(default=0)
    games_played = models.PositiveIntegerField(default=0)
    three_point_attempt_rate = models.FloatField(default=0.0)
    total_rebound_percentage = models.CharField(max_length=200, null=False, default='')
    win_shares = models.FloatField(default=0.0)
    win_shares_per_48_minutes = models.FloatField(default=0.0)
    box_plus_minus = models.FloatField(default=0.0)
    value_over_replacement_player = models.FloatField(default=0.0)
    player_efficiency_rating = models.FloatField(default=0.0)

    def __str__(self):
        return f"AdvanceStats for WS: {self.name}, {self.win_shares}, WS/48: {self.win_shares_per_48_minutes}, BPM: {self.box_plus_minus}, VORP: {self.value_over_replacement_player}"
