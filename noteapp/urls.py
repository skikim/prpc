from django.urls import path
from . import views


app_name = 'noteapp'


urlpatterns = [
    path('send_notes/', views.send_note, name='send_notes'),
    path('display_notes/', views.display_notes, name='display_notes'),
    path('delete_notes/<int:note_id>/', views.delete_note, name='delete_notes'),
    path('notes_history/', views.notes_history, name='notes_history'),
    # path('delete_all_notes/', views.delete_all_notes, name='delete_all_notes'),
    path('delete_note_ajax/<int:note_id>/', views.delete_note_ajax, name='delete_note_ajax'),

]

