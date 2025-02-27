# Generated by Django 5.1.5 on 2025-02-18 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research_products', '0003_remove_grant_group_remove_publication_group'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publication',
            old_name='date',
            new_name='published',
        ),
        migrations.AlterField(
            model_name='publication',
            name='published',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='publication',
            name='submitted',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='journal',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='publication',
            name='preparation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='publication',
            name='issue',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='publication',
            name='volume',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
