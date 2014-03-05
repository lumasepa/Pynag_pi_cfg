from __future__ import absolute_import

from celery import shared_task
from fabric.api import env, run, put
from fabric.contrib.files import exists
import os


@shared_task
def ssh_key(sonda, user, passwd):
    env.user = user
    env.password = passwd
    env.host_string = str(sonda.address)
    if not exists('/root/.ssh/'):
        run("mkdir /root/.ssh")
    if not exists('/root/.ssh/authorized_keys/'):
        run("mkdir /root/.ssh/authorized_keys")
    put(os.getcwd()+"/keys/id_rsa", "/root/.ssh/authorized_keys/id_rsa")
    sonda.ssh = True
    sonda.save()


@shared_task
def send_checks(sonda):
    pass

