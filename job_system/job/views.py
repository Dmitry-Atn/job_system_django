from django.shortcuts import render
from .models import Job
from django.views.generic import ListView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .services import JobRunner


def run_task(request, pk):
    JobRunner().run_job(pk)
    return render(request, 'job/joblist.html', {'jobs': Job.objects.all()})


class JobListView(ListView):

    template_name = 'job/joblist.html'
    context_object_name = 'jobs'
    ordering = ['crated']

    def get_queryset(self):
        return Job.objects.all()


class JobUpdateView(UpdateView):
    model = Job
    fields = ['description', 'scheduling']

    def get_success_url(self):
        return reverse('job-list')


class JobCreateView(CreateView):
    model = Job
    fields = [
        'description',
        'document',
        'scheduling',
    ]

    def get_success_url(self):
        return reverse('job-list')
