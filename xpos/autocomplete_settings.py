from autocomplete.views import AutocompleteSettings
from autocomplete.views import autocomplete

from xpos.models import Item

class ItemAutocompleteSettings(AutocompleteSettings):
    queryset = Item.objects.all()
    search_fields = ('name',)
    login_required = True

autocomplete.register('items', ItemAutocompleteSettings)
