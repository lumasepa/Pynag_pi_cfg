from __future__ import absolute_import

from celery import shared_task
from fabric.api import env, run, put
from fabric.contrib.files import exists
from django.conf import settings
from main.models import Sonda, HostsServicesSondas
from tasklog.models import TasksLog, Task, TaskStatus
import sys
import datetime
from django.template import Template, Context



@shared_task
def ssh_key_send_task(sonda_pk, user, passwd, tasklog_pk):
    sonda = Sonda.objects.get(pk=sonda_pk)
    if Task.objects.filter(name="ssh_key").count() == 0:
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
    except Exception as e:
        taskstatus.message = e.message
        taskstatus.status = 1
    except:
        fail = "Unknow exeption !\n sys exc info : \n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        taskstatus.status = 2

    taskstatus.timestamp = datetime.datetime.now()
    taskstatus.save()


@shared_task
def send_nrpecfg(sonda_pk, tasklog_pk):
    sonda = Sonda.objects.get(pk=sonda_pk)
    if Task.objects.filter(name="send_nrpecfg").count() == 0:
        task = Task()
        task.name = "send_nrpecfg"
        task.description = "send the script to a sonda and configure cron to execute the script"
        task.save()
    if tasklog_pk is None:
        tasklog = TasksLog()
        tasklog.sonda = sonda
        tasklog.task = Task.objects.get(name="send_nrpecfg")
        tasklog.save()
    else:
        tasklog = TasksLog.objects.get(pk=tasklog_pk)
    taskstatus = TaskStatus()
    taskstatus.tasklog = tasklog

    try:
        data = {"NAGIOS_SERVER": sonda.servidor_nagios, "checks": []}
        custom_checks = []
        for hostservicesonda in HostsServicesSondas.objects.filter(sonda=sonda):
            data["checks"].append("[" + sonda.name + "_" +
                                  hostservicesonda.service.name + "_" +
                                  hostservicesonda.host.name + "]=" +
                                  sonda.dir_checks + "/" +
                                  hostservicesonda.service.command.replace("$HOST", hostservicesonda.host.address))
            if not hostservicesonda.service.command_nativo:
                f = open("tmp/" + hostservicesonda.service.name, "w")
                f.write(hostservicesonda.service.command_script.replace("$HOST", hostservicesonda.host.name))
                f.close()
                custom_checks.append(hostservicesonda.service.name)

        f = open("templates/nrpe.cfg", "r")
        template = Template(f.read())
        f.close()

        nrpecfg = open("tmp/nrpe.cfg", "w")
        nrpecfg.write(template.render(Context(data)))
        nrpecfg.close()

        env.skip_bad_hosts = True
        env.abort_on_prompts = True
        env.user = "root"
        env.host_string = str(sonda.address)
        env.key_filename = settings.PROJECT_ROOT + '/keys/id_rsa'
        put("tmp/nrpe.cfg", "/etc/nagios/nrpe.cfg")
        for check in custom_checks:
            put("tmp/" + check, sonda.dir_checks + "/check_" + check)  # FAIL = Problem Space in rpi !!
            run("chmod +x " + sonda.dir_checks + "/check_" + check)

        run("service " + sonda.nrpe_service_name + " restart")

        taskstatus.message = "nrpe.cfg send to" + sonda.name
        taskstatus.status = 0

    except Exception as e:
        taskstatus.message = e.message
        taskstatus.status = 1
    except:
        fail = "Unknow exeption !\n sys exc info : \n"
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        taskstatus.status = 2

    taskstatus.timestamp = datetime.datetime.now()
    taskstatus.save()
