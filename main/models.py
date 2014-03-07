from django.db import models


class Sonda(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)
    localizacion = models.CharField(max_length=300)
    ssh = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=200)
    command = models.TextField()
    pluging = models.BooleanField()

    def __unicode__(self):
        return self.name


class Host(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)

    def __unicode__(self):
        return self.name


class HostsServicesSondas(models.Model):
    host = models.ForeignKey(Host)
    service = models.ForeignKey(Service)
    sonda = models.ForeignKey(Sonda)
    check_every = models.IntegerField()
    contact = models.CharField(max_length=200)