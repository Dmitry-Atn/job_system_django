from django.db import models
from datetime import datetime

# Create your models here.


class Job(models.Model):
    STATUS_RUNNING = "running"
    STATUS_FAILED = "failed"
    STATUS_READY = "ready"
    STATUS_CHOICES = (
        (STATUS_RUNNING, 'Running'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_READY, 'Ready')
    )
    SCHEDULE_NONE = 0
    SCHEDULE_1H = 1
    SCHEDULE_2H = 2
    SCHEDULE_6H = 6
    SCHEDULE_12H = 12
    SCHEDULE_CHOICES = (
        (SCHEDULE_NONE, 'none'),
        (SCHEDULE_1H, '1 hour'),
        (SCHEDULE_2H, '2 hours'),
        (SCHEDULE_6H, '6 hours'),
        (SCHEDULE_12H, '12 hours')
    )

    description = models.CharField(max_length=1024)
    created = models.DateTimeField(auto_now_add=True)
    last_executed = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_READY)
    document = models.TextField(max_length=10240, blank=True)
    scheduling = models.IntegerField(choices=SCHEDULE_CHOICES, default=SCHEDULE_NONE)

    def is_runnable(self):
        return self.status != Job.STATUS_RUNNING

    def __str__(self):
        return f'{self.pk}: {self.last_executed} {self.document} {self.status}'
