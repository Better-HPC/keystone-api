# Generated by Django 4.2.7 on 2024-01-03 09:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_researchgroup_admins_and_more'),
        ('allocations', '0004_alter_proposal_submitted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalreview',
            name='reviewer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user'),
        ),
    ]
