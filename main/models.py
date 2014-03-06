from django.db import models

# Create your models here.


class Sonda(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)
    localizacion = models.CharField(max_length=300)
    ssh = models.BooleanField()
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


class Task(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __unicode__(self):
        return self.name


class TasksLog(models.Model):
    status = models.IntegerField()
    message = models.TextField()
    sonda = models.ForeignKey(Sonda)
    task = models.ForeignKey(Task)

    def __unicode__(self):
        return self.task.name + " " + str(self.status) + " " + self.sonda.name