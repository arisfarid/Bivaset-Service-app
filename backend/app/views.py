from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from .models import Category, User, Project, Proposal, ProjectFile
import logging

logger = logging.getLogger(__name__)  # برای لاگ‌گیری

# Serializers
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'children']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone', 'telegram_id', 'name', 'role', 'created_at']

class ProjectSerializer(serializers.ModelSerializer):
    user_telegram_id = serializers.CharField(write_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    location = serializers.ListField(
        child=serializers.FloatField(), write_only=True, required=False
    )  # برای دریافت [longitude, latitude]

    class Meta:
        model = Project
        fields = [
            'id', 'user', 'user_telegram_id', 'title', 'category', 'service_location',
            'location', 'address', 'budget', 'description', 'status', 'expiry_date',
            'created_at', 'deadline_date', 'start_date'
        ]
        read_only_fields = ['user']

    def to_internal_value(self, data):
        # تبدیل [longitude, latitude] به Point
        if 'location' in data and data['location']:
            try:
                longitude, latitude = data['location']
                data['location'] = Point(longitude, latitude, srid=4326)
            except (ValueError, TypeError, IndexError) as e:
                logger.error(f"Invalid location format: {data['location']}, error: {e}")
                raise serializers.ValidationError("فرمت لوکیشن نامعتبر است. باید [longitude, latitude] باشد.")
        return super().to_internal_value(data)

    def create(self, validated_data):
        user_telegram_id = validated_data.pop('user_telegram_id')
        user, created = User.objects.get_or_create(
            telegram_id=user_telegram_id,
            defaults={'phone': f"tg_{user_telegram_id}", 'name': 'کاربر', 'role': 'client'}
        )
        project = Project.objects.create(user=user, **validated_data)
        return project

class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = '__all__'

# Views
@api_view(['POST'])
def upload_file(request):
    file = request.FILES.get('file')
    if file:
        project_file = ProjectFile(file=file)
        project_file.save()
        return Response({'file_url': project_file.file.url}, status=201)
    return Response({'error': 'No file provided'}, status=400)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        files = request.FILES.getlist('files') or data.get('files', [])
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        for file in files:
            if isinstance(file, str):  # اگر URL هست
                ProjectFile.objects.create(project=project, file=file)
            else:  # اگر فایل آپلود شده هست
                ProjectFile.objects.create(project=project, file=file)
        return Response(serializer.data, status=201)

class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer