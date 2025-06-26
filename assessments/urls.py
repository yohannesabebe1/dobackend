from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet, QuestionViewSet, ChoiceViewSet, UserAttemptViewSet

router = DefaultRouter()
router.register('assessments', AssessmentViewSet, basename='assessment')
router.register('questions', QuestionViewSet, basename='questions')
router.register('choices', ChoiceViewSet, basename='choices')
router.register('user-attempts', UserAttemptViewSet, basename='user-attempts')
# router.register('user-responses', UserResponseViewSet)
urls = router.urls