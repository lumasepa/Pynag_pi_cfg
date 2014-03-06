from __future__ import absolute_import

from celery import shared_task
from fabric.api import env, run, put
from fabric.contrib.files import exists
from django.conf import settings
from fabric import exceptions
from main.models import TasksLog, Task
import os
import sys

@shared_task
def ssh_key_task(sonda, user, passwd):
    if Task.objects.filter(name="ssh_key").count() == 0:
        task = Task()
        task.name = "ssh_key"
        task.description = "send the ssh key to a sonda"
        task.save()
    try:
        env.user = user
        env.password = passwd
        env.host_string = str(sonda.address)
        if not exists('/root/.ssh/'):
            run("mkdir /root/.ssh")
        if not exists('/root/.ssh/authorized/'):
            run("mkdir /root/.ssh/authorized")
        put(settings.PROJECT_ROOT + "/keys/id_rsa.pub", "/root/.ssh/authorized/id_rsa.pub")
        run("cat /root/.ssh/authorized/id_rsa.pub >> /root/.ssh/authorized_keys")
        sonda.ssh = True
        sonda.save()
        print("Config done with " + sonda.name)
        tasklog = TasksLog()
        tasklog.message = "Config done with " + sonda.name
        tasklog.sonda = sonda
        tasklog.status = 0
        tasklog.task = Task.objects.get(name="ssh_key")
        tasklog.save()
    except exceptions.CommandTimeout:
        tasklog = TasksLog()
        tasklog.message = "CommandTimeout"
        tasklog.sonda = sonda
        tasklog.status = 1
        tasklog.task = Task.objects.get(name="ssh_key")
        tasklog.save()
    except exceptions.NetworkError:
        tasklog = TasksLog()
        tasklog.message = "NetworkError"
        tasklog.sonda = sonda
        tasklog.status = 1
        tasklog.task = Task.objects.get(name="ssh_key")
        tasklog.save()
    except:
        fail = "Unknow exeption :\n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        tasklog = TasksLog()
        tasklog.message = fail
        tasklog.sonda = sonda
        tasklog.status = 2
        tasklog.task = Task.objects.get(name="ssh_key")
        tasklog.save()

@shared_task
def send_checks(sonda, script):
    if Task.objects.filter(name="send_checks").count() == 0:
        task = Task()
        task.name = "send_checks"
        task.description = "send the script to a sonda and configure cron to execute the script"
        task.save()
    try:
        crontabtemplate = 'echo "*/$2 * * * * root /root/$1 $2" >> /etc/crontab'
        print(sonda.address)
        env.user = "root"
        env.host_string = str(sonda.address)
        env.key_filename = settings.PROJECT_ROOT + '/keys/id_rsa.pub'
        put("scripts/checks-" + sonda.name + ".sh", "/root/" + "checks-" + sonda.name + ".sh")

        for i in script.keys():
            crontab = crontabtemplate.replace("$2", str(i))
            run(crontab.replace("$1", "checks-" + sonda.name + ".sh "))

        run("chmod +x /root/" + "checks-" + sonda.name + ".sh")

        tasklog = TasksLog()
        tasklog.message = "Checks send to " + sonda.name
        tasklog.sonda = sonda
        tasklog.status = 0
        tasklog.task = Task.objects.get(name="send_checks")
        tasklog.save()
    except exceptions.CommandTimeout:
        tasklog = TasksLog()
        tasklog.message = "CommandTimeout"
        tasklog.sonda = sonda
        tasklog.status = 1
        tasklog.task = Task.objects.get(name="send_checks")
        tasklog.save()
    except exceptions.NetworkError:
        tasklog = TasksLog()
        tasklog.message = "NetworkError"
        tasklog.sonda = sonda
        tasklog.status = 1
        tasklog.task = Task.objects.get(name="send_checks")
        tasklog.save()
    except:
        fail = "Unknow exeption :\n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        tasklog = TasksLog()
        tasklog.message = fail
        tasklog.sonda = sonda
        tasklog.status = 2
        tasklog.task = Task.objects.get(name="send_checks")
        tasklog.save()