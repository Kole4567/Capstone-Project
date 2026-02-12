from django.shortcuts import render


# This name MUST match what is in your weapons/urls.py
def armors_index(request):
    return render(request, 'armors.html')
