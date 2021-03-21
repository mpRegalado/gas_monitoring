from django.db import models
from django.utils import timezone

# Create your models here.

class Session(models.Model):
    #A session represents a complete set of measurements by a single device.
    #Each session is identified by a positive integer generated by the device.
    #There is room to improve on this model by assigning a unique identifyer to
    #each sensor and
    session_id = models.IntegerField()
    creation_date = models.DateTimeField(default = timezone.now)
    name = models.CharField(default = str(timezone.now()), max_length=200)

    def __str__(self):
        return self.name

    def is_fixed(self):
        return self.measurement_set.exclude(latitude=None).count() > 0
    def get_first_fix(self):
        if self.is_fixed():
            return self.measurement_set.exclude(latitude=None, longitude=None).order_by('date_time').first()
        else:
            return None



class Measurement(models.Model):
    #Each measurement contains information about the ammount of gas recorded,
    #the location, and the time it was taken, and it's tied to a specific session.
    gas_high = models.IntegerField()
    gas_avg = models.IntegerField()
    latitude = models.FloatField(default=None, blank=True, null=True)
    longitude = models.FloatField(default=None, blank=True, null=True)
    date_time = models.DateTimeField(default = timezone.now)
    session= models.ForeignKey(Session,on_delete=models.CASCADE)

    def __str__(self):
        return str(self.date_time.hour) + ":" + str(self.date_time.minute) + ":" + str(self.date_time.second) + "->" + str(self.gas_high)

    def get_formated_date_time(self):
        return self.date_time.strftime("%Y-%m-%d %H:%M:%S")

    def is_fixed(self):
        return self.latitude != None and self.longitude != None