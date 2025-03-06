from rest_framework import serializers, viewsets
from .models import Category, User, Project, Proposal

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

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer