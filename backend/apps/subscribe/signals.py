from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Subscription, PinnedPost, SubscriptionHistory

# Обработчик сохранения подписки
@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    if created:
        # Создаем запись в истории при создании подписки
        SubscriptionHistory.objects.create(
            subscription=instance,
            action='created',
            description=f'Subscription created for plan {instance.plan.name}'
        )
    else:
        # Проверяем, изменился ли статус
        if hasattr(instance, '_previous_status'):
            if instance._previous_status != instance.status:
                SubscriptionHistory.objects.create(
                    subscription=instance,
                    action=instance.status,
                    description=f'Subscription status changed from {instance._previous_status} to {instance.status}'
                )

# Обработчик удаления подписки
@receiver(pre_delete, sender=Subscription)
def subscription_pre_delete(sender, instance, **kwargs):
    # Удаляем закрепленный пост при удалении подписки
    try:
        instance.user.pinned_post.delete()
    except PinnedPost.DoesNotExist:
        pass

# Обработчик сохранения закрепленного поста
@receiver(post_save, sender=PinnedPost)
def pinned_post_post_save(sender, instance, created, **kwargs):
    if created:
        # Проверяем, что у пользователя есть активная подписка
        if not hasattr(instance.user, 'subscription') or not instance.user.subscription.is_active:
            instance.delete()
            return

        # Записываем в историю попдиски
        SubscriptionHistory.objects.create(
            subscription=instance.user.subscription,
            action='post_pinned',
            description=f'Post "{instance.post.title}" pinned',
            metadata={
                'post_id': instance.post.id,
                'post_title': instance.post.title
            }
        )

# Обработчик удаления закрепленного поста
@receiver(pre_delete, sender=PinnedPost)
def pinned_post_pre_delete(sender, instance, **kwargs):
    # Записываем в историю подписки
    if hasattr(instance.user, 'subscription'):
        SubscriptionHistory.objects.create(
            subscription=instance.user.subscription,
            action='post_unpinned',
            description=f'Post "{instance.post.title}" unpinned',
            metadata={
                'post_id': instance.post.id,
                'post_title': instance.post.title
            }
        )