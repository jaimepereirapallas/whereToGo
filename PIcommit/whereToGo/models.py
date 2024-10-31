from django.db import models
from django.contrib.auth.models import User

class Trips(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    origin = models.CharField(max_length=30, null=False)
    destination = models.CharField(max_length=30, null=False)
    takeoff = models.DateTimeField(null=False)
    arrival = models.DateTimeField(null=False)
    escalas = models.CharField(max_length=50, null=False)
    latitude = models.FloatField(null=True)  
    longitude = models.FloatField(null=True)  

    def __str__(self):
        return f"El viaje con destino a {self.destination} y origen {self.origin} del usuario {self.user} sale a las {self.takeoff} y llega a las {self.arrival}, tipo de vuelo {self.escalas}"
