from django.contrib import admin
from .models import Park, Sign, Visit, VisitPhoto


class VisitPhotoInline(admin.TabularInline):
    model = VisitPhoto
    extra = 1


class VisitInline(admin.TabularInline):
    model = Visit
    extra = 0
    show_change_link = True


class SignInline(admin.TabularInline):
    model = Sign
    extra = 0
    show_change_link = True
    fields = ['sign_type', 'latitude', 'longitude', 'is_visited']
    readonly_fields = ['is_visited']

    def is_visited(self, obj):
        return obj.is_visited
    is_visited.boolean = True


@admin.register(Sign)
class SignAdmin(admin.ModelAdmin):
    list_display = ['park', 'sign_type', 'latitude', 'longitude', 'is_visited', 'visit_count']
    list_filter = ['sign_type', 'park__neighborhood']
    search_fields = ['park__name']
    raw_id_fields = ['park']

    def is_visited(self, obj):
        return obj.is_visited
    is_visited.boolean = True
    is_visited.short_description = 'Visited'


@admin.register(Park)
class ParkAdmin(admin.ModelAdmin):
    list_display = ['name', 'neighborhood', 'park_type', 'acres', 'has_rainbow_sign', 'sign_count', 'is_visited', 'visit_count']
    list_filter = ['has_rainbow_sign', 'park_type', 'neighborhood']
    search_fields = ['name', 'address', 'neighborhood', 'pma_id']
    inlines = [SignInline, VisitInline]

    def sign_count(self, obj):
        return obj.signs.count()
    sign_count.short_description = 'Signs'
    
    def is_visited(self, obj):
        return obj.is_visited
    is_visited.boolean = True
    is_visited.short_description = 'Visited'


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['park', 'sign', 'visit_date', 'rating', 'photo_count']
    list_filter = ['visit_date', 'rating']
    search_fields = ['park__name', 'notes']
    raw_id_fields = ['sign']
    autocomplete_fields = ['park']
    date_hierarchy = 'visit_date'
    inlines = [VisitPhotoInline]
    
    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Photos'


@admin.register(VisitPhoto)
class VisitPhotoAdmin(admin.ModelAdmin):
    list_display = ['visit', 'caption', 'created_at']
    list_filter = ['created_at']
    search_fields = ['visit__park__name', 'caption']
