from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


from apps.accounts.fields import AutoCreatedField, AutoLastModifiedField


class Site(models.Model):
    title = models.CharField(
        max_length=200, help_text="Name of Mercury Site", blank=False, null=False
    )
    slug = models.CharField(
        max_length=200,
        help_text="Subdomain address",
        blank=False,
        null=False,
        unique=True,
    )
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    SHARE_CHOICES = (
        (PUBLIC, "Anyone can access notebooks and execute"),
        (PRIVATE, "Only selected users have access to notebooks"),
    )
    share = models.CharField(
        default=PUBLIC, max_length=32, choices=SHARE_CHOICES, blank=True, null=True
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
    info = models.TextField(blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class UsersGroup(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Group of users in Mercury",
        blank=False,
        null=False,
    )
    # view, edit, admin
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
    hosted_on = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(UsersGroup, on_delete=models.CASCADE)
    created_at = AutoCreatedField()
    updated_at = AutoLastModifiedField()
    hosted_on = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
    )
