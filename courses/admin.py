from django.contrib import admin
from .models import Category, Course, Module, Lesson, Enrollment, ReviewRating, UserProgress, Contact

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ('order',)

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title',)
    ordering = ('course', 'order')
    inlines = [LessonInline]

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    raw_id_fields = ('user',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')
    inlines = [EnrollmentInline]
    
    # Remove ModuleInline from inlines

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'youtube_url', 'order')
    fields = ('module', 'title', 'content', 'youtube_url', 'resources', 'order')
    list_filter = ('module__course', 'module')
    search_fields = ('title', 'content')
    ordering = ('module__course', 'module', 'order')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Module, ModuleAdmin)  # Register Module separately
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Enrollment)
admin.site.register(UserProgress)
admin.site.register(ReviewRating)
admin.site.register(Contact)