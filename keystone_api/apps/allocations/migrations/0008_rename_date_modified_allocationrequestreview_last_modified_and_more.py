# Generated by Django 5.1.2 on 2024-10-11 20:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allocations', '0007_alter_allocationrequestreview_reviewer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='allocationrequestreview',
            old_name='date_modified',
            new_name='last_modified',
        ),
        migrations.AddField(
            model_name='allocationrequest',
            name='submitter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_allocationrequest_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='allocationrequest',
            name='assignees',
            field=models.ManyToManyField(blank=True, related_name='assigned_allocationrequest_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
