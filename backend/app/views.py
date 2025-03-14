from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Category, User, Project, Proposal, ProjectFile

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

    class Meta:
        model = Project
        fields = ['id', 'user', 'category', 'service_location', 'location', 'address', 'budget', 'description', 'title', 'status', 'expiry_date', 'created_at', 'user_telegram_id']
        read_only_fields = ['user']

    def create(self, validated_data):
        user_telegram_id = validated_data.pop('user_telegram_id')
        user, created = User.objects.get_or_create(
            telegram_id=user_telegram_id,
            defaults={'phone': f"tg_{user_telegram_id}", 'name': 'کاربر'}
        )
        project = Project.objects.create(user=user, **validated_data)
        return project

class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = '__all__'

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

async def submit_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = context.user_data.get('location')
    location_data = None
    if location:
        location_data = [location['longitude'], location['latitude']]  # فقط مختصات به صورت لیست
    
    data = {
        'title': generate_title(context),
        'description': context.user_data.get('description', ''),
        'category': context.user_data.get('category_id', ''),
        'service_location': context.user_data.get('service_location', ''),
        'location': location_data,  # لیست مختصات
        'budget': context.user_data.get('budget', None),
        'deadline_date': convert_deadline_to_date(context.user_data.get('deadline', None)),
        'start_date': context.user_data.get('need_date', None),
        'files': await upload_attachments(context.user_data.get('files', []), context),
        'user_telegram_id': str(update.effective_user.id)
    }
    logger.info(f"Sending project data to API: {data}")
    try:
        response = requests.post(f"{BASE_URL}projects/", json=data)
        # بقیه کد بدون تغییر
    except Exception as e:
        logger.error(f"Error submitting project: {e}")
        await update.message.reply_text("❌ خطا در ثبت درخواست.")
    context.user_data.clear()
    await start(update, context)