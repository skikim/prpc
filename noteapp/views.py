from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from noteapp.models import Note


@login_required
def send_note(request):
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        message = request.POST.get('message')
        recipient = User.objects.get(id=recipient_id)
        sender = request.user
        note = Note.objects.create(sender=sender, recipient=recipient, message=message)
        return redirect('superapp/supercreate')
    else:
        return render(request, 'noteapp/send_notes.html')


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.user == note.recipient:
        note.delete()
    return redirect('home')


# @login_required
# def delete_all_notes(request):
#     Note.objects.filter(recipient=request.user).delete()
#     return redirect('home')


@login_required
def display_notes(request):
    notes = Note.objects.filter(recipient=request.user)
    unread_notes_count = notes.filter(is_read=False).count()
    for note in notes:
        if not note.is_read:
            note.is_read = True
            note.save()
    return render(request, 'noteapp/display_notes.html', {'notes': notes, 'unread_notes_count': unread_notes_count})


