from django.contrib import admin
from .models import Assessment, Question, Choice, UserAttempt, UserResponse

# Inline for Choices under Questions
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3  # Show 3 empty choice fields by default, with "Add another" button
    fields = ('text', 'is_correct')

# Inline for Questions under Assessments
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True
    fields = ('text', 'question_type', 'marks', 'order')

# Inline for UserAttempts under Assessments
class UserAttemptInline(admin.TabularInline):
    model = UserAttempt
    extra = 1  # Show 1 empty attempt field by default
    fields = ('user', 'assessment', 'start_time', 'end_time', 'score', 'passed')
    readonly_fields = ('start_time', 'end_time', 'score', 'passed')  # Calculated fields
    raw_id_fields = ('user',)

# Inline for UserResponses under Questions
class UserResponseInline(admin.TabularInline):
    model = UserResponse
    extra = 1  # Show 1 empty response field by default
    fields = ('attempt', 'question', 'chosen_choice', 'text_response')
    raw_id_fields = ('attempt', 'question', 'chosen_choice')

# Inline for UserResponses under UserAttempts (optional)
class UserResponseUnderAttemptInline(admin.TabularInline):
    model = UserResponse
    extra = 1
    fields = ('question', 'chosen_choice', 'text_response')
    raw_id_fields = ('question', 'chosen_choice')

# Admin for Assessments
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'assessment_type', 'course', 'passing_score', 'created_at')
    list_filter = ('assessment_type', 'course')
    search_fields = ('title',)
    inlines = [QuestionInline, UserAttemptInline]

# Admin for Questions
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'assessment', 'question_type', 'marks', 'order')
    list_filter = ('assessment', 'question_type')
    search_fields = ('text',)
    inlines = [ChoiceInline, UserResponseInline]

# Admin for UserAttempt
class UserAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'start_time', 'score', 'passed')
    list_filter = ('passed', 'assessment')
    readonly_fields = ('start_time', 'end_time', 'score', 'passed')
    inlines = [UserResponseUnderAttemptInline]  # Optional: responses under attempts

# Register models
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(UserAttempt, UserAttemptAdmin)
admin.site.register(UserResponse)