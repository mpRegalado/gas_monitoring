# Generated by Django 3.0.8 on 2020-07-17 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('readings', '0003_auto_20200717_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='name',
            field=models.CharField(default='2020-07-17 17:31:38.031439+00:00', max_length=200),
        ),
    ]
