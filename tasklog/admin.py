from django import forms
from tasklog.models import TasksLog, TaskStatus, Task
from django.contrib import admin
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages
from os import path, system
import sys
from main.tasks import ssh_key_send_task, send_nrpecfg
from django.conf import settings


class TaskStatusInline(admin.StackedInline):
    model = TaskStatus
    ordering = ("timestamp",)
    readonly_fields = ("timestamp", "message", "status")


class TaskLogAdmin(admin.ModelAdmin):
    search_fields = ['task',  'sonda']
    list_display = ('task',  'sonda')
    actions = ['resend_shh_key', 'resend_nrpecfg']
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

    def resend_shh_key(self, request, queryset):
        form = None
        if 'apply' in request.POST:
            form = self.SshForm(request.POST)
            if form.is_valid():
                try:
                    if not path.isfile(settings.PROJECT_ROOT + "/keys/id_rsa"):
                        system("ssh-keygen -t rsa -f " + settings.PROJECT_ROOT + "/keys/id_rsa -N ''")
                    sondas_updated = 0
                    user = request.POST["user"]
                    password = request.POST["passwd"]

                    for tasklog in TasksLog.objects.all():
                        if (tasklog.sonda.ssh == False or request.POST.get("force", '') != '') and tasklog.task.name == "ssh_key":
                            last_timestamp = max([i.timestamp for i in TaskStatus.objects.filter(tasklog=tasklog)])
                            taskstatus = TaskStatus.objects.get(timestamp=last_timestamp, tasklog=tasklog)
                            if taskstatus.status > 0:
                                ssh_key_send_task.apply_async((tasklog.sonda.pk, user, password, tasklog.pk), serializer="json")
                                sondas_updated += 1
                except:
                    fails = "\n"
                    for fail in sys.exc_info()[0:5]:
                        fails = fails + str(fail) + "\n"
                    messages.error(request, 'Error :' + fails)
                    return HttpResponseRedirect(request.get_full_path())

                messages.info(request, str(sondas_updated) + ' sondas have been pushed to the task queue')
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = self.SshForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render_to_response('confssh.html', {"form": form, "action": "resend_shh_key"}, context_instance=RequestContext(request))

    resend_shh_key.short_description = "resend key to failed"

    def resend_nrpecfg(self, request, queryset):
        sondas = []
        tasklog_list = []
        sondas_updated = 0
        for tasklog in TasksLog.objects.all():
            if tasklog.task.name == "send_nrpecfg":
                if TaskStatus.objects.filter(tasklog=tasklog).count() == 1:
                    last_timestamp = TaskStatus.objects.get(tasklog=tasklog).timestamp
                else:
                    last_timestamp = max([i.timestamp for i in TaskStatus.objects.filter(tasklog=tasklog)])
                taskstatus = TaskStatus.objects.get(timestamp=last_timestamp, tasklog=tasklog)
                if taskstatus.status > 0:
                    sondas.append(tasklog.sonda)
                    tasklog_list.append(tasklog)
                    sondas_updated += 1

        if sondas_updated == 0:
            messages.info(request, str(sondas_updated) + ' sondas have been pushed to the task queue')
            return HttpResponseRedirect(request.get_full_path())

        for i in range(0, len(sondas)):
            send_nrpecfg.apply_async((sondas[i].pk, tasklog_list[i].pk), serializer="json")


        messages.info(request, str(sondas_updated) + ' sondas have been pushed to the task queue')
        return HttpResponseRedirect(request.get_full_path())

    resend_nrpecfg.short_description = "resend nrpe.cfg to failed"


class TaskAdmin(admin.ModelAdmin):
    search_fields = ['name',  'description']
    list_display = ('name',  'description')


admin.site.register(TasksLog, TaskLogAdmin)
admin.site.register(Task, TaskAdmin)