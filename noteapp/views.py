from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from noteapp.models import Note
from django.urls import reverse


@login_required
def send_note(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            recipient_id = request.POST.get('recipient_id')
            message = request.POST.get('message')
            recipient = User.objects.get(id=recipient_id)
            sender = request.user
            note = Note.objects.create(sender=sender, recipient=recipient, message=message)
            return redirect('/supers/supercreate3/')
        else:
            return render(request, 'noteapp/send_notes.html')
    else:
        return render(request, 'articleapp/index.html')


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.user == note.recipient:
        note.delete()
    return redirect('noteapp:display_notes')


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


@login_required
def notes_history(request):
    if request.user.is_superuser:
        dict_notes = Note.objects.filter(message__isnull=False).order_by('-id')[:120]
        context = {
            'notes': dict_notes
        }

        return render(request, 'noteapp/notes_history.html', context)
    elif not request.user.is_superuser:
        return redirect(reverse('articleapp:index'))