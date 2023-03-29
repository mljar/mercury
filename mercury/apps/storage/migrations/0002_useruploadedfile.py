# Generated by Django 3.2.5 on 2023-03-29 09:06

import apps.accounts.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserUploadedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=1024)),
                ('filepath', models.CharField(max_length=1024)),
                ('session_id', models.CharField(max_length=128)),
                ('created_at', apps.accounts.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False)),
                ('hosted_on', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.site')),
            ],
        ),
    ]
