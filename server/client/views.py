from django.shortcuts import render, get_object_or_404, redirect


# Models Import
from .models import *
from authentication.models import *


def index(request):
    return render(request, 'client/index.html')
