from rest_framework import serializers
from .models import Assessment, Question, Choice, UserAttempt, UserResponse

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, required=False)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'marks', 'order', 'choices']

class AssessmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Assessment
        fields = '__all__'
        depth = 2

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if 'expand' in self.context.get('request').query_params:
            expand_fields = self.context['request'].query_params['expand'].split('.')
            for field in expand_fields:
                if field in ['questions', 'choices']:
                    response[field] = getattr(instance, field).all().values()
        return response
class UserResponseSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    chosen_choice = serializers.PrimaryKeyRelatedField(queryset=Choice.objects.all())

    class Meta:
        model = UserResponse
        fields = ['question', 'chosen_choice', 'text_response']

# assessments/serializers.py
# assessments/serializers.py
class UserAttemptSerializer(serializers.ModelSerializer):
    responses = UserResponseSerializer(many=True)
    
    class Meta:
        model = UserAttempt
        fields = ['id', 'assessment', 'responses', 'score', 'passed']
        read_only_fields = ['score', 'passed']

    def create(self, validated_data):
        responses_data = validated_data.pop('responses')
        attempt = UserAttempt.objects.create(**validated_data)
        
        for response_data in responses_data:
            UserResponse.objects.create(attempt=attempt, **response_data)
        
        return attempt