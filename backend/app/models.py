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
    telegram_phone = models.CharField(max_length=50, null=True, blank=True)  # شماره تلگرام اصلی
    name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=[("client", "کارفرما"), ("contractor", "مجری")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} ({self.role})"

class Project(models.Model):
    id = models.BigAutoField(primary_key=True)  # شماره منحصر به فرد پروژه
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_telegram_id = models.CharField(max_length=50, default="unknown")
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    service_location = models.CharField(max_length=20, choices=[("client_site", "محل کارفرما"), ("contractor_site", "محل مجری"), ("remote", "غیرحضوری")])
    location = gis_models.PointField(null=True, blank=True, srid=4326)  # اضافه کردن srid=4326
    address = models.CharField(max_length=200, blank=True)
    budget = models.BigIntegerField(null=True, blank=True)  # تغییر به BigIntegerField
    description = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=20, default="open", choices=[("open", "باز"), ("in_progress", "در حال اجرا"), ("completed", "تکمیل‌شده")])
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline_date = models.DateField(null=True, blank=True)
    start_date = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.title

class ProjectFile(models.Model):
    project = models.ForeignKey(Project, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')

class Proposal(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    contractor = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.IntegerField()
    time = models.CharField(max_length=50)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"پیشنهاد {self.contractor.phone} برای {self.project.title}"