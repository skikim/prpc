from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from profileapp.models import Profile
from django.http import JsonResponse
# Create your views here.


@csrf_exempt
def searchpage(request):
    data = []
    search_term = request.POST.get('search_term', '') if request.method == 'POST' else ''
    if request.method == 'POST':
        search_term = request.POST.get('search_term', None)
        print(search_term)
        data = list(Profile.objects.filter(
            Q(real_name__icontains=search_term) |
            Q(birth_date__icontains=search_term) |
            Q(phone_num__icontains=search_term)
        ).values('user__id', 'real_name', 'birth_date', 'phone_num', 'chart_num'))
    # return render(request, 'searchapp/searchpage.html', {'data': data, 'search_term': search_term})
    return render(request, 'searchapp/searchpage.html', {'data': data, 'search_term': search_term})


@csrf_exempt
def search(request):
    data = []
    if request.method == 'POST':
        search_term = request.POST.get('search_term', None)
        print(search_term)
        profiles = list(Profile.objects.filter(
            Q(real_name__icontains=search_term) |
            Q(birth_date__icontains=search_term) |
            Q(phone_num__icontains=search_term)
        ).values('user__id', 'real_name', 'birth_date', 'phone_num', 'chart_num'))
        for profile in profiles:
            data.append({
                'user_id': profile['user__id'],
                'real_name': profile['real_name'],
                'birth_date': profile['birth_date'],
                'phone_num': profile['phone_num'],
                'chart_num': profile['chart_num'],
            })
    return JsonResponse({'data': data, 'search_term': search_term})
