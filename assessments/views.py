from rest_framework import viewsets, permissions, status
from django.db.models import Q

from rest_framework.response import Response
from .models import Assessment, Question, Choice, UserAttempt, UserResponse
from .serializers import (
    AssessmentSerializer,
    QuestionSerializer,
    ChoiceSerializer,
    UserAttemptSerializer
)

# assessments/views.py (修正核心过滤逻辑)
class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Assessment.objects.filter(
            Q(lesson__module__course__students=user) |
            Q(module__course__students=user) |
            Q(course__students=user)
        ).distinct()

        # 明确处理测验类型参数
        assessment_type = self.request.query_params.get('assessment_type')
        lesson_id = self.request.query_params.get('lesson_id')

        if assessment_type == 'quiz' and lesson_id:
            queryset = queryset.filter(
                lesson__id=lesson_id,
                assessment_type='quiz'
            )

        return queryset.select_related('lesson').prefetch_related('questions__choices')
class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        return Question.objects.filter(assessment_id=self.kwargs['assessment_pk'])


class ChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        return Question.objects.filter(assessment_id=self.kwargs['assessment_pk'])

    
# assessments/views.py
class UserAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = UserAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAttempt.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the attempt and calculate score
        attempt = serializer.save(user=request.user)
        attempt.calculate_score()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )