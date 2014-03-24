from django.db import models


class Sonda(models.Model):
    name = models.CharField(max_length=200, unique=True)
    address = models.CharField(max_length=400)
    localizacion = models.CharField(max_length=300)
    ssh = models.BooleanField(default=False)
    dir_checks = models.CharField(default="/usr/lib/nagios/plugins", max_length=500, verbose_name="Directorio de plugings nagios")
    servidor_nagios = models.CharField(default="193.145.118.253", max_length=400)
    nrpe_service_name = models.CharField(default="nagios-nrpe-server", max_length=400)
    script_inicio = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=200, unique=True)
    command = models.CharField(default='check_xxx $HOST', max_length=500)
    command_nativo = models.BooleanField(default=False)
    command_script = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Host(models.Model):
    name = models.CharField(max_length=200, unique=True)
    address = models.CharField(max_length=400)

    def __unicode__(self):
        return self.name


class HostsServicesSondas(models.Model):
    host = models.ForeignKey(Host)
    service = models.ForeignKey(Service)
    sonda = models.ForeignKey(Sonda)
    check_every = models.IntegerField()
    contact = models.CharField(max_length=200)