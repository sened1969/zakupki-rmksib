"""
Django модели для админ-панели.
Соответствуют SQLAlchemy моделям из database/models.py
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

# JSONField доступен напрямую в Django 3.1+
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField


class User(models.Model):
    """Пользователи системы"""
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    
    id = models.AutoField(primary_key=True)
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name='Username')
    full_name = models.CharField(max_length=255, verbose_name='Полное имя')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='user', verbose_name='Роль')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создан')
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name='Последний визит')
    contact_email = models.EmailField(null=True, blank=True, verbose_name='Email')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} (@{self.username or 'без username'})"


class UserPreference(models.Model):
    """Настройки пользователя"""
    SMTP_PROVIDER_CHOICES = [
        ('yandex', 'Yandex'),
        ('gmail', 'Gmail'),
        ('mailru', 'Mail.ru'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences', verbose_name='Пользователь')
    notify_enabled = models.BooleanField(default=True, verbose_name='Уведомления включены')
    customers = models.JSONField(null=True, blank=True, verbose_name='Заказчики')
    nomenclature = models.JSONField(null=True, blank=True, verbose_name='Номенклатура')
    email_password = models.TextField(null=True, blank=True, verbose_name='Пароль email (зашифрован)')
    smtp_provider = models.CharField(max_length=50, choices=SMTP_PROVIDER_CHOICES, null=True, blank=True, verbose_name='SMTP провайдер')
    budget_min = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)], verbose_name='Минимальный бюджет (руб.)')
    budget_max = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)], verbose_name='Максимальный бюджет (руб.)')
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'Настройки пользователя'
        verbose_name_plural = 'Настройки пользователей'
    
    def __str__(self):
        return f"Настройки {self.user.full_name}"


class Lot(models.Model):
    """Лоты (закупки)"""
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('closed', 'Закрыт'),
        ('pending', 'В ожидании'),
        ('rejected', 'Отклонен'),
    ]
    
    REVIEW_STATUS_CHOICES = [
        ('not_viewed', 'Не просмотрен'),
        ('in_work', 'В работе'),
        ('rejected', 'Отказ'),
    ]
    
    SOURCE_CHOICES = [
        ('parser', 'Парсер'),
        ('email', 'Email'),
        ('manual', 'Вручную'),
    ]
    
    id = models.AutoField(primary_key=True)
    platform_name = models.CharField(max_length=100, verbose_name='Платформа')
    lot_number = models.CharField(max_length=100, unique=True, verbose_name='Номер лота')
    title = models.TextField(verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    budget = models.FloatField(validators=[MinValueValidator(0)], verbose_name='Бюджет (руб.)')
    deadline = models.DateTimeField(verbose_name='Дедлайн')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создан')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    review_status = models.CharField(max_length=50, choices=REVIEW_STATUS_CHOICES, null=True, blank=True, default='not_viewed', verbose_name='Статус просмотра')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lots', verbose_name='Владелец')
    customer = models.CharField(max_length=255, null=True, blank=True, verbose_name='Заказчик')
    nomenclature = models.JSONField(null=True, blank=True, verbose_name='Номенклатура')
    documentation_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='Путь к документации')
    documentation_text = models.TextField(null=True, blank=True, verbose_name='Текст документации')
    documentation_analyzed = models.BooleanField(default=False, verbose_name='Документация проанализирована')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, null=True, blank=True, verbose_name='Источник')
    url = models.URLField(max_length=500, null=True, blank=True, verbose_name='URL')
    
    class Meta:
        db_table = 'lots'
        verbose_name = 'Лот'
        verbose_name_plural = 'Лоты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lot_number']),
            models.Index(fields=['status']),
            models.Index(fields=['review_status']),
            models.Index(fields=['deadline']),
        ]
    
    def __str__(self):
        return f"{self.lot_number} - {self.title[:50]}"
    
    @property
    def is_expired(self):
        """Проверка, просрочен ли лот"""
        return timezone.now() > self.deadline


class Supplier(models.Model):
    """Поставщики"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    inn = models.CharField(max_length=12, unique=True, verbose_name='ИНН')
    contact_email = models.EmailField(verbose_name='Email')
    contact_phone = models.CharField(max_length=20, verbose_name='Телефон')
    reliability_rating = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Рейтинг надежности')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создан')
    
    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['-reliability_rating', 'name']
    
    def __str__(self):
        return f"{self.name} (ИНН: {self.inn})"


class CommercialProposal(models.Model):
    """Коммерческие предложения"""
    id = models.AutoField(primary_key=True)
    lot = models.ForeignKey(Lot, on_delete=models.SET_NULL, null=True, blank=True, related_name='commercial_proposals', verbose_name='Лот')
    supplier_name = models.CharField(max_length=255, verbose_name='Название поставщика')
    supplier_inn = models.CharField(max_length=12, null=True, blank=True, verbose_name='ИНН поставщика')
    proposal_file_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='Путь к файлу КП')
    proposal_text = models.TextField(null=True, blank=True, verbose_name='Текст КП')
    product_price = models.FloatField(validators=[MinValueValidator(0)], verbose_name='Цена товара (руб.)')
    delivery_cost = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)], verbose_name='Стоимость доставки (руб.)')
    other_conditions = models.TextField(null=True, blank=True, verbose_name='Прочие условия')
    items_count = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)], verbose_name='Количество наименований')
    supplier_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)], verbose_name='Рейтинг поставщика (0-100)')
    supplier_reliability_info = models.TextField(null=True, blank=True, verbose_name='Информация о надежности')
    integral_rating = models.FloatField(null=True, blank=True, verbose_name='Интегральный рейтинг')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commercial_proposals', verbose_name='Создано пользователем')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создано')
    analyzed_at = models.DateTimeField(null=True, blank=True, verbose_name='Проанализировано')
    
    class Meta:
        db_table = 'commercial_proposals'
        verbose_name = 'Коммерческое предложение'
        verbose_name_plural = 'Коммерческие предложения'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier_name']),
            models.Index(fields=['integral_rating']),
        ]
    
    def __str__(self):
        return f"КП от {self.supplier_name} - {self.product_price:,.0f} руб."
    
    @property
    def total_price(self):
        """Общая стоимость (товар + доставка)"""
        return self.product_price + (self.delivery_cost or 0)

