from django.contrib import admin

# редактирование товаров
from main.models import ChristmasTree, Category, Customer, Cart, CartProduct, Order, ChristmasTreeHeight, \
    ChristmasTreeChoices


class ProductAdmin(admin.ModelAdmin):
    search_fields = ("title", "slug", "description")
    readonly_fields = ('image_tag',)


@admin.register(ChristmasTree)
class ChristmasTreeAdmin(ProductAdmin):
    list_display = ("title", "product_type", "price")
    list_filter = ("product_type",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    filter_horizontal = ('products',)
    readonly_fields = ('final_price', "total_products")


@admin.register(CartProduct)
class CartProductAdmin(admin.ModelAdmin):
    search_fields = ("object_id",)
    readonly_fields = ('get_tree_height',)

    def get_tree_height(self, obj):
        tree_height = obj.get_tree_height_object()
        if tree_height:
            return f"Высота дерева: {tree_height.tree_height.tree_height} м., цена за штуку: {tree_height.tree_height.tree_price} руб."
        else:
            return None


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    search_fields = ("customer", "pk",)
    list_display = ("__str__", "created_at", "customer")
    list_filter = ("created_at", "status")
    readonly_fields = ("order_content_description",)


@admin.register(ChristmasTreeHeight)
class ChristmasTreeHeightAdmin(admin.ModelAdmin):
    pass
    # search_fields = ("object_id",)


@admin.register(ChristmasTreeChoices)
class ChristmasTreeHeightAdmin(admin.ModelAdmin):
    pass
    # search_fields = ("object_id",)
