from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.

#Change form Register of Django

class Category(models.Model):
    sub_category = models.ForeignKey('self', on_delete = models.CASCADE, related_name = 'sub_categories', null = True, blank = True)
    is_sub = models.BooleanField(default = False)
    name = models.CharField(max_length = 200, null = True)
    slug = models.SlugField(max_length = 200, unique = True)
    def __str__(self):
        return self.name

class CreateUserForm(UserCreationForm):
    phone = forms.CharField(max_length=15)

    class Meta:
        model = User
        fields = ['username','email','first_name','last_name','password1','password2',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        common = {
            "class": "auth-input",
        }

        if "username" in self.fields:
            self.fields["username"].widget.attrs.update({**common, "placeholder": "Tên đăng nhập"})
        if "email" in self.fields:
            self.fields["email"].widget.attrs.update({**common, "placeholder": "Email"})
        if "phone" in self.fields:
            self.fields["phone"].widget.attrs.update({**common, "placeholder": "Số điện thoại"})
        if "first_name" in self.fields:
            self.fields["first_name"].widget.attrs.update({**common, "placeholder": "Họ"})
        if "last_name" in self.fields:
            self.fields["last_name"].widget.attrs.update({**common, "placeholder": "Tên"})
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({**common, "placeholder": "Mật khẩu"})
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({**common, "placeholder": "Nhập lại mật khẩu"})


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name = 'product')
    name = models.CharField(max_length = 200, null = True)
    price = models.IntegerField()
    digital = models.BooleanField(default = False, null = True, blank = False)
    image = models.ImageField(null=True,blank=True)
    detail = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.name
    
    @property
    def ImageUrl(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True)
    date_order = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default = False, null = True, blank = False)
    transaction_id = models.CharField(max_length=200,null=True)

    def __str__(self):
        return str(self.id)
    
    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total
    
    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total() for item in orderitems])
        return total
    
    
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL,blank=True,null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL,blank=True,null=True)
    quantity = models.IntegerField(default=0,null=True,blank=True)
    date_added = models.DateTimeField(auto_now_add = True)

    def get_total(self):
        total = self.product.price * self.quantity
        return total

class ShippingAddress(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL,blank=True,null=True)
    address = models.CharField(max_length=200,null=True)
    city = models.CharField(max_length=200,null=True)
    state = models.CharField(max_length=200,null=True)
    mobile = models.CharField(max_length=200,null=True)
    date_added = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.address

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length = 100, blank = True, null = True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.jpg')

    def __str__(self):
        return self.user.username


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    order_item = models.ForeignKey('OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_HIDDEN = 'hidden'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_HIDDEN, 'Hidden'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_APPROVED, db_index=True)

    def __str__(self):
        who = self.user.username if self.user else (self.name or "Anonymous")
        return f"{who} - {self.product.name} ({self.rating}/5)"

    class Meta:
        constraints = [
            # Mỗi user chỉ 1 review / 1 sản phẩm. (Cho phép bản ghi anonymous cũ user=None tồn tại)
            models.UniqueConstraint(fields=['product', 'user'], name='uniq_review_per_product_user'),
        ]


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ReviewImage(review_id={self.review_id})"


class ReviewHelpfulVote(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['review', 'user'], name='uniq_helpful_vote_per_review_user'),
        ]

    def __str__(self):
        return f"HelpfulVote(review_id={self.review_id}, user_id={self.user_id})"
    
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    
