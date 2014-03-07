from __future__ import absolute_import

from celery import shared_task
from fabric.api import env, run, put
from fabric.contrib.files import exists
from django.conf import settings
from fabric import exceptions
from main.models import TasksLog, Task, Sonda
import os
import sys
import datetime

@shared_task
def ssh_key_task(sonda_name, user, passwd):
    sonda = Sonda.objects.get(name=sonda_name)
    if Task.objects.filter(name="ssh_key").count() == 0:
        task = Task()
        task.name = "ssh_key"
        task.description = "send the ssh key to a sonda"
        task.save()
    tasklog = TasksLog()
    try:
        env.skip_bad_hosts = True
        env.abort_on_prompts = True
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
        tasklog.message = "Config done with " + sonda.name
        tasklog.status = 0
    except exceptions.CommandTimeout:
        tasklog.message = "CommandTimeout"
        tasklog.status = 1
    except exceptions.NetworkError:
        tasklog.message = "NetworkError"
        tasklog.status = 1
    except:
        fail = "Unknow exeption :\n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        tasklog = TasksLog()
        tasklog.message = fail
        tasklog.status = 2

    tasklog.sonda = sonda
    tasklog.task = Task.objects.get(name="ssh_key")
    tasklog.timestamp = datetime.datetime.now()
    tasklog.save()

@shared_task
def send_checks(sonda_name, sonda_address, script):
    if Task.objects.filter(name="send_checks").count() == 0:
        task = Task()
        task.name = "send_checks"
        task.description = "send the script to a sonda and configure cron to execute the script"
        task.save()
    tasklog = TasksLog()
    try:
        crontabtemplate = 'echo "*/$2 * * * * root /root/$1 $2" >> /etc/crontab'
        env.skip_bad_hosts = True
        env.abort_on_prompts = True
        #env.abort_exception =
        env.user = "root"
        env.host_string = str(sonda_address)
        env.key_filename = settings.PROJECT_ROOT + '/keys/id_rsa'
        put("scripts/checks-" + sonda_name + ".sh", "/root/" + "checks-" + sonda_name + ".sh")

        for i in script.keys():
            crontab = crontabtemplate.replace("$2", str(i))
            run(crontab.replace("$1", "checks-" + sonda_name + ".sh "))

        run("chmod +x /root/" + "checks-" + sonda_name + ".sh")


        tasklog.message = "Checks send to " + sonda_name
        tasklog.status = 0

    except exceptions.CommandTimeout:
        tasklog.message = "CommandTimeout"
        tasklog.status = 1
    except exceptions.NetworkError:
        tasklog.message = "NetworkError"
        tasklog.status = 1
    except:
        fail = "Unknow exeption :\n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        tasklog.message = fail
        tasklog.status = 2

    tasklog.sonda = Sonda.objects.get(name=sonda_name)
    tasklog.task = Task.objects.get(name="send_checks")
    tasklog.timestamp = datetime.datetime.now()
    tasklog.save()
