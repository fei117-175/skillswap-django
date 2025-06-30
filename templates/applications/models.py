from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()
class ExchangeRequest(models.Model):
    # 申请状态选项
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('waiting','待回应'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
        ('canceled','已取消'),
        ('overdue','已过期'),
        ('matched', '已匹配'),  # 新增状态
    ]

    # 关联用户模型
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name='exchange_requests',
        verbose_name='申请人'
    )

    # 新增：同意交换的用户
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # 用户删除时保留记录但设为NULL
        null=True,
        blank=True,
        related_name='accepted_exchanges',
        verbose_name='接受交换的用户'
    )

    # 课程信息字段
    course = models.CharField('课程名称', max_length=100)
    course_category = models.CharField('课程大类', max_length=50)
    course_subcategory = models.CharField('课程子类', max_length=50)

    # 技能交换字段
    skill = models.CharField('提供技能', max_length=100)
    skill_category = models.CharField('技能大类', max_length=50)
    skill_subcategory = models.CharField('技能子类', max_length=50)

    # 时间字段
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')

    # 描述信息
    description = models.TextField('详细描述', blank=True)

    # 状态字段
    apl_status = models.CharField(
        '申请状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        blank=True
    )

    # 自动时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '技能交换申请'
        verbose_name_plural = '技能交换申请'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.applicant.username}的{self.course}申请 (状态: {self.get_apl_status_display()})"


