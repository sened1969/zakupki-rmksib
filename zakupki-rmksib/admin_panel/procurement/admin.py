"""
Django Admin конфигурация для моделей закупок
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import User, UserPreference, Lot, Supplier, CommercialProposal


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель для пользователей"""
    list_display = ['id', 'telegram_id', 'full_name', 'username', 'role', 'is_active', 'contact_email', 'created_at', 'last_seen']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['full_name', 'username', 'telegram_id', 'contact_email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_seen']
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'telegram_id', 'username', 'full_name', 'role', 'is_active')
        }),
        ('Контактная информация', {
            'fields': ('contact_email',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'last_seen')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """Админ-панель для настроек пользователей"""
    list_display = ['id', 'user_link', 'notify_enabled', 'smtp_provider', 'budget_min', 'budget_max', 'customers_count', 'nomenclature_count']
    list_filter = ['notify_enabled', 'smtp_provider']
    search_fields = ['user__full_name', 'user__username']
    readonly_fields = ['id']
    list_per_page = 50
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('id', 'user')
        }),
        ('Уведомления', {
            'fields': ('notify_enabled',)
        }),
        ('Фильтры', {
            'fields': ('customers', 'nomenclature', 'budget_min', 'budget_max')
        }),
        ('Email настройки', {
            'fields': ('smtp_provider', 'email_password')
        }),
    )
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            url = reverse('admin:procurement_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
        return '-'
    user_link.short_description = 'Пользователь'
    
    def customers_count(self, obj):
        """Количество заказчиков"""
        if obj.customers:
            return len(obj.customers) if isinstance(obj.customers, list) else '-'
        return 0
    customers_count.short_description = 'Заказчиков'
    
    def nomenclature_count(self, obj):
        """Количество номенклатурных групп"""
        if obj.nomenclature:
            return len(obj.nomenclature) if isinstance(obj.nomenclature, list) else '-'
        return 0
    nomenclature_count.short_description = 'Номенклатурных групп'


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    """Админ-панель для лотов"""
    list_display = ['lot_number', 'title_short', 'platform_name', 'budget_formatted', 'deadline', 'status_badge', 'review_status_badge', 'owner_link', 'is_expired_badge', 'created_at']
    list_filter = ['status', 'review_status', 'platform_name', 'source', 'created_at', 'deadline']
    search_fields = ['lot_number', 'title', 'description', 'customer']
    readonly_fields = ['id', 'created_at', 'is_expired_check']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'lot_number', 'platform_name', 'title', 'description', 'url')
        }),
        ('Финансы и сроки', {
            'fields': ('budget', 'deadline', 'is_expired_check')
        }),
        ('Статусы', {
            'fields': ('status', 'review_status', 'source')
        }),
        ('Детали', {
            'fields': ('customer', 'nomenclature', 'owner')
        }),
        ('Документация', {
            'fields': ('documentation_path', 'documentation_text', 'documentation_analyzed')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    
    def title_short(self, obj):
        """Короткое название"""
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Название'
    
    def budget_formatted(self, obj):
        """Форматированный бюджет"""
        return f"{obj.budget:,.0f} ₽"
    budget_formatted.short_description = 'Бюджет'
    budget_formatted.admin_order_field = 'budget'
    
    def status_badge(self, obj):
        """Бейдж статуса"""
        colors = {
            'active': 'green',
            'closed': 'gray',
            'pending': 'orange',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'blue')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def review_status_badge(self, obj):
        """Бейдж статуса просмотра"""
        if not obj.review_status:
            return '-'
        colors = {
            'not_viewed': 'gray',
            'in_work': 'blue',
            'rejected': 'red',
        }
        color = colors.get(obj.review_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_review_status_display()
        )
    review_status_badge.short_description = 'Просмотр'
    
    def owner_link(self, obj):
        """Ссылка на владельца"""
        if obj.owner:
            url = reverse('admin:procurement_user_change', args=[obj.owner.id])
            return format_html('<a href="{}">{}</a>', url, obj.owner.full_name)
        return '-'
    owner_link.short_description = 'Владелец'
    
    def is_expired_badge(self, obj):
        """Бейдж просроченности"""
        if obj.is_expired:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Просрочен</span>')
        return format_html('<span style="color: green;">✓ Активен</span>')
    is_expired_badge.short_description = 'Статус дедлайна'
    
    def is_expired_check(self, obj):
        """Проверка просроченности (readonly)"""
        return 'Да' if obj.is_expired else 'Нет'
    is_expired_check.short_description = 'Просрочен'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Админ-панель для поставщиков"""
    list_display = ['name', 'inn', 'contact_email', 'contact_phone', 'reliability_rating_badge', 'created_at']
    list_filter = ['reliability_rating', 'created_at']
    search_fields = ['name', 'inn', 'contact_email', 'contact_phone']
    readonly_fields = ['id', 'created_at']
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'name', 'inn')
        }),
        ('Контактная информация', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Рейтинг', {
            'fields': ('reliability_rating',)
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    
    def reliability_rating_badge(self, obj):
        """Бейдж рейтинга"""
        if obj.reliability_rating >= 80:
            color = 'green'
        elif obj.reliability_rating >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.reliability_rating
        )
    reliability_rating_badge.short_description = 'Рейтинг'
    reliability_rating_badge.admin_order_field = 'reliability_rating'


@admin.register(CommercialProposal)
class CommercialProposalAdmin(admin.ModelAdmin):
    """Админ-панель для коммерческих предложений"""
    list_display = ['id', 'supplier_name', 'supplier_inn', 'lot_link', 'product_price_formatted', 'delivery_cost_formatted', 'total_price_formatted', 'items_count', 'integral_rating_badge', 'created_by_link', 'created_at']
    list_filter = ['created_at', 'analyzed_at', 'supplier_rating']
    search_fields = ['supplier_name', 'supplier_inn', 'proposal_text']
    readonly_fields = ['id', 'created_at', 'analyzed_at', 'total_price_calc']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'lot', 'supplier_name', 'supplier_inn')
        }),
        ('Финансовые данные', {
            'fields': ('product_price', 'delivery_cost', 'total_price_calc', 'other_conditions')
        }),
        ('Детали', {
            'fields': ('items_count',)
        }),
        ('Анализ', {
            'fields': ('supplier_rating', 'supplier_reliability_info', 'integral_rating', 'analyzed_at')
        }),
        ('Файлы', {
            'fields': ('proposal_file_path', 'proposal_text')
        }),
        ('Метаданные', {
            'fields': ('created_by', 'created_at')
        }),
    )
    
    def lot_link(self, obj):
        """Ссылка на лот"""
        if obj.lot:
            url = reverse('admin:procurement_lot_change', args=[obj.lot.id])
            return format_html('<a href="{}">{}</a>', url, obj.lot.lot_number)
        return '-'
    lot_link.short_description = 'Лот'
    
    def product_price_formatted(self, obj):
        """Форматированная цена товара"""
        return f"{obj.product_price:,.0f} ₽"
    product_price_formatted.short_description = 'Цена товара'
    product_price_formatted.admin_order_field = 'product_price'
    
    def delivery_cost_formatted(self, obj):
        """Форматированная стоимость доставки"""
        if obj.delivery_cost:
            return f"{obj.delivery_cost:,.0f} ₽"
        return '-'
    delivery_cost_formatted.short_description = 'Доставка'
    
    def total_price_formatted(self, obj):
        """Форматированная общая стоимость"""
        return f"{obj.total_price:,.0f} ₽"
    total_price_formatted.short_description = 'Итого'
    
    def integral_rating_badge(self, obj):
        """Бейдж интегрального рейтинга"""
        if obj.integral_rating is None:
            return '-'
        if obj.integral_rating >= 80:
            color = 'green'
        elif obj.integral_rating >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{:.1f}</span>',
            color,
            obj.integral_rating
        )
    integral_rating_badge.short_description = 'Рейтинг'
    integral_rating_badge.admin_order_field = 'integral_rating'
    
    def created_by_link(self, obj):
        """Ссылка на создателя"""
        if obj.created_by:
            url = reverse('admin:procurement_user_change', args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by.full_name)
        return '-'
    created_by_link.short_description = 'Создано'
    
    def total_price_calc(self, obj):
        """Расчет общей стоимости (readonly)"""
        return f"{obj.total_price:,.0f} ₽"
    total_price_calc.short_description = 'Общая стоимость'

