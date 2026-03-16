from django.db import models


class Blocks(models.Model):
    title = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.title


class Floors(models.Model):
    number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.number)


class Rooms(models.Model):
    number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.number)


class Renovation(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.title


class Basement(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.title
