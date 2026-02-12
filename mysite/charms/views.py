from django.shortcuts import render


# This name MUST match what is in your weapons/urls.py
def charms_index(request):
    return render(request, 'charms.html')