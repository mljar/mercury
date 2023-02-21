from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


from apps.accounts.fields import AutoCreatedField, AutoLastModifiedField



class MercurySite(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Name of Mercury Site",
        blank=False,
        null=False,
        unique=True
    )
    share = models.CharField(
        max_length=200,
        help_text="Share as public or only with auth users (private)",
        blank=False,
        null=False,
        default="public"
    )
    created_at = AutoCreatedField()
    updated_at = AutoLastModifiedField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # custom fields for user
    plan = models.CharField(max_length=200, default="free", blank=True)
    info = models.TextField(blank=True)
    subscription_id = models.CharField(max_length=200, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class MercuryGroup(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Group of users in Mercury",
        blank=False,
        null=False,
    )
    rights = models.CharField(
        max_length=200,
        help_text="Rights for group of users",
        blank=False,
        null=False,
    )
    created_at = AutoCreatedField()
    updated_at = AutoLastModifiedField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    site = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(MercuryGroup, on_delete=models.CASCADE)
    created_at = AutoCreatedField()
    updated_at = AutoLastModifiedField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
