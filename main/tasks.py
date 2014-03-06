from __future__ import absolute_import

from celery import shared_task
from fabric.api import env, run, put
from fabric.contrib.files import exists
from django.conf import settings
import os
import sys


@shared_task
def ssh_key_task(sonda, user, passwd):
    env.user = user
    env.password = passwd
    env.host_string = str(sonda.address)
    if not exists('/root/.ssh/'):
        run("mkdir /root/.ssh")
    if not exists('/root/.ssh/authorized_keys/'):
        run("mkdir /root/.ssh/authorized_keys")
    put(settings.PROJECT_ROOT + "/keys/id_rsa", "/root/.ssh/authorized_keys/id_rsa")
    sonda.ssh = True
    sonda.save()
    print("Config done with " + sonda.name)


@shared_task
def send_checks(sonda, script):
    try:
        crontabtemplate = 'echo "*/$2 * * * * root /root/$1 $2" >> /etc/crontab'
        print(sonda.address)
        env.host_string = str(sonda.address)
        env.user = "root"
        print(settings.PROJECT_ROOT + '/keys/id_rsa.pub')
        env.key_filename = settings.PROJECT_ROOT + '/keys/id_rsa.pub'
        print(env.key_filename)
        put(settings.PROJECT_ROOT + "/scripts/checks-" + sonda.name + ".sh", "/root/" + "checks-" + sonda.name + ".sh")

        for i in script.keys():
            crontab = crontabtemplate.replace("$2", str(i))
            run(crontab.replace("$1", "checks-" + sonda.name + ".sh "))

        run("chmod +x /root/" + "checks-" + sonda.name + ".sh")

    except :
        fail = ""
        for fails in sys.exc_info()[0:5]:
            fail += str(fails) + "\n"
        print (fail)
        pass

