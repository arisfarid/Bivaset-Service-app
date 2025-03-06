from django.db import models
from django.contrib.gis.db import models as gis_models  # برای PointField

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

class User(models.Model):
    phone = models.CharField(max_length=50, unique=True)
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=[("client", "کارفرما"), ("contractor", "مجری")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} ({self.role})"

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    service_location = models.CharField(max_length=20, choices=[("client_site", "محل کارفرما"), ("contractor_site", "محل مجری"), ("remote", "غیرحضوری")])
    location = gis_models.PointField(null=True, blank=True)  # اصلاح‌شده
    address = models.CharField(max_length=200, blank=True)
    budget = models.IntegerField(null=True, blank=True)
    description = models.TextField(max_length=500, blank=True)
    title = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="open", choices=[("open", "باز"), ("in_progress", "در حال اجرا"), ("completed", "تکمیل‌شده")])
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Proposal(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    contractor = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.IntegerField()
    time = models.CharField(max_length=50)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"پیشنهاد {self.contractor.phone} برای {self.project.title}"