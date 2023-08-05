from django.contrib import admin

from noteapp.models import Note


# Register your models here.


class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'message', 'timestamp', 'is_read')
    search_fields = ['recipient', 'message', 'timestamp', 'is_read']


admin.site.register(Note, NoteAdmin)
