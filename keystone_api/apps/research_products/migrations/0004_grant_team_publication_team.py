# Generated by Django 5.1.2 on 2024-10-12 14:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research_products', '0003_remove_grant_group_remove_publication_group'),
        ('users', '0009_team_teammembership_team_users_delete_researchgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='grant',
            name='team',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.team'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publication',
            name='team',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.team'),
            preserve_default=False,
        ),
    ]
