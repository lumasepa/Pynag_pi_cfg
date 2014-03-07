from __future__ import absolute_import

from celery import shared_task
from fabric.api import env, run, put
from fabric.contrib.files import exists
from django.conf import settings
from fabric import exceptions
from main.models import Sonda
from tasklog.models import TasksLog, Task, TaskStatus
import sys
import datetime

@shared_task
def ssh_key_task(sonda_pk, user, passwd, tasklog_pk):
    sonda = Sonda.objects.get(pk=sonda_pk)
    if Task.objects.get(name="ssh_key") is None:
        task = Task()
        task.name = "ssh_key"
        task.description = "send the ssh key to a sonda"
        task.save()
    if tasklog_pk is None:
        tasklog = TasksLog()
        tasklog.sonda = sonda
        tasklog.task = Task.objects.get(name="ssh_key")
        tasklog.save()
    else:
        tasklog = TasksLog.objects.get(pk=tasklog_pk)
    taskstatus = TaskStatus()
    taskstatus.tasklog = tasklog

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
        taskstatus.message = "Config done with " + sonda.name
        taskstatus.status = 0
    except exceptions.CommandTimeout:
        taskstatus.message = "CommandTimeout"
        taskstatus.status = 1
    except exceptions.NetworkError:
        taskstatus.message = "NetworkError"
        taskstatus.status = 1
    except:
        fail = "Unknow exeption :\n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        taskstatus.message = fail
        taskstatus.status = 2

    taskstatus.timestamp = datetime.datetime.now()
    taskstatus.save()

@shared_task
def send_checks(sonda_pk, script, tasklog_pk):
    sonda = Sonda.objects.get(pk=sonda_pk)
    if Task.objects.filter(name="send_checks").count() == 0:
        task = Task()
        task.name = "send_checks"
        task.description = "send the script to a sonda and configure cron to execute the script"
        task.save()
    if tasklog_pk is None:
        tasklog = TasksLog()
        tasklog.sonda = sonda
        tasklog.task = Task.objects.get(name="send_checks")
        tasklog.save()
    else:
        tasklog = TasksLog.objects.get(pk=tasklog_pk)
    taskstatus = TaskStatus()
    taskstatus.tasklog = tasklog

    try:
        crontabtemplate = 'echo "*/$2 * * * * root /root/$1 $2" >> /etc/crontab'
        env.skip_bad_hosts = True
        env.abort_on_prompts = True
        env.user = "root"
        env.host_string = str(sonda.address)
        env.key_filename = settings.PROJECT_ROOT + '/keys/id_rsa'
        put("scripts/checks-" + sonda.name + ".sh", "/root/" + "checks-" + sonda.name + ".sh")

        for i in script.keys():
            crontab = crontabtemplate.replace("$2", str(i))
            run(crontab.replace("$1", "checks-" + sonda.name + ".sh "))

        run("chmod +x /root/" + "checks-" + sonda.name + ".sh")

        taskstatus.message = "Checks send to " + sonda.name
        taskstatus.status = 0

    except exceptions.CommandTimeout:
        taskstatus.message = "CommandTimeout"
        taskstatus.status = 1
    except exceptions.NetworkError:
        taskstatus.message = "NetworkError"
        taskstatus.status = 1
    except:
        fail = "Unknow exeption :\n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        taskstatus.message = fail
        taskstatus.status = 2

    taskstatus.timestamp = datetime.datetime.now()
    taskstatus.save()
