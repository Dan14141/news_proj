from rest_framework import serializers
from .models import Comment
from apps.posts.models import Post

# Базовый сериализатор для комментариев
class CommentSerializer(serializers.ModelSerializer):

    author_info = serializers.SerializerMethodField()
    replies_count = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_info',
            'created_at', 'is_reply', 'replies_count',
            'is_active', 'updated_at'
        ]

    def get_author_info(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'full_name': obj.author.full_name,
            'avatar': obj.author.avatar.url if obj.author.avatar else None,
        }

# Сериализатор для создания комментариев
class CommentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['post','parent', 'content']

    # Проверка на существование публикации
    def validate_post(self, value):
        if not Post.objects.filter(id=value.id, status='published').exists():
            raise serializers.ValidationError('Post does not exist')
        return value

    # Проверка на пренадлежность родительского коммента к данному посту
    def validate_parent(self, value):
        if value:
            post_data = self.initial_data.get('post')
            if post_data:
                if value.post.id != int(post_data):
                    raise serializers.ValidationError(
                        'Parent comment must belong to the same post'
                    )
        return value

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

# Сериализатор для обновления комментариев
class CommentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['content']

# Сериализатор для просмотра конкретного комментария
class CommentDetailSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta(CommentCreateSerializer.Meta):
        fields = CommentCreateSerializer.Meta.fields + ['replies']

    # Показываем ответы, только если комментарий основной
    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.filter(is_active=True).order_by('-created_at')
            return CommentSerializer(replies, many=True, context=self.context).data
        return []