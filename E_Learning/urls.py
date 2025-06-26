
from django.contrib import admin
from django.urls import path, include
from courses.router import urls
from django.conf import settings
from django.conf.urls.static import static
from courses.views import CourseViewSet
from assessments.urls import urls as assessment_urls
from payments import views as payment_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('djoser.urls')),
    path('api/v1/', include('djoser.urls.jwt')),
    path('api/v1/resend_activation/', include('djoser.urls')),
    path('api/v1/', include('users.urls')),
    path('api/v1/', include(urls)),
    path('api/v1/', include(assessment_urls)),

    # Payment endpoints
    path('chapa-ipn/', payment_views.chapa_ipn, name='chapa-ipn'),
    path('api/v1/payments/', include('payments.urls')),
    
    # Direct PayPal URLs (no include)
    path('paypal-ipn/', payment_views.paypal_ipn, name='paypal-ipn'),
    path('payment-complete/', payment_views.payment_complete, name='payment-complete'),
    path('payment-cancelled/', payment_views.payment_cancelled, name='payment-cancelled'),

    path('api/v1/courses/<int:pk>/rate/', CourseViewSet.as_view({'post': 'rate_course'}), name='course-rate'),
    path('api/v1/courses/<int:pk>/has_rated/', CourseViewSet.as_view({'get': 'has_rated'}), name='course-has-rated'),
    path('api/v1/courses/<int:pk>/toggle_lesson_progress/', CourseViewSet.as_view({'post': 'toggle_lesson_progress'})),
    path('api/v1/courses/<int:pk>/progress/', CourseViewSet.as_view({'get': 'progress'}), name='course-progress'),
    path('api/v1/courses/<int:pk>/enroll/', CourseViewSet.as_view({'post': 'enroll'}), name='course-enroll'),
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
