# Generated by Django 5.1.5 on 2025-03-31 21:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_team_teammembership_team_users_delete_researchgroup'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TeamMembership',
            new_name='Membership',
        ),
    ]
