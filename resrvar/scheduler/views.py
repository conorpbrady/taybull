from django.shortcuts import render
from django.views import generic
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import *
from django.contrib.auth import authenticate
from django.urls import reverse
# Create your views here.

class IndexView(TemplateView):
    template_name = 'index.html'

# Venues
class VenueListView(LoginRequiredMixin, generic.ListView):
    ordering = '-created'
    template_name = 'venue_list.html'
    context_object_name = 'venue_list'

    def get_queryset(self):
        return Venue.objects.filter(
                owner = self.request.user,
                active = True)

class VenueCreateView(LoginRequiredMixin, CreateView):
    model = Venue
    template_name = 'venue_form.html'
    fields = ['venue_name', 'venue_id', 'reservation_type', 'display_name', 'res_platform',
              'tock_multiple_res_types', 'tock_type_to_select', 'resy_url']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('venues')

class VenueUpdateView(LoginRequiredMixin, UpdateView):
    model = Venue
    template_name = 'venue_form.html'
    fields = ['venue_name', 'venue_id', 'reservation_type', 'display_name', 'res_platform',
              'tock_multiple_res_types', 'tock_type_to_select', 'resy_url']

    def get_success_url(self):
        return reverse('venues')

# Requests
class RequestListView(LoginRequiredMixin, generic.ListView):
    template_name = 'request_list.html'
    context_object_name = 'request_list'
    ordering = '-created'

    def get_queryset(self):
        return ReservationRequest.objects.filter(
                owner = self.request.user)

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = ReservationRequest
    template_name = 'request_form.html'
    fields = ['booked_venue', 'decision_preference', 'scheduling_preference',
              'account', 'party_size', 'active']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.status = 'Created'
        return super().form_valid(form)

    def get_form_class(self):
        modelform = super().get_form_class()
        modelform.base_fields['booked_venue'].limit_choices_to={'owner': self.request.user}
        modelform.base_fields['decision_preference'].limit_choices_to={'owner': self.request.user}
        modelform.base_fields['scheduling_preference'].limit_choices_to={'owner': self.request.user}
        modelform.base_fields['account'].limit_choices_to={'owner': self.request.user}
        return modelform

    def get_success_url(self):
        return reverse('requests')

class RequestUpdateView(LoginRequiredMixin, UpdateView):
    model = ReservationRequest
    template_name = 'request_form.html'
    fields = ['booked_venue', 'decision_preference', 'scheduling_preference',
              'account', 'party_size', 'active']

    def get_form_class(self):
        modelform = super().get_form_class()
        modelform.base_fields['booked_venue'].limit_choices_to={'owner': self.request.user}
        modelform.base_fields['decision_preference'].limit_choices_to={'owner': self.request.user}
        modelform.base_fields['scheduling_preference'].limit_choices_to={'owner': self.request.user}
        return modelform

    def get_success_url(self):
        return reverse('requests')

# Preferences
class PreferenceListView(LoginRequiredMixin, generic.ListView):
    ordering = '-created'
    template_name = 'preference_list.html'
    context_object_name = 'preference_list'

    def get_queryset(self):
        return DecisionPreference.objects.filter(
                owner = self.request.user,
                active = True)

class PreferenceCreateView(LoginRequiredMixin, CreateView):
    model = DecisionPreference
    template_name = 'preference_form.html'
    fields = ['display_name', 'ideal_time', 'first_available', 'specific_date_flag', 'specific_date', 'threshold',
              'mon_rank', 'tue_rank', 'wed_rank', 'thu_rank', 'fri_rank', 'sat_rank', 'sun_rank']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('preferences')


class PreferenceUpdateView(LoginRequiredMixin, UpdateView):
    model = DecisionPreference
    template_name = 'preference_form.html'

    fields = ['display_name', 'ideal_time', 'first_available', 'specific_date_flag', 'specific_date', 'threshold',
              'mon_rank', 'tue_rank', 'wed_rank', 'thu_rank', 'fri_rank', 'sat_rank', 'sun_rank']

    def get_success_url(self):
        return reverse('preferences')

# Scheduling Preferences
class SchedulingView(LoginRequiredMixin, generic.ListView):
    ordering = '-created'
    template_name = 'scheduling_list.html'
    context_object_name = 'scheduling_list'

    def get_queryset(self):
        return SchedulingPreference.objects.filter(
                owner = self.request.user)

class SchedulingCreateView(LoginRequiredMixin, CreateView):
    model = SchedulingPreference
    template_name = 'scheduling_form.html'
    fields = ['display_name', 'frequency', 'specific_time', 'mon_run', 'tue_run', 'wed_run',
              'thu_run', 'fri_run', 'sat_run', 'sun_run', 'start_time', 'end_time']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
            return reverse('scheduling')

class SchedulingUpdateView(LoginRequiredMixin, UpdateView):
    model = SchedulingPreference
    template_name = 'scheduling_form.html'
    fields = ['display_name', 'frequency', 'specific_time', 'mon_run', 'tue_run', 'wed_run',
              'thu_run', 'fri_run', 'sat_run', 'sun_run', 'start_time', 'end_time']


    def get_success_url(self):
            return reverse('scheduling')
# Account Info
class AccountInfoListView(LoginRequiredMixin, generic.ListView):
    ordering = '-created'
    template_name = 'accountinfo_list.html'
    context_object_name = 'accountinfo_list'

    def get_queryset(self):
        return AccountInfo.objects.filter(owner = self.request.user)

class AccountInfoCreateView(LoginRequiredMixin, CreateView):
    model = AccountInfo
    template_name = 'accountinfo_form.html'

    fields = ['display_name', 'resy_api_key', 'resy_auth_token', 'resy_payment_id', 'tock_email', 'card_cvv']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('accountinfo')

class AccountInfoUpdateView(LoginRequiredMixin, UpdateView):
    model = AccountInfo
    template_name = 'accountinfo_form.html'


    fields = ['display_name', 'resy_api_key', 'resy_auth_token', 'resy_payment_id', 'tock_email', 'card_cvv']

    def get_success_url(self):
        return reverse('accountinfo')

# Run History
class HistoryListView(LoginRequiredMixin, generic.ListView):
    ordering = ['created']
    template_name = 'history_list.html'
    context_object_name = 'history_list'

    def get_queryset(self):
        return RunHistory.objects.filter(
                owner = self.request.user).order_by('-created')
