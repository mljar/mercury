from enum import Enum

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.fields import AutoCreatedField, AutoLastModifiedField


class SiteState(str, Enum):
    Created = "Created"
    Initializing = "Initializing"
    Ready = "Ready"
    Error = "Error"


class Site(models.Model):
    title = models.CharField(
        max_length=256, help_text="Name of Mercury Site", blank=False, null=False
    )
    slug = models.CharField(
        max_length=256,
        help_text="Subdomain",
        blank=False,
        null=False,
        unique=True,
    )
    domain = models.CharField(
        default="runmercury.com",
        max_length=256,
        help_text="Domain address",
        blank=True,
        null=True,
    )
    custom_domain = models.CharField(
        max_length=256,
        help_text="Custom domain address",
        blank=True,
        null=True,
        unique=True,
    )

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    SHARE_CHOICES = (
        (PUBLIC, "Anyone can access notebooks and execute"),
        (PRIVATE, "Only selected users have access to notebooks"),
    )
    share = models.CharField(
        default=PUBLIC, max_length=32, choices=SHARE_CHOICES, blank=False, null=False
    )

    # Created
    # Initializing
    # Ready
    # Error
    status = models.CharField(default="Created", max_length=32, blank=False, null=False)
    info = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True, blank=False, null=False)
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


@receiver(post_save, sender=User)
def check_invitations(sender, instance, **kwargs):
    
    print("check invitations")
    print(instance.username, instance.email)

    invitations = Invitation.objects.filter(invited=instance.email)
    for invitation in invitations:
        previous_memberships = Membership.objects.filter(user=instance, host=invitation.hosted_on)
        if not previous_memberships:
            Membership.objects.create(
                user=instance,
                host=invitation.hosted_on,
                rights=invitation.rights,
                created_by=invitation.created_by
            )
            invitation.delete()


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    host = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="hosts")
    # view, edit, admin
    VIEW = "VIEW"
    EDIT = "EDIT"
    RIGHTS_CHOICES = (
        (VIEW, "View and execute notebooks"),
        (EDIT, "Edit and view site, files and execute notebooks"),
    )
    rights = models.CharField(
        default=VIEW,
        choices=RIGHTS_CHOICES,
        max_length=32,
        help_text="Rights for user",
        blank=False,
        null=False,
    )
    created_at = AutoCreatedField()
    updated_at = AutoLastModifiedField()
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_by"
    )


class Invitation(models.Model):
    invited = models.CharField(max_length=256, blank=False, null=False)
    created_at = AutoCreatedField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    hosted_on = models.ForeignKey(
        Site, on_delete=models.CASCADE
    )
    rights = models.CharField(
        default=Membership.VIEW,
        choices=Membership.RIGHTS_CHOICES,
        max_length=32,
        help_text="Rights for user",
        blank=False,
        null=False,
    )


class Secret(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    token = models.TextField(blank=False, null=False)
    created_at = AutoCreatedField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    hosted_on = models.ForeignKey(Site, on_delete=models.CASCADE)

