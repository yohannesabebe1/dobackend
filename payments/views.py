# payments/views.py
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.urls import reverse
from courses.models import Course, Enrollment
from django.shortcuts import redirect
from .models import Payment
from .serializers import PaymentSerializer
import uuid
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import MultipleObjectsReturned
import logging

logger = logging.getLogger(__name__)
import requests

from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_paypal_payment(request):
    try:
        user = request.user
        course_id = request.data.get('course_id')
        
        if not course_id:
            return Response({'error': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.get(id=course_id)
        
        # Check existing enrollment
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({'error': 'Already enrolled'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle free courses
        if course.price == 0:
            Enrollment.objects.create(user=user, course=course)
            return Response({'status': 'enrolled'})

        # Create payment record
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=course.price,
            status=False
        )

        # Verify PayPal settings
        if not all([settings.PAYPAL_EMAIL, settings.PAYPAL_URL]):
            raise Exception('PayPal configuration missing')

        # Build URLs
        return_url = request.build_absolute_uri(
            reverse('payment-complete') + f'?payment_id={payment.id}'
        )
        cancel_url = request.build_absolute_uri(reverse('payment-cancelled'))
        notify_url = request.build_absolute_uri(reverse('paypal-ipn'))

        paypal_data = {
            'cmd': '_xclick',
            'business': settings.PAYPAL_EMAIL,
            'amount': str(course.price),
            'item_name': course.title,
            'invoice': str(payment.id),
            'currency_code': 'USD',
            'return': return_url,
            'cancel_return': cancel_url,
            'notify_url': notify_url,
            'no_shipping': '1',
            'custom': str(user.id),
        }

        return Response({
            'payment_url': settings.PAYPAL_URL,
            'payment_data': paypal_data,
            'payment_id': payment.id
        })

    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Payment Error: {str(e)}")  # Check console for this error
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def paypal_ipn(request):
    # Verify IPN with PayPal
    data = request.POST.copy()
    data['cmd'] = '_notify-validate'
    response = requests.post(settings.PAYPAL_VERIFY_URL, data=data)
    
    if response.text == 'VERIFIED':
        payment_id = data.get('invoice')
        txn_id = data.get('txn_id')
        payment_status = data.get('payment_status')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            if payment_status == 'Completed' and not payment.status:
                payment.payment_id = txn_id
                payment.status = True
                payment.save()
                
                # Create enrollment
                Enrollment.objects.get_or_create(
                    user=payment.user,
                    course=payment.course
                )
                
        except Payment.DoesNotExist:
            pass
            
    return Response(status=200)
def payment_complete(request):
    payment_id = request.GET.get('payment_id')
    # Redirect to Vue frontend with success status
    return redirect(f'{settings.FRONTEND_URL}/payment/success?payment_id={payment_id}')

def payment_cancelled(request):
    # Redirect to Vue frontend with cancelled status
    return redirect(f'{settings.FRONTEND_URL}/payment/cancel')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    try:
        payment = Payment.objects.get(id=pk, user=request.user)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=404)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chapa_payment(request):
    try:
        user = request.user
        course_id = request.data.get('course_id')
        
        
        # Validate email format
        if not user.email or '@' not in user.email:
            return Response({'error': 'Valid user email required'}, status=400)
        
        if not course_id:
            return Response({'error': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.get(id=course_id)
        
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({'error': 'Already enrolled'}, status=status.HTTP_400_BAD_REQUEST)

        if course.price == 0:
            Enrollment.objects.create(user=user, course=course)
            return Response({'status': 'enrolled'})

        # Create payment record
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=course.price,
            gateway='chapa',
            chapa_tx_ref=f'chapa-tx-{uuid.uuid4().hex[:10]}'
        )

        # Build Chapa payment data
        chapa_data = {
            'public_key': settings.CHAPA_PUBLIC_KEY,
            'tx_ref': payment.chapa_tx_ref,
            'amount': str(course.price),
            'currency': 'ETB',
            'email': user.email,
            'first_name': user.first_name or 'User',
            'last_name': user.last_name or str(user.id),
            'title': f"Course: {course.title}",
            'description': f"Payment for {course.title}",
            'callback_url': request.build_absolute_uri(reverse('chapa-ipn')),
            'return_url': f"{settings.FRONTEND_URL}/payment/success?payment_id={payment.id}",
        }
    
        return Response({
            'payment_url': 'https://api.chapa.co/v1/hosted/pay',
            'payment_data': chapa_data,
            'payment_id': payment.id
        })

    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Chapa Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add Chapa IPN handler
@csrf_exempt
@api_view(['GET', 'POST'])  # Allow both GET and POST
def chapa_ipn(request):
    # Handle GET parameters for Chapa callback
    data = request.query_params if request.method == 'GET' else request.data
    
    try:
        tx_ref = data.get('tx_ref')
        if not tx_ref:
            return Response({'error': 'Missing transaction reference'}, status=400)

        payment = get_object_or_404(
            Payment,
            chapa_tx_ref=tx_ref,
            status=False
        )
        
        if data.get('status') == 'success':
            payment.payment_id = data.get('transaction_id') or data.get('id')
            payment.status = True
            payment.save()
            
            Enrollment.objects.get_or_create(
                user=payment.user,
                course=payment.course
            )
            
            return redirect(f'{settings.FRONTEND_URL}/payment/success?payment_id={payment.id}')
            
        return Response({'status': 'pending'})

    except MultipleObjectsReturned:
        logger.error(f'Multiple payments found for tx_ref: {tx_ref}')
        return Response({'error': 'Duplicate transaction'}, status=400)
    except Exception as e:
        logger.error(f'Chapa IPN error: {str(e)}')
        return Response({'error': 'Payment processing failed'}, status=400)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_chapa_payment(request):
    try:
        tx_ref = request.data.get('tx_ref')
        if not tx_ref:
            return Response({'error': 'Transaction reference required'}, status=400)

        payment = Payment.objects.get(
            chapa_tx_ref=tx_ref,
            user=request.user
        )

        if payment.status:
            return Response({
                'status': 'success',
                'payment': PaymentSerializer(payment).data
            })

        # Verify with Chapa API
        headers = {'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'}
        response = requests.get(
            f'https://api.chapa.co/v1/transaction/verify/{tx_ref}/',
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        payment_data = response.json().get('data', {})
        if payment_data.get('status') == 'success':
            # Ensure we have a valid payment ID
            payment.payment_id = payment_data.get('id') or f'chapa-{tx_ref}'
            payment.status = True
            payment.save()
            Enrollment.objects.get_or_create(user=payment.user, course=payment.course)

        return Response({
            'status': 'success' if payment.status else 'pending',
            'payment': PaymentSerializer(payment).data
        })

    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=404)
    except requests.exceptions.RequestException as e:
        logger.error(f'Chapa API error: {str(e)}')
        return Response({'error': 'Payment verification service unavailable'}, status=503)
    except Exception as e:
        logger.error(f'Verification error: {str(e)}')
        return Response({'error': 'Payment verification failed'}, status=500)