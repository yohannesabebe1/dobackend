from django.shortcuts import render
import json
from rest_framework.decorators import api_view
from django.http import JsonResponse, HttpResponseBadRequest
from .models import UserAccount
# Create your views here.
@api_view(['POST'])
def resetPassword(request):
    data = json.loads(request.body)
    email = data['email']
    newPassword = data['newPassword']
    
    try:    
        user = UserAccount.objects.get(email=email)
        user.set_password(newPassword)
        user.save()
        return JsonResponse({'message': 'Password reset successfully!'}, safe=False)
    
    except UserAccount.DoesNotExist:
        return HttpResponseBadRequest('User not found!')