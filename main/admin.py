from django.contrib import admin


# редактирование товаров

class CategoryAdmin(admin.ModelAdmin):
    pass

class SubcategoryAdmin(admin.ModelAdmin):
    pass

class GoodAdmin(admin.ModelAdmin):
    pass

class ImageAdmin(admin.ModelAdmin):
    pass
"""
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory,SubcategoryAdmin)
admin.site.register(Good, GoodAdmin)
admin.site.register(Image, ImageAdmin)
"""