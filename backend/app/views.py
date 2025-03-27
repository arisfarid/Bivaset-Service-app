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
    files = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'user', 'user_telegram_id', 'title', 'category', 'service_location',
            'location', 'address', 'budget', 'description', 'status', 'expiry_date',
            'created_at', 'deadline_date', 'start_date', 'files'
        ]
        read_only_fields = ['user']

    def to_internal_value(self, data):
        logger.info(f"Raw project data received: {data}")
        if 'location' in data and data['location']:
            try:
                longitude, latitude = data['location']
                data['location'] = Point(longitude, latitude, srid=4326)
                logger.info(f"Converted location to Point: {data['location']}")
            except (ValueError, TypeError, IndexError) as e:
                logger.error(f"Invalid location format: {data['location']}, error: {e}")
                raise serializers.ValidationError("فرمت لوکیشن نامعتبر است. باید [longitude, latitude] باشد.")
        return super().to_internal_value(data)

    def create(self, validated_data):
        logger.info(f"Validated data before creating project: {validated_data}")
        user_telegram_id = validated_data.pop('user_telegram_id')
        user, created = User.objects.get_or_create(
            telegram_id=user_telegram_id,
            defaults={'phone': f"tg_{user_telegram_id}", 'name': 'کاربر', 'role': 'client'}
        )
        validated_data['user'] = user
        # مطمئن شو که location یه Point باشه
        if 'location' in validated_data and validated_data['location'] and not isinstance(validated_data['location'], Point):
            longitude, latitude = validated_data['location']
            validated_data['location'] = Point(longitude, latitude, srid=4326)
        project = Project.objects.create(**validated_data)
        logger.info(f"Project created with ID: {project.id}")
        return project

    def get_files(self, obj):
        return [file.file.name for file in obj.files.all()]

    def validate(self, data):
        """
        اعتبارسنجی اطلاعات پروژه
        """
        if data.get('service_location') in ['client_site', 'contractor_site']:
            if not data.get('location'):
                raise serializers.ValidationError({
                    'location': ['برای خدمات حضوری، ثبت لوکیشن الزامی است.']
                })
        elif data.get('service_location') == 'remote':
            # برای خدمات غیرحضوری، لوکیشن اختیاری است
            data['location'] = None
            
        return data

class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = '__all__'

# Views
@api_view(['POST'])
def upload_file(request):
    file = request.FILES.get('file')
    project_id = request.data.get('project_id')
    logger.info(f"Received upload request. Project ID: {project_id}, File: {file}")
    if file and project_id:
        try:
            project = Project.objects.get(id=project_id)
            project_file = ProjectFile(file=file, project=project)
            project_file.save()
            logger.info(f"File saved successfully: {project_file.file.url}")
            return Response({'file_url': project_file.file.url}, status=201)
        except Project.DoesNotExist:
            logger.error(f"Invalid project_id: {project_id}")
            return Response({'error': 'Invalid project_id'}, status=400)
    logger.error("No file or project_id provided")
    return Response({'error': 'No file or project_id provided'}, status=400)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        فیلتر کردن کاربران بر اساس telegram_id در درخواست GET
        """
        telegram_id = self.request.query_params.get('telegram_id', None)
        if telegram_id:
            return User.objects.filter(telegram_id=telegram_id)
        return super().get_queryset()

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user_telegram_id = self.request.query_params.get('user_telegram_id')
        if user_telegram_id:
            return Project.objects.filter(user__telegram_id=user_telegram_id)
        return super().get_queryset()

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