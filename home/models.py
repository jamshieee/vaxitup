from django.contrib.auth.hashers import make_password, check_password
from django.db import models

class Userreg(models.Model):
    Name = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=255)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.Name

class Healthcenters(models.Model):
    center_name = models.CharField(max_length=100, unique=True, null=False, blank=False)  
    center_id = models.PositiveIntegerField(unique=True)
    phone = models.BigIntegerField(unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    thaluk = models.CharField(max_length=100, null=True, blank=True)  
    district = models.CharField(max_length=100, default="Unknown District")
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)   
    profile_image = models.ImageField(upload_to="center_profiles/", null=True, blank=True)

    def __str__(self):
        return self.center_name


class Vaccines(models.Model):
    center = models.ForeignKey(Healthcenters, on_delete=models.CASCADE, related_name="vaccines", null=True, blank=True)
    vaccine_category = models.CharField(max_length=255, default="General")  # Added category with default value
    vaccine_name = models.CharField(max_length=255)
    vaccine_details = models.TextField()
    doses = models.CharField(max_length=255, default="Single Dose")  # Default to "Single Dose"
    availability = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.vaccine_name} at {self.center.center_name} - {'Available' if self.availability else 'Not Available'}"

class CenterHoliday(models.Model):
    center = models.ForeignKey(Healthcenters, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.center.center_name} - {self.date}"    

class BookingDetails(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(Userreg, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    email = models.EmailField()
    phone = models.BigIntegerField()
    aadhaar = models.CharField(max_length=12, null=False, blank=True)  # ✅ Added Aadhaar field
    center = models.ForeignKey(Healthcenters, on_delete=models.CASCADE)
    vaccine_name = models.CharField(max_length=50)
    dose = models.PositiveIntegerField()
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ Token number for queue management
    token_number = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token_number:
            self.token_number = self.generate_token_number()
        super().save(*args, **kwargs)

    def generate_token_number(self):
        """
        Generate a unique token number for the user based on the number of bookings
        at the same center, date, and time slot.
        """
        existing_bookings = BookingDetails.objects.filter(
            center=self.center,
            date=self.date,
            time=self.time
        ).count()

        return existing_bookings + 1  # Token number starts from 1 and increments

    def __str__(self):
        return f"{self.name} - {self.vaccine_name} (Dose {self.dose}) at {self.center.center_name} ({self.status}) - Token: {self.token_number}"

 
    
class Notification(models.Model):
    health_center = models.ForeignKey(Healthcenters, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Userreg, on_delete=models.CASCADE, null=True, blank=True)  # Make user optional
    message = models.TextField()
    document = models.FileField(upload_to='notifications/', null=True, blank=True)  # Stores PDF certificates
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        recipient = self.user.Name if self.user else "Health Center"
        return f"{self.health_center.center_name} -> {recipient}: {self.message[:30]}"

class Feedback(models.Model):
    user = models.ForeignKey(Userreg, on_delete=models.CASCADE)  # Links feedback to a user
    feedback = models.TextField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # Rating from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of submission

    def __str__(self):
        return f"Feedback by {self.user.Name} - {self.rating} Stars"  