from django import forms
from main.models import Host, Service, Sonda, HostsServicesSondas
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
    readonly_fields = ["ssh", ]

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
                            ssh_key_task.apply_async((sonda.pk, user, password, None), serializer="json")
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
        return render_to_response('confssh.html', {"form": form, "action": "ssh_key"}, context_instance=RequestContext(request))

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

admin.site.register(Host, HostAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Sonda, SondaAdmin)
admin.site.register(HostsServicesSondas, HostsServicesSondasAdmin)
