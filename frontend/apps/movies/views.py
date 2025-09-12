from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

def movie_list(request):
    """Page d'accueil - redirige vers le login"""
    return redirect('users:login')
