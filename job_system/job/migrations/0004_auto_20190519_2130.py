# Generated by Django 2.2.1 on 2019-05-19 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0003_auto_20190514_1923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='last_executed',
            field=models.DateTimeField(null=True),
        ),
    ]
