from django.db import models

# Create your models here.


class Sondas(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)
    user = models.CharField(max_length=50)
    passwd = models.CharField(max_length=50)
    localizacion = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

class Services(models.Model):
    name = models.CharField(max_length=200)
    command = models.CharField(max_length=2000)
    pluging = models.BooleanField()
    freshness_threshold = models.IntegerField()
    contact = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name


class Hosts(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)

    def __unicode__(self):
        return self.name


class HostsServicesSondas(models.Model):
    host = models.ForeignKey(Hosts)
    service = models.ForeignKey(Services)
    sonda = models.ForeignKey(Sondas)