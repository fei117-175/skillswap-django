# Generated by Django 5.2.1 on 2025-06-23 07:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0003_alter_user_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name_plural': 'Users'},
        ),
    ]
