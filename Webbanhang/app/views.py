from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from .models import *
import json
import time
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import F
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import logging

from .forms import ReviewForm
from .ai.chat_service import chat_reply, ChatProviderError

# Create your views here.
import re

logger = logging.getLogger(__name__)

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
    # Gợi ý sản phẩm: nhẹ, không phá backend/route
    suggested_products = (
        Product.objects.exclude(id=id).order_by('-id')[:8]
        if id else Product.objects.order_by('-id')[:8]
    )
    base_reviews = (
        Review.objects
        .filter(product_id=id, status=Review.STATUS_APPROVED)
        .select_related('user')
        .prefetch_related('images')
    )

    # Filters kiểu Shopee
    f_rating = request.GET.get('rating')  # '5','4',...
    f_has_comment = request.GET.get('has_comment')  # '1'
    f_has_image = request.GET.get('has_image')  # '1'
    sort = request.GET.get('sort', 'newest')  # newest|highest|lowest|helpful

    reviews = base_reviews
    if f_rating and f_rating.isdigit():
        reviews = reviews.filter(rating=int(f_rating))
    if f_has_comment == '1':
        reviews = reviews.exclude(comment__isnull=True).exclude(comment__exact='')
    if f_has_image == '1':
        reviews = reviews.filter(images__isnull=False).distinct()

    if sort == 'highest':
        reviews = reviews.order_by('-rating', '-created_at')
    elif sort == 'lowest':
        reviews = reviews.order_by('rating', '-created_at')
    elif sort == 'helpful':
        reviews = reviews.order_by('-helpful_count', '-created_at')
    else:
        reviews = reviews.order_by('-created_at')

    # Summary stats
    rating_stats = base_reviews.aggregate(avg=Avg('rating'), count=Count('id'))
    star_counts_raw = base_reviews.values('rating').annotate(c=Count('id'))
    star_counts = {i: 0 for i in range(1, 6)}
    for row in star_counts_raw:
        star_counts[int(row['rating'])] = row['c']
    total_reviews = rating_stats.get('count') or 0
    star_percent = {
        i: (star_counts[i] * 100 / total_reviews) if total_reviews else 0
        for i in range(1, 6)
    }

    # Pagination
    paginator = Paginator(reviews, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # User state
    user_review = None
    can_review = False
    if request.user.is_authenticated and id:
        user_review = Review.objects.filter(product_id=id, user=request.user).first()
        can_review = OrderItem.objects.filter(
            order__customer=request.user,
            order__complete=True,
            product_id=id
        ).exists()

    # Forms (để giữ dữ liệu & show lỗi khi POST fail)
    add_form = ReviewForm()
    edit_form = ReviewForm(instance=user_review) if user_review else None

    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    context = {
        'products':products,
        'suggested_products': suggested_products,
        'reviews': page_obj.object_list,
        'page_obj': page_obj,
        'review_count': total_reviews,
        'avg_rating': rating_stats.get('avg') or 0,
        'star_counts': star_counts,
        'star_percent': star_percent,
        'filters': {'rating': f_rating, 'has_comment': f_has_comment, 'has_image': f_has_image, 'sort': sort},
        'user_review': user_review,
        'can_review': can_review,
        'add_review_form': add_form,
        'edit_review_form': edit_form,
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'categories':categories,
        'active_category':active_category
    }
    return render(request, 'app/detail.html', context)


def add_review(request):
    if request.method != "POST":
        return redirect('home')
    if not request.user.is_authenticated:
        messages.error(request, 'Vui lòng đăng nhập để đánh giá.')
        return redirect('login')

    product_id = request.POST.get('product_id')
    if not product_id:
        messages.error(request, 'Thiếu sản phẩm để đánh giá.')
        return redirect('home')

    # Mỗi user chỉ được review 1 lần / 1 sản phẩm
    if Review.objects.filter(product_id=product_id, user=request.user).exists():
        messages.info(request, 'Bạn đã đánh giá sản phẩm này rồi. Bạn có thể chỉnh sửa đánh giá của mình.')
        return redirect(f'/detail/?id={product_id}')

    # Chỉ user đã mua hàng (Order complete=True) mới được review
    order_item = (
        OrderItem.objects
        .filter(order__customer=request.user, order__complete=True, product_id=product_id)
        .select_related('order')
        .order_by('-date_added')
        .first()
    )
    if not order_item:
        messages.error(request, 'Bạn chỉ có thể đánh giá sau khi đã mua và đơn hàng hoàn tất.')
        return redirect(f'/detail/?id={product_id}')

    form = ReviewForm(request.POST, files=request.FILES)
    if not form.is_valid():
        # Render lại detail để giữ dữ liệu user đã nhập + show lỗi ngay tại form
        customer = request.user
        order, _ = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        categories = Category.objects.filter(is_sub=False)
        active_category = request.GET.get('category', '')
        # reuse summary/reviews from detail() via query
        base_reviews = (
            Review.objects
            .filter(product_id=product_id, status=Review.STATUS_APPROVED)
            .select_related('user')
            .prefetch_related('images')
        )
        rating_stats = base_reviews.aggregate(avg=Avg('rating'), count=Count('id'))
        star_counts_raw = base_reviews.values('rating').annotate(c=Count('id'))
        star_counts = {i: 0 for i in range(1, 6)}
        for row in star_counts_raw:
            star_counts[int(row['rating'])] = row['c']
        total_reviews = rating_stats.get('count') or 0
        star_percent = {i: (star_counts[i] * 100 / total_reviews) if total_reviews else 0 for i in range(1, 6)}
        paginator = Paginator(base_reviews.order_by('-created_at'), 6)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'app/detail.html', {
            'products': Product.objects.filter(id=product_id),
            'reviews': page_obj.object_list,
            'page_obj': page_obj,
            'review_count': total_reviews,
            'avg_rating': rating_stats.get('avg') or 0,
            'star_counts': star_counts,
            'star_percent': star_percent,
            'filters': {'rating': request.GET.get('rating'), 'has_comment': request.GET.get('has_comment'), 'has_image': request.GET.get('has_image'), 'sort': request.GET.get('sort', 'newest')},
            'user_review': None,
            'can_review': True,
            'add_review_form': form,
            'edit_review_form': None,
            'items': items,
            'order': order,
            'cartItems': cartItems,
            'categories': categories,
            'active_category': active_category,
        })

    review = form.save(commit=False)
    review.product_id = product_id
    review.user = request.user
    review.name = ''
    review.order_item = order_item
    review.is_verified_purchase = True
    review.status = Review.STATUS_APPROVED
    review.save()

    # Upload ảnh (nhiều ảnh)
    files = form.cleaned_data.get('images') or []
    for f in files[:6]:
        ReviewImage.objects.create(review=review, image=f)

    messages.success(request, 'Đã gửi đánh giá. Cảm ơn bạn!')
    return redirect(f'/detail/?id={product_id}')


@login_required
def edit_review(request, product_id):
    review = Review.objects.filter(product_id=product_id, user=request.user).first()
    if not review:
        messages.error(request, 'Không tìm thấy đánh giá của bạn để chỉnh sửa.')
        return redirect(f'/detail/?id={product_id}')

    if request.method != 'POST':
        return redirect(f'/detail/?id={product_id}')

    form = ReviewForm(request.POST, files=request.FILES, instance=review)
    if not form.is_valid():
        # Render lại detail để giữ dữ liệu + lỗi
        customer = request.user
        order, _ = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        categories = Category.objects.filter(is_sub=False)
        active_category = request.GET.get('category', '')

        base_reviews = (
            Review.objects
            .filter(product_id=product_id, status=Review.STATUS_APPROVED)
            .select_related('user')
            .prefetch_related('images')
        )
        rating_stats = base_reviews.aggregate(avg=Avg('rating'), count=Count('id'))
        star_counts_raw = base_reviews.values('rating').annotate(c=Count('id'))
        star_counts = {i: 0 for i in range(1, 6)}
        for row in star_counts_raw:
            star_counts[int(row['rating'])] = row['c']
        total_reviews = rating_stats.get('count') or 0
        star_percent = {i: (star_counts[i] * 100 / total_reviews) if total_reviews else 0 for i in range(1, 6)}
        paginator = Paginator(base_reviews.order_by('-created_at'), 6)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'app/detail.html', {
            'products': Product.objects.filter(id=product_id),
            'reviews': page_obj.object_list,
            'page_obj': page_obj,
            'review_count': total_reviews,
            'avg_rating': rating_stats.get('avg') or 0,
            'star_counts': star_counts,
            'star_percent': star_percent,
            'filters': {'rating': request.GET.get('rating'), 'has_comment': request.GET.get('has_comment'), 'has_image': request.GET.get('has_image'), 'sort': request.GET.get('sort', 'newest')},
            'user_review': review,
            'can_review': True,
            'add_review_form': ReviewForm(),
            'edit_review_form': form,
            'items': items,
            'order': order,
            'cartItems': cartItems,
            'categories': categories,
            'active_category': active_category,
        })

    updated = form.save(commit=False)
    updated.is_edited = True
    updated.save()

    # Xoá ảnh cũ nếu user chọn
    delete_ids = request.POST.getlist('delete_image_ids')
    if delete_ids:
        ReviewImage.objects.filter(review=review, id__in=delete_ids).delete()

    # Upload ảnh bổ sung (tối đa 6 ảnh tổng)
    current = review.images.count()
    remain = max(0, 6 - current)
    files = form.cleaned_data.get('images') or []
    for f in files[:remain]:
        ReviewImage.objects.create(review=review, image=f)

    messages.success(request, 'Đã cập nhật đánh giá của bạn.')
    return redirect(f'/detail/?id={product_id}')


@login_required
def toggle_helpful_review(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed'}, status=405)

    review = Review.objects.filter(id=review_id, status=Review.STATUS_APPROVED).first()
    if not review:
        return JsonResponse({'ok': False, 'error': 'Not found'}, status=404)

    vote, created = ReviewHelpfulVote.objects.get_or_create(review=review, user=request.user)
    if created:
        Review.objects.filter(id=review_id).update(helpful_count=F('helpful_count') + 1)
        review.refresh_from_db(fields=['helpful_count'])
        return JsonResponse({'ok': True, 'liked': True, 'helpful_count': review.helpful_count})
    else:
        vote.delete()
        Review.objects.filter(id=review_id, helpful_count__gt=0).update(helpful_count=F('helpful_count') - 1)
        review.refresh_from_db(fields=['helpful_count'])
        return JsonResponse({'ok': True, 'liked': False, 'helpful_count': review.helpful_count})

def category(request):
    # Header/cart context (giống home/cart/checkout) để số lượng giỏ luôn cập nhật.
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']

    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')

    products = Product.objects.none()
    if active_category:
        products = Product.objects.filter(category__slug=active_category).distinct()

    context = {
        'categories': categories,
        'products': products,
        'active_category': active_category,
        'items': items,
        'order': order,
        'cartItems': cartItems,
    }
    return render(request, 'app/category.html', context)

def search(request):
    # Giữ route `/search/` hiện có nhưng hỗ trợ cả GET (q=) để:
    # - giữ keyword trên URL (shareable)
    # - dùng được sort/filter/pagination bằng query params
    if request.method == "POST":
        q = (request.POST.get("searched") or "").strip()
        # Chuyển sang GET để giữ keyword trên ô search & URL rõ ràng
        return redirect(f"/search/?q={q}" if q else "/search/")

    q = (request.GET.get("q") or "").strip()
    sort = (request.GET.get("sort") or "relevant").strip()
    category_slug = (request.GET.get("cat") or "").strip()
    price_min_raw = (request.GET.get("min") or "").strip()
    price_max_raw = (request.GET.get("max") or "").strip()

    # Base queryset
    keys = Product.objects.all()

    # Search (gần đúng, không phân biệt hoa thường)
    if q:
        # Tìm theo từng token để kết quả "gần đúng" hơn (VD: "iphone 15")
        tokens = [t for t in q.split() if t]
        query = Q()
        for t in tokens:
            query &= Q(name__icontains=t)
        keys = keys.filter(query)
    else:
        # Keyword trống: hiển thị empty state + gợi ý
        keys = keys.none()

    # Filter theo danh mục (model hiện tại: Product.category is ManyToMany)
    if category_slug:
        keys = keys.filter(category__slug=category_slug).distinct()

    # Filter khoảng giá (nếu nhập sai thì bỏ qua, không crash)
    try:
        if price_min_raw != "":
            keys = keys.filter(price__gte=int(price_min_raw))
    except ValueError:
        price_min_raw = ""
    try:
        if price_max_raw != "":
            keys = keys.filter(price__lte=int(price_max_raw))
    except ValueError:
        price_max_raw = ""

    # Sort (best_selling chưa có dữ liệu -> fallback "relevant")
    if sort == "latest":
        keys = keys.order_by("-id")
    elif sort == "price_asc":
        keys = keys.order_by("price", "-id")
    elif sort == "price_desc":
        keys = keys.order_by("-price", "-id")
    elif sort == "best_selling":
        # Chưa có trường sold_count nên giữ nguyên "relevant"
        pass
    else:
        sort = "relevant"

    total_count = keys.count()

    # Pagination
    paginator = Paginator(keys, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Build querystring giữ lại filter/sort khi phân trang
    qs = request.GET.copy()
    qs.pop("page", None)
    querystring = qs.urlencode()

    # Cart context giữ nguyên như các trang khác
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']

    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')

    return render(
        request,
        "app/search.html",
        {
            # giữ key cũ để không phá template đang dùng "searched"/"keys"
            "searched": q,
            "q": q,
            "keys": page_obj.object_list,
            "page_obj": page_obj,
            "total_count": total_count,
            "sort": sort,
            "filters": {
                "cat": category_slug,
                "min": price_min_raw,
                "max": price_max_raw,
            },
            "querystring": querystring,
            "items": items,
            "order": order,
            "cartItems": cartItems,
            "categories": categories,
            "active_category": active_category,
        },
    )

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
    context = {
        'products': products,
        'cartItems': cartItems,
        'categories': categories,
        'active_category': active_category,
        'is_home': True,
    }
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
        # Hard-block server side: must confirm info first
        if order.get_cart_items <= 0:
            messages.error(request, "Giỏ hàng của bạn đang trống.")
            return redirect('checkout')

        if request.POST.get("is_info_confirmed") != "1":
            messages.error(request, "Vui lòng xác nhận thông tin trước khi đặt hàng.")
            return redirect('checkout')

        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        mobile = request.POST.get("phone")   # ⚠️ bạn đang dùng name="phone"
        pay_method = request.POST.get("pay_method")
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()

        errors = []
        if not name:
            errors.append("Vui lòng nhập họ và tên.")
        if not email:
            errors.append("Vui lòng nhập email.")
        elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            errors.append("Vui lòng nhập email hợp lệ.")

        digits = re.sub(r"[^\d]", "", mobile or "")
        if not digits:
            errors.append("Vui lòng nhập số điện thoại.")
        elif not re.match(r"^0\d{9,10}$", digits):
            errors.append("Vui lòng nhập số điện thoại hợp lệ.")

        if not (state or "").strip():
            errors.append("Vui lòng nhập thành phố.")
        if not (city or "").strip():
            errors.append("Vui lòng nhập quận/huyện.")
        if not (address or "").strip():
            errors.append("Vui lòng nhập địa chỉ.")

        if pay_method not in {"cod", "bank"}:
            errors.append("Vui lòng chọn phương thức thanh toán.")

        if errors:
            for msg in errors[:3]:
                messages.error(request, msg)
            return redirect('checkout')

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
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentication required'}, status=401)
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
    product_id_val = product.id
    line_removed = False
    line_qty = orderItem.quantity
    line_total = 0

    if orderItem.quantity <= 0:
        orderItem.delete()
        line_removed = True
        line_qty = 0
        line_total = 0
    else:
        line_total = orderItem.get_total()

    return JsonResponse({
        'ok': True,
        'action': action,
        'cartItems': order.get_cart_items,
        'cartTotal': order.get_cart_total,
        'productId': product_id_val,
        'lineRemoved': line_removed,
        'lineQuantity': line_qty,
        'lineTotal': line_total,
    })

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
        if not request.user.is_authenticated:
            messages.error(request, "Vui lòng đăng nhập để cập nhật hồ sơ.")
            return redirect('login')

        user = request.user
        profile = user.profile

        # USER INFO
        username = (request.POST.get("username") or "").strip()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        email = (request.POST.get("email") or "").strip()

        # PROFILE (read early so we can re-render with user's input on validation error)
        phone = (request.POST.get("phone") or "").strip()
        address = (request.POST.get("address") or "").strip()

        form_values = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
        }
        form_errors = {}

        # Required validation: username / first_name / last_name
        if not username:
            form_errors["username"] = "Vui lòng nhập tên đăng nhập"
        if not first_name:
            form_errors["first_name"] = "Vui lòng nhập họ"
        if not last_name:
            form_errors["last_name"] = "Vui lòng nhập tên"

        if form_errors:
            categories = Category.objects.filter(is_sub = False)
            active_category = request.GET.get('category','')
            context = {
                'items': items,
                'order': order,
                'cartItems': cartItems,
                'categories': categories,
                'active_category': active_category,
                'form_errors': form_errors,
                'form_values': form_values,
            }
            return render(request, 'app/update_profile.html', context)

        # Nếu người dùng để trống các trường quan trọng, giữ nguyên giá trị cũ
        # (tránh set username = "" hoặc toàn khoảng trắng làm không lưu được thay đổi khác).
        if username != user.username and User.objects.filter(username=username).exclude(pk=user.pk).exists():
            categories = Category.objects.filter(is_sub = False)
            active_category = request.GET.get('category','')
            context = {
                'items': items,
                'order': order,
                'cartItems': cartItems,
                'categories': categories,
                'active_category': active_category,
                'form_errors': {"username": "Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác."},
                'form_values': form_values,
            }
            return render(request, 'app/update_profile.html', context)

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        # Optional fields: allow empty values (user can clear)
        user.email = email

        # PROFILE
        profile.phone = phone
        profile.address = address
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        try:
            user.save()
            profile.save()
        except Exception:
            categories = Category.objects.filter(is_sub = False)
            active_category = request.GET.get('category','')
            context = {
                'items': items,
                'order': order,
                'cartItems': cartItems,
                'categories': categories,
                'active_category': active_category,
                'form_errors': {"__all__": "Không thể lưu thay đổi. Vui lòng kiểm tra lại thông tin."},
                'form_values': form_values,
            }
            return render(request, 'app/update_profile.html', context)

        messages.success(request, "Đã lưu thay đổi hồ sơ.")
        return redirect('profile')
    categories = Category.objects.filter(is_sub = False)
    active_category = request.GET.get('category','')
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'categories':categories, 'active_category':active_category}
    return render(request, 'app/update_profile.html', context)


@require_POST
@csrf_protect
def api_chat(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "Dữ liệu không hợp lệ."}, status=400)

    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []

    if not message:
        return JsonResponse({"ok": False, "error": "Vui lòng nhập nội dung trước khi gửi."}, status=400)
    if not isinstance(history, list):
        history = []

    safe_history = []
    for m in history[-20:]:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            safe_history.append({"role": role, "content": content.strip()})

    user_label = request.user.username if getattr(request, "user", None) and request.user.is_authenticated else None

    try:
        res = chat_reply(message=message, history=safe_history, user_label=user_label)
        return JsonResponse({"ok": True, "reply": res.reply, "provider": res.provider})
    except ChatProviderError as e:
        # Log rõ nguyên nhân để debug (không trả chi tiết ra client)
        logger.warning("ChatProviderError in /api/chat/: %s", str(e), exc_info=True)
        return JsonResponse(
            {"ok": False, "error": "Chatbot chưa sẵn sàng hoặc đang bận. Vui lòng thử lại sau."},
            status=503,
        )
    except Exception:
        return JsonResponse({"ok": False, "error": "Đã có lỗi xảy ra, vui lòng thử lại."}, status=500)
