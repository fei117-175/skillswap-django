# Generated by Django 5.2.1 on 2025-06-24 03:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangerequest',
            name='accepted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accepted_exchanges', to=settings.AUTH_USER_MODEL, verbose_name='接受交换的用户'),
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='applicant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exchange_requests', to=settings.AUTH_USER_MODEL, verbose_name='申请人'),
        ),
        migrations.AlterField(
            model_name='exchangerequest',
            name='apl_status',
            field=models.CharField(blank=True, choices=[('pending', '待处理'), ('rejected', '已拒绝'), ('completed', '已完成'), ('matched', '已匹配')], default='pending', max_length=20, verbose_name='申请状态'),
        ),
    ]
