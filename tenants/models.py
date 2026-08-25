from django.contrib.auth.hashers import (
    check_password,
    make_password,
    UNUSABLE_PASSWORD_PREFIX,
)
from django.db import models
from django.utils.crypto import salted_hmac


class PlatformAdmin(models.Model):

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="اسم المستخدم",
    )

    password = models.CharField(
        max_length=255,
        verbose_name="كلمة المرور",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط",
    )

    is_staff = models.BooleanField(
        default=True,
        verbose_name="فريق العمل",
    )

    is_superuser = models.BooleanField(
        default=True,
        verbose_name="مدير النظام الأساسي",
    )

    full_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="الاسم الكامل",
    )

    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخر تسجيل دخول",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "مدير المنصة"
        verbose_name_plural = "مدراء المنصة"

    def __str__(self):
        return self.full_name or self.username

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def set_unusable_password(self):
        self.password = make_password(None)

    def has_usable_password(self):
        return (
            self.password is not None
            and not self.password.startswith(UNUSABLE_PASSWORD_PREFIX)
        )

    def get_session_auth_hash(self):
        key_salt = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
        return salted_hmac(
            key_salt,
            self.password,
            algorithm="sha256",
        ).hexdigest()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def has_perm(self, perm, obj=None):
        return self.is_superuser and self.is_active

    def has_module_perms(self, app_label):
        return self.is_superuser and self.is_active

    def get_user_permissions(self, obj=None):
        return set()

    def get_group_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return set()


class Tenant(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "نشط"
        SUSPENDED = "suspended", "موقوف"

    clinic_name = models.CharField(
        max_length=150,
        verbose_name="اسم العيادة",
    )

    slug = models.SlugField(
        unique=True,
        max_length=100,
        verbose_name="المعرف",
    )

    database_name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="اسم قاعدة البيانات",
    )

    database_host = models.CharField(
        max_length=255,
        default="127.0.0.1",
        verbose_name="Database Host",
    )

    database_port = models.PositiveIntegerField(
        default=5432,
        verbose_name="Database Port",
    )

    database_user = models.CharField(
        max_length=150,
        verbose_name="Database User",
    )

    database_password = models.CharField(
        max_length=255,
        verbose_name="Database Password",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.clinic_name