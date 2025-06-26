from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from django.db.models import Count
from django.utils import timezone
from django.db.models import Case, When, F
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import *


from rest_framework.response import Response
from .models import Category, Course, Module, Lesson, Enrollment, UserProgress, ReviewRating, Contact
from .serializers import (
    CategorySerializer,
    CourseSerializer,
    CourseCreateSerializer,
    ModuleSerializer,
    LessonSerializer,
    UserProgressSerializer,
    EnrollmentSerializer,
    ReviewRatingSerializer,
    ContactSerializer

)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CourseCreateSerializer
        return CourseSerializer
    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='toggle_lesson_progress',
            url_name='toggle-lesson-progress')
    def toggle_lesson_progress(self, request, pk=None):
        course = self.get_object()
        lesson_id = request.data.get('lesson_id')

        if not lesson_id:
            return Response(
                {"error": "lesson_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify lesson exists and belongs to course
            lesson = Lesson.objects.get(
                id=lesson_id,
                module__course=course
            )

            # Get or create progress entry
            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                course=course,
                lesson=lesson,
                defaults={
                    'module': lesson.module,
                    'completed': True,
                    'completed_at': timezone.now()
                }
            )

            # Toggle if existing entry
            if not created:
                progress.completed = not progress.completed
                progress.completed_at = timezone.now() if progress.completed else None
                progress.save()

            return Response({
                "id": progress.id,
                "completed": progress.completed,
                "lesson_id": lesson.id,
                "module_id": lesson.module.id
            }, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                {"error": "Lesson not found in this course"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='progress',
            url_name='progress')
    def progress(self, request, pk=None):
        course = self.get_object()
        progress = UserProgress.objects.filter(
            user=request.user,
            course=course
        ).select_related('lesson', 'module')
        serializer = UserProgressSerializer(progress, many=True)
        return Response({
            'course_id': course.id,
            'progress': serializer.data
        })

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='enroll')
    def enroll(self, request, pk=None):
        course = self.get_object()
        Enrollment.objects.get_or_create(user=request.user, course=course)
        return Response({'status': 'enrolled'}, status=status.HTTP_201_CREATED)



    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def has_rated(self, request, pk=None):
        course = self.get_object()
        has_rated = ReviewRating.objects.filter(user=request.user, course=course).exists()
        return Response({'has_rated': has_rated})

# In views.py CourseViewSet - replace duplicate rate_course
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate_course(self, request, pk=None):
        course = self.get_object()
        serializer = ReviewRatingSerializer(
            data=request.data,
            context={
                'request': request,
                'course': course
            }
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Rating error: {str(e)}")
            return Response(
                {"error": "Failed to save rating"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def search(self, request):
        """Search courses by title or description"""
        search_term = request.query_params.get('search', '')
        queryset = self.get_queryset().filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term)
        ).distinct()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# views.py
class UserProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        result = {}
        for progress in serializer.data:
            course_id = str(progress['course'])
            if course_id not in result:
                result[course_id] = []
            result[course_id].append({
                "lesson": {"id": progress['lesson']['id']},
                "completed": progress['completed'],
                "updated_at": progress['completed_at']
            })
        print(f"Returning progress: {result}")  # Debug log
        return Response(result)

    def create(self, request, *args, **kwargs):
        course_id = request.data.get('courseId')
        lesson_id = request.data.get('lessonId')
        completed = request.data.get('completed', True)

        if not course_id or not lesson_id:
            return Response(
                {"error": "courseId and lessonId are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
            lesson = Lesson.objects.get(id=lesson_id, module__course=course)
            progress, created = UserProgress.objects.update_or_create(
                user=request.user,
                course=course,
                lesson=lesson,
                defaults={
                    'module': lesson.module,
                    'completed': completed,
                    'completed_at': timezone.now() if completed else None
                }
            )
            serializer = self.get_serializer(progress)
            print(f"Saved progress: {serializer.data}")  # Debug log
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except (Course.DoesNotExist, Lesson.DoesNotExist):
            return Response(
                {"error": "Course or Lesson not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error saving progress: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['put'])
    def toggle_complete(self, request, pk=None):
        progress = self.get_object()
        progress.completed = not progress.completed
        progress.completed_at = timezone.now() if progress.completed else None
        progress.save()
        return Response(self.get_serializer(progress).data)

class ModuleViewSet(viewsets.ModelViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Module.objects.filter(course_id=self.kwargs['course_pk'])

    def perform_create(self, serializer):
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        serializer.save(course=course)

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Lesson.objects.filter(module_id=self.kwargs['module_pk'])

    def perform_create(self, serializer):
        module = Module.objects.get(pk=self.kwargs['module_pk'])
        serializer.save(module=module)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer  # Create this serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to submit

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
