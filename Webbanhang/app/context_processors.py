from __future__ import annotations

from .models import Category, Order


def shop_context(request):
    """
    Context dùng chung cho header/cart/checkout.
    - Không đổi route/view/model hiện có.
    - Đảm bảo mọi template luôn có: categories, active_category, items, order, cartItems.
    """
    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get("category", "")

    if request.user.is_authenticated:
        order, _ = Order.objects.get_or_create(customer=request.user, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = {"get_cart_items": 0, "get_cart_total": 0}
        cartItems = 0

    return {
        "categories": categories,
        "active_category": active_category,
        "items": items,
        "order": order,
        "cartItems": cartItems,
    }

