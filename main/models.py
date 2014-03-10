from django.db import models


class Sonda(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)
    localizacion = models.CharField(max_length=300)
    ssh = models.BooleanField(default=False)
    dir_checks = models.CharField(default="/usr/lib/nagios/plugins", max_length=500, verbose_name="Directorio de plugings nagios")
    cfg_nsca = models.CharField(default="/etc/send_nsca.cfg", max_length=500, verbose_name="Archivo de configuracion nsca")
    servidor_nagios = models.CharField(default="193.145.118.253", max_length=400)

    def __unicode__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=200)
    command = models.TextField(default='MESSAGE=`$DIR_PLUGINGS/check_xxx $HOST`\nssend_nsca \"$HOST" "$SERVICE" "$?" "$MESSAGE" ')

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