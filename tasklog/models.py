from django.db import models

# Create your models here.
from django.db import models
from main.models import Sonda


class Task(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __unicode__(self):
        return self.name


class TasksLog(models.Model):
    sonda = models.ForeignKey(Sonda)
    task = models.ForeignKey(Task)

    def __unicode__(self):
        return self.task.name + " " + self.sonda.name


class TaskStatus(models.Model):
    STATUS_CHOICES = (
        (0, 'Correct'),
        (1, 'Know fail'),
        (2, 'Unknow fail'),
        (-1, 'Relaunched'),
    )
    tasklog = models.ForeignKey(TasksLog)
    status = models.IntegerField(choices=STATUS_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField()

    def __unicode__(self):
        return self.tasklog.task.name + str(self.status) + " " + str(self.timestamp)