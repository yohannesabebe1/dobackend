from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register('courses', CourseViewSet, basename='courses')  # Changed to plural
router.register('categories', CategoryViewSet, basename='categories')
router.register('modules', ModuleViewSet, basename='modules')
router.register('lessons', LessonViewSet, basename='lessons')
router.register('progress', UserProgressViewSet, basename='progress')
router.register('enrollments', EnrollmentViewSet, basename='enrollments')
router.register('contacts', ContactViewSet, basename='contacts')
urls = router.urls