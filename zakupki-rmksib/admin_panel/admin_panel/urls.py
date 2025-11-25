"""
URL configuration for admin_panel project.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Добавляем поддержку медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Кастомизация админ-панели
admin.site.site_header = "Админ-панель Закупки РМКСИБ"
admin.site.site_title = "Закупки РМКСИБ"
admin.site.index_title = "Панель управления"

