from django.shortcuts import render

# Create your views here.
def monsters_index(request):
    return render(request, 'monsters.html')