# Generated by Django 5.1.2 on 2024-11-13 17:36

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('allocations', '0010_rename_file_data_attachment_path'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AllocationRequestReview',
            new_name='AllocationReview',
        ),
    ]
