from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from profileapp.models import Profile
from django.http import JsonResponse, HttpResponseForbidden

MAX_SEARCH_RESULTS = 50


@login_required
def searchpage(request):
    if not request.user.is_superuser:
        return redirect('articleapp:index')
    data = []
    search_term = ''
    if request.method == 'POST':
        search_term = (request.POST.get('search_term') or '').strip()
        if search_term:
            data = list(Profile.objects.filter(
                Q(real_name__icontains=search_term) |
                Q(birth_date__icontains=search_term) |
                Q(phone_num__icontains=search_term)
            ).values('user__id', 'real_name', 'birth_date', 'phone_num', 'chart_num')[:MAX_SEARCH_RESULTS])
    return render(request, 'searchapp/searchpage.html', {'data': data, 'search_term': search_term})


@login_required
def search(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    data = []
    search_term = ''
    if request.method == 'POST':
        search_term = (request.POST.get('search_term') or '').strip()
        if search_term:
            profiles = list(Profile.objects.filter(
                Q(real_name__icontains=search_term) |
                Q(birth_date__icontains=search_term) |
                Q(phone_num__icontains=search_term)
            ).values('user__id', 'real_name', 'birth_date', 'phone_num', 'chart_num')[:MAX_SEARCH_RESULTS])
            for profile in profiles:
                data.append({
                    'user_id': profile['user__id'],
                    'real_name': profile['real_name'],
                    'birth_date': profile['birth_date'],
                    'phone_num': profile['phone_num'],
                    'chart_num': profile['chart_num'],
                })
    return JsonResponse({'data': data, 'search_term': search_term})
