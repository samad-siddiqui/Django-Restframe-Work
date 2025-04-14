from rest_framework import serializers
from .models import Project, CustomUser, Profile, Task, Document, Comment
from .models import TimelineEvent, Notification
# from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "Password didn't match."
                )
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class ProjectSerializer(serializers.ModelSerializer):
    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id',
            'current_user_role',
            'title',
            'description',
            'start_date',
            'end_date',
        )

    def get_current_user_role(self, obj):
        user = self.context['request'].user
        profile = Profile.objects.get(user=user)
        return profile.role

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError(
                    "Start date cannot be after end date."
                )
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer

    class Meta:
        model = Profile
        fields = (
            'user',
            'role',
            'contact',
        )


class TaskSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all()
                                                 )
    project_detail = ProjectSerializer(source='project', read_only=True)
    assigned_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'project',         # For POST/PUT
            'project_detail',
            'assigned_by',
            'status',
        )


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['author', 'created_at']


class TimelineEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineEvent
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'read', 'created_at']

# class AssignSerializer(serializers.ModelSerializer):
#     assignee_id = serializers.IntegerField()

#     def validate_assignee_id(self, attrs):
#         try:
#             return Profile.objects.get(id=attrs)
#         except Profile.DoesNotExist:
#             raise serializers.ValidationError(
#                 "Assignee does not exist."
#             )

# class ProfileCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = (
#             'role',
#             'contact',
#         )


# class TaskSerializer(serializers.ModelSerializer):
#     # project = ProjectSerializer()
#     class Meta:
#         model = Task
#         fields = (
#                 'title',
#                 'description',
#                 'project',
#                 )


# class CommentsSerializer(serializers.ModelSerializer):

#     project_title = serializers.CharField(source='project.title')
#     project_date = serializers.DateField(source='project.start_date')
#     author_name = serializers.CharField(source='author.email')
#     task = TaskSerializer()

#     class Meta:
#         model = Comment
#         fields = (
#             "text",
#             "author_user",
#             "create_date",
#             "task",
#             "project_title",
#             "project_date",

#             )


# class ProjectInfoSerializer(serializers.Serializer):
#     # get all the projects and count of projects

#     projects = ProjectSerializer(many=True)
#     count = serializers.IntegerField()
