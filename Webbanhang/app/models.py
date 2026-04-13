from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    
