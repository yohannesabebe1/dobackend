from django.db import models
from courses.models import Course
from users.models import UserAccount
class Payment(models.Model):
    order_id = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=50, null=True, blank=True, default='pending')
    user = models.ForeignKey('users.UserAccount', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00  # Add proper default value
    )
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)
    gateway = models.CharField(max_length=20, default='paypal')  # Add gateway field
    chapa_tx_ref = models.CharField(max_length=100, null=True, blank=True, unique=True)

    def __str__(self):
        return f"Payment {self.order_id}"
