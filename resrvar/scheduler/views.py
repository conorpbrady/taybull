from django.shortcuts import render
from django.views import generic
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import *

# Create your views here.

class LoginView(TemplateView):
    template_name = 'login.html'

class IndexView(TemplateView):
    template_name = 'index.html'

class BookView(LoginRequiredMixin, generic.ListView):
    login_url = '/login'
    redirect_field_name = 'redirect_to'

    context_object_name = 'reservation_request'
    ordering = '-created'
    def get_queryset(self):
        return ReservationRequest.objects.filter(
                owner = self.request.user,
                active = True)

class PreferenceView(LoginRequiredMixin, generic.ListView):
    ordering = '-created'
    def get_queryset(self):
        return DecisionPreference.objects.filter(
                owner = self.request.user,
                active = True)

class RunHistoryView(LoginRequiredMixin, generic.ListView):
    ordering = '-created'
    def get_queryset(self):
        return RunHistory.objects.filter(
                owner = self.request.user,
                active = True)
