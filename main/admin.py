from django import forms
from main.models import Host, Service, Sonda, HostsServicesSondas, TasksLog
from django.contrib import admin
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages
from os import path, system
import sys
from tasks import ssh_key_task, send_checks
from django.conf import settings
from django.template import Template, Context


class HostsServicesSondasInline(admin.StackedInline):
    model = HostsServicesSondas
    extra = 2
    pass


class ServiceAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']
    actions = ['set_by_block_host_sonda']

    class SetByBlockHostSonda(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        sonda = forms.ModelChoiceField(queryset=Sonda.objects.all())
        host = forms.ModelChoiceField(queryset=Host.objects.all())
        check_every = forms.IntegerField()
        contact = forms.CharField(max_length=200)

    def set_by_block_host_sonda(self, request, queryset):
        print(request.POST)
        form = None
        if 'apply' in request.POST:
            form = self.SetByBlockHostSonda(request.POST)
            if form.is_valid():
                for service in queryset:
                    hostservicesonda = HostsServicesSondas()
                    hostservicesonda.host = Host.objects.get(pk=request.POST["host"])
                    hostservicesonda.service = service
                    hostservicesonda.sonda = Sonda.objects.get(pk=request.POST["sonda"])
                    hostservicesonda.check_every = int(request.POST["check_every"])
                    hostservicesonda.contact = request.POST["contact"]
                    hostservicesonda.save()
                messages.info(request, 'hosts has been updated suscefully')
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = self.SetByBlockHostSonda(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render_to_response('setbyblockhostsonda.html', {"form": form}, context_instance=RequestContext(request))

    set_by_block_host_sonda.short_description = "set selected host & sonda"
    pass


class SondaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address']
    list_display = ('name', 'address')
    actions = ['set_by_block_service_host','ssh_key']

    class SetByBlockServiceHost(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        host = forms.ModelChoiceField(queryset=Host.objects.all())
        service = forms.ModelChoiceField(queryset=Service.objects.all())
        check_every = forms.IntegerField()
        contact = forms.CharField(max_length=200)

    def set_by_block_service_host(self, request, queryset):
        print(request.POST)
        form = None
        if 'apply' in request.POST:
            form = self.SetByBlockServiceHost(request.POST)
            if form.is_valid():
                for sonda in queryset:
                    hostservicesonda = HostsServicesSondas()
                    hostservicesonda.host = Host.objects.get(pk=request.POST["host"])
                    hostservicesonda.service = Service.objects.get(pk=request.POST["service"])
                    hostservicesonda.sonda = sonda
                    hostservicesonda.check_every = int(request.POST["check_every"])
                    hostservicesonda.contact = request.POST["contact"]
                    hostservicesonda.save()
                messages.info(request, 'hosts has been updated suscefully')
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = self.SetByBlockServiceHost(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render_to_response('setbyblockservicehost.html', {"form": form}, context_instance=RequestContext(request))

    set_by_block_service_host.short_description = "set selected service & host"

    class SshForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        user = forms.CharField(max_length=200)
        passwd = forms.CharField(widget=forms.PasswordInput)
        force = forms.BooleanField(required=False)

    def ssh_key(self, request, queryset):
        print(request.POST)
        form = None
        if 'apply' in request.POST:
            form = self.SshForm(request.POST)
            if form.is_valid():
                try:
                    if not path.isfile(settings.PROJECT_ROOT + "/keys/id_rsa"):
                        system("ssh-keygen -t rsa -f " + settings.PROJECT_ROOT + "/keys/id_rsa -N ''")
                    sondas_actualizadas = 0
                    user = request.POST["user"]
                    password = request.POST["passwd"]

                    for sonda in queryset:
                        if sonda.ssh == False or request.POST.get("force", '') != '':
                            ssh_key_task(sonda, user, password)
                            sondas_actualizadas += 1
                except:
                    fails = "\n"
                    for fail in sys.exc_info()[0:5]:
                        fails = fails + str(fail) + "\n"
                    messages.error(request, 'Error :' + fails)
                    return HttpResponseRedirect(request.get_full_path())

                messages.info(request, str(sondas_actualizadas) + ' sondas have been pushed to the task queue')
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.SshForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render_to_response('confssh.html', {"form": form}, context_instance=RequestContext(request))

    ssh_key.short_description = "send key"
    pass


class HostAdmin(admin.ModelAdmin):
    inlines = [HostsServicesSondasInline]
    search_fields = ['name', 'address']
    list_display = ('name', 'address')
    actions = ['set_by_block_service_sonda']

    class SetByBlockServiceSonda(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        sonda = forms.ModelChoiceField(queryset=Sonda.objects.all())
        service = forms.ModelChoiceField(queryset=Service.objects.all())
        check_every = forms.IntegerField()
        contact = forms.CharField(max_length=200)

    def set_by_block_service_sonda(self, request, queryset):
        print(request.POST)
        form = None
        if 'apply' in request.POST:
            form = self.SetByBlockServiceSonda(request.POST)
            if form.is_valid():
                for host in queryset:
                    hostservicesonda = HostsServicesSondas()
                    hostservicesonda.host = host
                    hostservicesonda.service = Service.objects.get(pk=request.POST["service"])
                    hostservicesonda.sonda = Sonda.objects.get(pk=request.POST["sonda"])
                    hostservicesonda.check_every = int(request.POST["check_every"])
                    hostservicesonda.contact = request.POST["contact"]
                    hostservicesonda.save()
                messages.info(request, 'hosts has been updated suscefully')
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = self.SetByBlockServiceSonda(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render_to_response('setbyblockservicesonda.html', {"form": form}, context_instance=RequestContext(request))

    set_by_block_service_sonda.short_description = "set selected service & sonda"
    pass


class HostsServicesSondasAdmin(admin.ModelAdmin):
    search_fields = ['host', 'service', 'sonda']
    list_display = ('host', 'service', 'sonda')


class TaskLogAdmin(admin.ModelAdmin):
    search_fields = ['task',  'sonda', 'status', 'timestamp']
    list_display = ('task',  'sonda', 'status',  'timestamp')
    actions = ['ressh_key', 'resend_checks']

    scriptSnippet = \
                """
            MESSAGE=`$DIR_PLUGINGS/$2`
            ssend_nsca "$HOST" "$SERVICE" "$?" "$MESSAGE"
            """

    class SshForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        user = forms.CharField(max_length=200)
        passwd = forms.CharField(widget=forms.PasswordInput)
        force = forms.BooleanField(required=False)

    def ressh_key(self, request, queryset):
        print(request.POST)
        form = None
        if 'apply' in request.POST:
            form = self.SshForm(request.POST)
            if form.is_valid():
                try:
                    if not path.isfile(settings.PROJECT_ROOT + "/keys/id_rsa"):
                        system("ssh-keygen -t rsa -f " + settings.PROJECT_ROOT + "/keys/id_rsa -N ''")
                    sondas_actualizadas = 0
                    user = request.POST["user"]
                    password = request.POST["passwd"]

                    for tasklog in TasksLog.objects.all():
                        if (tasklog.sonda.ssh == False or request.POST.get("force", '') != '') and tasklog.status > 0 and tasklog.task.name == "ssh_key":
                            ssh_key_task(tasklog.sonda, user, password)
                            sondas_actualizadas += 1
                            tasklog.status = -1
                            tasklog.save()
                except:
                    fails = "\n"
                    for fail in sys.exc_info()[0:5]:
                        fails = fails + str(fail) + "\n"
                    messages.error(request, 'Error :' + fails)
                    return HttpResponseRedirect(request.get_full_path())

                messages.info(request, str(sondas_actualizadas) + ' sondas have been pushed to the task queue')
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.SshForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render_to_response('confssh.html', {"form": form}, context_instance=RequestContext(request))

    ressh_key.short_description = "resend key to failed"

    def resend_checks(self, request, queryset):
        scripts = {}
        sondas = []
        sondas_actualizadas = 0
        for tasklog in TasksLog.objects.all():
            if tasklog.status > 0 and tasklog.task.name == "send_checks":
                sondas.append(tasklog.sonda)
                tasklog.status = -1
                tasklog.save()
                failed = True
                sondas_actualizadas += 1

        if sondas_actualizadas == 0:
            messages.info(request, str(sondas_actualizadas) + ' sondas have been pushed to the task queue')
            return HttpResponseRedirect(request.get_full_path())

        for sonda in sondas:
            scripts[sonda.name] = {}

            for hostservicesonda in HostsServicesSondas.objects.filter(sonda=sonda):
                if not int(hostservicesonda.check_every/60) in scripts[sonda.name]:
                    if int(hostservicesonda.check_every/60) == 0:
                            hostservicesonda.check_every = 60
                            hostservicesonda.save()
                    scripts[hostservicesonda.sonda.name][int(hostservicesonda.check_every/60)] = []

                if hostservicesonda.service.pluging:
                    snipet = self.scriptSnippet.replace("$2", hostservicesonda.service.command)
                    snipet = snipet.replace("$HOST", hostservicesonda.host.address)
                    snipet = snipet.replace("$SERVICE", hostservicesonda.service.name + "_" + hostservicesonda.sonda.name)
                    scripts[sonda.name][int(hostservicesonda.check_every/60)].append(snipet)
                else:
                    scripts[sonda.name][int(hostservicesonda.check_every/60)].append(hostservicesonda.service.command.replace("$HOST", hostservicesonda.host.address))

        ## Render template

        f = open("templates/check_template.sh", "r")
        template = Template(f.read())
        f.close()

        for sonda in sondas:
            script = open("scripts/checks-" + sonda.name + ".sh", "w")
            script.write(template.render(Context({
                "NSCA_CONF_FILE": "/etc/send_nsca.cfg",
                "DIR_PLUGINGS": "/usr/lib/nagios/plugins",
                "NAGIOS_SERVER": "193.145.118.253",
                "checks": scripts[sonda.name].iteritems(),
            })))
            script.close()
        ## End Render

        ## Send Scripts
        for sonda in sondas:
            send_checks(sonda, scripts[sonda.name])

        messages.info(request, str(sondas_actualizadas) + ' sondas have been pushed to the task queue')
        return HttpResponseRedirect(request.get_full_path())

    resend_checks.short_description = "resend checks to failed"


admin.site.register(Host, HostAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Sonda, SondaAdmin)
admin.site.register(HostsServicesSondas, HostsServicesSondasAdmin)
admin.site.register(TasksLog, TaskLogAdmin)