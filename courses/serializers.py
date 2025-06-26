from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import Category, Course, Module, Lesson, UserProgress, Enrollment, ReviewRating, Contact
from django.db.models import Avg

class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class LessonSerializer(ModelSerializer):
    video = serializers.CharField(read_only=True)  # Renamed field
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content', 'youtube_url', 
            'video', 'resources', 'order'  # Updated field name
        ]
        extra_kwargs = {
            'youtube_url': {
                'help_text': 'Paste YouTube watch URL (e.g. https://www.youtube.com/watch?v=VIDEO_ID)'
            }
        }

class ModuleSerializer(ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons']

class CourseSerializer(ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    modules = ModuleSerializer(many=True, read_only=True)
    category = CategorySerializer()
    enrollments_count = serializers.IntegerField(
        source='enrollments.count', 
        read_only=True
    )
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'category', 
            'price', 'thumbnail', 'created_at', 'modules',
            'enrollments_count', 'is_enrolled', 'user_progress', 'average_rating'
        ]

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserProgressSerializer(
                UserProgress.objects.filter(user=request.user, course=obj),
                many=True
            ).data
        return []

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False
    
    def get_average_rating(self, obj):
        return obj.reviewrating_set.aggregate(Avg('rating'))['rating__avg'] or 0

class CourseCreateSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'price', 'thumbnail']


# serializers.py
class UserProgressSerializer(ModelSerializer):
    lesson = serializers.SerializerMethodField()
    module = serializers.StringRelatedField()
    course = serializers.IntegerField(source='course.id', read_only=True)

    class Meta:
        model = UserProgress
        fields = ['id', 'course', 'completed', 'completed_at', 'lesson', 'module']

    def get_lesson(self, obj):
        return {"id": obj.lesson.id}

class EnrollmentSerializer(ModelSerializer):
    class Meta:
        model = Enrollment
        fields = "__all__"

class ReviewRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewRating
        fields = ['id', 'rating', 'created_at', 'user', 'course']
        read_only_fields = ['user', 'course', 'created_at']

    def create(self, validated_data):
        return ReviewRating.objects.update_or_create(
            user=self.context['request'].user,
            course=self.context['course'],
            defaults=validated_data
        )[0]
    

class ContactSerializer(ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['created_at']