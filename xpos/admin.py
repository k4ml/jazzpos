from django.contrib import admin

from xpos.models import Item, ItemPrice

class ItemPriceInline(admin.TabularInline):
    model = ItemPrice

class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemPriceInline,]
    search_fields = ['name',]

class ItemPriceAdmin(admin.ModelAdmin):
    list_display = ('item', 'customertype', 'price')
    list_filter = ('customertype',)

admin.site.register(Item, ItemAdmin)
admin.site.register(ItemPrice, ItemPriceAdmin)
