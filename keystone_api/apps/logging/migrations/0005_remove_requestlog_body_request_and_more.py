# Generated by Django 5.1.2 on 2024-12-10 17:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logging', '0004_alter_requestlog_endpoint'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requestlog',
            name='body_request',
        ),
        migrations.RemoveField(
            model_name='requestlog',
            name='body_response',
        ),
    ]
