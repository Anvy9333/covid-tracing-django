from django.db import models
from django.contrib.auth.models import User


#  establishment
class Establishment(models.Model):
    name = models.CharField(max_length=200)
    capacity = models.IntegerField()  # number of seats/places
    is_compliant = models.BooleanField(default=True)
    # Who owns it. If the manager's User is deleted, delete their establishments too.
    manager = models.ForeignKey(User, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name


# booking 
class Reservation(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)
    date = models.DateField()
    nb_people = models.IntegerField()  # used to check capacity

    def __str__(self):
        return f"{self.client.username} @ {self.establishment.name} ({self.date})"


# positive client  on a given date.
class PositiveReport(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    test_date = models.DateField()

    def __str__(self):
        return f"{self.client.username} positive ({self.test_date})"
    
# extra flag for manager 
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} (manager={self.is_manager})"