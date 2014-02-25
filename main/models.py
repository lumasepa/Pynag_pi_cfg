from django.db import models

# Create your models here.


class Sondas(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)
    localizacion = models.CharField(max_length=300)
    ssh = models.BooleanField()
    def __unicode__(self):
        return self.name


class Services(models.Model):
    name = models.CharField(max_length=200)
    command = models.TextField()
    pluging = models.BooleanField()

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
    check_every = models.IntegerField()
    contact = models.CharField(max_length=200)
