import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models.signals import post_save
from django.dispatch import receiver


class Contact(models.Model):
    fullname = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    phone = models.CharField(max_length=20, null=True, blank=True)
    message = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fullname} - {self.email}"

    class Meta:
        ordering = ['-date_created']


class Category(models.Model):
    sub_category = models.ForeignKey('self', on_delete=models.CASCADE, related_name='sub_categories', null=True, blank=True)
    is_sub = models.BooleanField(default=False)
    name = models.CharField(max_length=200, null=True)
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class UserProfile(models.Model):
    """Thông tin mở rộng của người dùng (OneToOne với User)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Số điện thoại')
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='Địa chỉ')
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name='Thành phố')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Ảnh đại diện')
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile của {self.user.username}"

    @property
    def AvatarURL(self):
        try:
            url = self.avatar.url
        except Exception:
            url = ''
        return url


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Tự động tạo UserProfile khi tạo User mới."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Tự động lưu UserProfile khi lưu User."""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name='products')
    name = models.CharField(max_length=200, null=True)
    price = models.FloatField()
    digital = models.BooleanField(default=False, null=True, blank=False)
    image = models.ImageField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    # CT1: Quản lý tồn kho
    stock = models.IntegerField(default=100, verbose_name='Số lượng tồn kho')

    def __str__(self):
        return self.name

    @property
    def ImageURL(self):
        try:
            url = self.image.url
        except Exception:
            url = ''
        return url

    @property
    def in_stock(self):
        """Kiểm tra còn hàng hay không."""
        return self.stock > 0


class Order(models.Model):
    # CT2: Trạng thái đơn hàng
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPING = 'shipping'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Chờ xử lý'),
        (STATUS_PROCESSING, 'Đang xử lý'),
        (STATUS_SHIPPING, 'Đang giao hàng'),
        (STATUS_DELIVERED, 'Đã giao hàng'),
        (STATUS_CANCELLED, 'Đã hủy'),
    ]

    customer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    date_order = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, null=True, blank=False)
    # CT6: UUID đảm bảo uniqueness tuyệt đối
    transaction_id = models.CharField(max_length=200, null=True, blank=True, unique=True)
    # CT2: Trạng thái chi tiết
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Trạng thái')

    def __str__(self):
        return str(self.id)

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems if item.product is not None])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems if item.product is not None])
        return total

    @property
    def status_display_class(self):
        """Trả về Bootstrap badge class tương ứng với trạng thái."""
        class_map = {
            self.STATUS_PENDING: 'warning',
            self.STATUS_PROCESSING: 'primary',
            self.STATUS_SHIPPING: 'info',
            self.STATUS_DELIVERED: 'success',
            self.STATUS_CANCELLED: 'danger',
        }
        return class_map.get(self.status, 'secondary')


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        if self.product is None:
            return 0
        return self.product.price * self.quantity


class ShippingAddress(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    mobile = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address