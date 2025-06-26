from django.db import models

# Create your models here.
from django.db import models
from courses.models import Course, Module, Lesson
from users.models import UserAccount

class Assessment(models.Model):
    ASSESSMENT_TYPES = (
        ('quiz', 'Lesson Quiz'),
        ('mid-exam', 'Module Exam'),
        ('final-exam', 'Course Final Exam'),
    )
    title = models.CharField(max_length=255)
    assessment_type = models.CharField(max_length=10, choices=ASSESSMENT_TYPES)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='quizzes')
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='quiz')
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    passing_score = models.PositiveIntegerField(default=70)
    max_attempts = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice Question'),
        ('TF', 'True/False'),
        ('SA', 'Short Answer'),
        ('ES', 'Essay'),
    )
    assessment = models.ForeignKey(Assessment, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.assessment.title} - Question {self.order}"

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class UserAttempt(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)

    def calculate_score(self):
    # Calculate achieved score
        total_score = 0
        for response in self.responses.all():
            if response.chosen_choice and response.chosen_choice.is_correct:
                total_score += response.question.marks
        
        # Calculate maximum possible score
        total_possible = sum(question.marks for question in self.assessment.questions.all())
        
        # Calculate percentage score
        score_percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
        
        # Update attempt results
        self.score = total_score
        self.passed = score_percentage >= self.assessment.passing_score
        self.save()

    class Meta:
        ordering = ['-start_time']

class UserResponse(models.Model):
    attempt = models.ForeignKey(UserAttempt, related_name='responses', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    chosen_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_response = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ('attempt', 'question')