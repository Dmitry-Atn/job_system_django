# Generated by Django 2.2.1 on 2019-05-19 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0004_auto_20190519_2130'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='description',
            field=models.CharField(max_length=1024),
        ),
        migrations.AlterField(
            model_name='job',
            name='document',
            field=models.TextField(blank=True, max_length=10240),
        ),
    ]
