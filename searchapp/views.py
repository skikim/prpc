from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from profileapp.models import Profile
# Create your views here.


@csrf_exempt
def search(request):
    data = []
    search_term = request.POST.get('search_term', '') if request.method == 'POST' else ''
    if request.method == 'POST':
        search_term = request.POST.get('search_term', None)
        data = list(Profile.objects.filter(
            Q(real_name__icontains=search_term) |
            Q(birth_date__icontains=search_term) |
            Q(phone_num__icontains=search_term)
        ).values('user__id', 'real_name', 'birth_date', 'phone_num', 'chart_num'))
    return render(request, 'searchapp/search.html', {'data': data, 'search_term': search_term})