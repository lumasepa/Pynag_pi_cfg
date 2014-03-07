from django import forms
from main.models import HostsServicesSondas
from tasklog.models import TasksLog, TaskStatus, Task
from django.contrib import admin
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages
from os import path, system
import sys
from main.tasks import ssh_key_task, send_checks
from django.conf import settings
from django.template import Template, Context


class TaskStatusInline(admin.StackedInline):
    model = TaskStatus
    ordering = ("timestamp",)
    readonly_fields = ("timestamp", "message", "status")


class TaskLogAdmin(admin.ModelAdmin):
    search_fields = ['task',  'sonda']
    list_display = ('task',  'sonda')
    actions = ['ressh_key', 'resend_checks']
    inlines = [TaskStatusInline, ]
    readonly_fields = ('task', 'sonda')

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
                        if (tasklog.sonda.ssh == False or request.POST.get("force", '') != '') and tasklog.task.name == "ssh_key":
                            last_timestamp = max([i.timestamp for i in TaskStatus.objects.filter(tasklog=tasklog)])
                            taskstatus = TaskStatus.objects.get(timestamp=last_timestamp, tasklog=tasklog)
                            if taskstatus.status > 0:
                                ssh_key_task.apply_async((tasklog.sonda.pk, user, password, tasklog.pk), serializer="json")
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
        return render_to_response('confssh.html', {"form": form, "action": "ressh_key"}, context_instance=RequestContext(request))

    ressh_key.short_description = "resend key to failed"

    def resend_checks(self, request, queryset):
        scripts = {}
        sondas = []
        tasklog_list = []
        sondas_actualizadas = 0
        for tasklog in TasksLog.objects.all():
            if tasklog.task.name == "send_checks":
                last_timestamp = max([i.timestamp for i in TaskStatus.objects.filter(tasklog=tasklog)])
                taskstatus = TaskStatus.objects.get(timestamp=last_timestamp, tasklog=tasklog)
                if taskstatus.status > 0:
                    sondas.append(tasklog.sonda)
                    tasklog_list.append(tasklog)
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
        for i in range(0, len(sondas)):
            send_checks.apply_async((sondas[i].pk, scripts[sondas[i].name], tasklog_list[i].pk), serializer="json")

        messages.info(request, str(sondas_actualizadas) + ' sondas have been pushed to the task queue')
        return HttpResponseRedirect(request.get_full_path())

    resend_checks.short_description = "resend checks to failed"

admin.site.register(TasksLog, TaskLogAdmin)


class TaskAdmin(admin.ModelAdmin):
    search_fields = ['name',  'description']
    list_display = ('name',  'description')

admin.site.register(Task, TaskAdmin)