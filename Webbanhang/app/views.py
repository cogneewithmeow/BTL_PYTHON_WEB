from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from .models import *
import json
import time
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages

# Create your views here.

def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0 , 'get_cart_total': 0}
        cartItems = order['get_cart_items']
    if request.method == 'POST':
        avatar = request.FILES.get('avatar')
        if avatar:
            profile.avatar = avatar
            profile.save()

    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category}
    return render(request, 'app/profile.html', context)

def detail(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0 , 'get_cart_total': 0}
        cartItems = order['get_cart_items']
    id = request.GET.get('id','')
    products = Product.objects.filter(id=id)
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    context = {'products':products ,'items': items, 'order': order, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category}
    return render(request, 'app/detail.html', context)

def category(request):
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    if active_category:
        products = Product.objects.filter(category__slug = active_category)
    context = {'categories': categories, 'products':products, 'active_category':active_category}
    return render(request, 'app/category.html', context)

def search(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        keys = Product.objects.filter(name__contains = searched)
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0 , 'get_cart_total': 0}
        cartItems = order['get_cart_items']
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    products = Product.objects.all()
    return render(request, 'app/search.html', {"searched":searched, "keys":keys, 'products': products, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category})

def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user =form.save()
            phone = form.cleaned_data.get('phone')
            profile = Profile.objects.get(user=user)
            profile.phone = phone
            profile.save()
            return redirect('login')
    context = {'form':form}
    
    return render(request, 'app/register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password1')
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else: messages.info(request, 'user or password is incorrect!')
    context = {}
    return render(request, 'app/login.html', context)

def logoutPage(request):
    logout(request)
    return redirect('login')

def home(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0 , 'get_cart_total': 0}
        cartItems = order['get_cart_items']
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category}
    return render(request, 'app/home.html', context)

def cart(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0 , 'get_cart_total': 0}
        cartItems = order['get_cart_items']
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category}
    return render(request, 'app/cart.html', context)

def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')

    customer = request.user
    order, created = Order.objects.get_or_create(
        customer=customer,
        complete=False
    )

    items = order.orderitem_set.all()
    cartItems = order.get_cart_items

    if request.method == "POST":
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        mobile = request.POST.get("phone")   # ⚠️ bạn đang dùng name="phone"
        pay_method = request.POST.get("pay_method")

        # 🔥 Lưu payment vào order
        transaction_id = str(int(time.time()))
        order.transaction_id = transaction_id
        order.complete = True   # checkout xong
        order.save()

        # 🔥 Lưu địa chỉ
        ShippingAddress.objects.filter(order=order).delete()

        ShippingAddress.objects.create(
            customer=customer,
            order=order,  # ⚠️ bạn đang thiếu dòng này
            address=address,
            city=city,
            state=state,
            mobile=mobile
        )

        return redirect('success')

    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')

    context = {
        'created': created,
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'categories': categories,
        'active_category': active_category
    }

    return render(request, 'app/checkout.html', context)

def payment(request):
    if not request.user.is_authenticated:
        return redirect('login')

    order = Order.objects.get(customer=request.user, complete=False)
    items = order.orderitem_set.all()
    shipping = ShippingAddress.objects.filter(order=order).first()

    context = {
        'order': order,
        'items': items,
        'shipping': shipping
    }

    if request.method == "POST":
        order.complete = True
        order.transaction_id = str(time.time())
        order.save()

        return redirect('success')
    return render(request, 'app/payment.html', context)

def success(request):
    return render(request, 'app/success.html')

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user
    product = Product.objects.get(id = productId)
    order, created = Order.objects.get_or_create(customer = customer, complete = False)
    orderItem, created = OrderItem.objects.get_or_create(order = order, product = product)
    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()
    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('added', safe = False)

def update_profile(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer = customer, complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items':0 , 'get_cart_total': 0}
        cartItems = order['get_cart_items']

    if request.method == "POST":
        user = request.user
        profile = user.profile
        username = request.POST.get("username")
        # user info
        username = request.POST.get("username")
        if username:
            user.username = username

        first_name = request.POST.get("first_name")
        if first_name:
            user.first_name = first_name

        last_name = request.POST.get("last_name")
        if last_name:
            user.last_name = last_name

        email = request.POST.get("email")
        if email:
            user.email = email

        user.save()

        # PROFILE
        phone = request.POST.get("phone")
        if phone:
            profile.phone = phone

        address = request.POST.get("address")
        if address:
            profile.address = address

        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category}
    return render(request, 'app/update_profile.html', context)
