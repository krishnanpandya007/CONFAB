import hashlib
from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Account(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    university = models.CharField(max_length=100, null=True, blank=True)
    major = models.CharField(max_length=100, null=False, blank=False)
    is_valid = models.BooleanField(default=False)
    email_hash = models.CharField(null=False, blank=False, max_length=41)
    year = models.PositiveSmallIntegerField(null=True, blank=True)

    def get_formatted(self):
        ender = {1: "st", 2: "nd", 3: "rd", 4: "th"}
        return f"{self.university} ({self.major} {self.year}{ender[self.year]})"
    def __str__(self):
        return "( " + self.university + " ) : " + self.year + " " + self.major
