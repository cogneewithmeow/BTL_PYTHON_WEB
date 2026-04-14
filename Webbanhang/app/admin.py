from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
admin.site.register(Profile)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'rating', 'status', 'is_verified_purchase', 'helpful_count', 'created_at')
    list_filter = ('status', 'rating', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'created_at')
    search_fields = ('review__product__name', 'review__user__username')
    ordering = ('-created_at',)


@admin.register(ReviewHelpfulVote)
class ReviewHelpfulVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'user', 'created_at')
    search_fields = ('review__product__name', 'user__username')
    ordering = ('-created_at',)
