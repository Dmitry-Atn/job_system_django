from django.shortcuts import render, redirect
from .models import Job
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .services import JobRunner
from django.contrib import messages



def run_task(request, pk):
    message = JobRunner().run_job(pk)
    if message:
        messages.warning(request, message)
    return redirect('job-list')

class JobListView(ListView):

    template_name = 'job/joblist.html'
    context_object_name = 'jobs'
    ordering = ['crated']

    def get_queryset(self):
        return Job.objects.all()


class JobUpdateView(UpdateView):
    model = Job
    fields = ['description', 'document', 'scheduling']

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


class JobDeleteView(DeleteView):
    model = Job

    def get_success_url(self):
        return reverse('job-list')

