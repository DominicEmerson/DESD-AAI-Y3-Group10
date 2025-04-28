from claims.models import Accident, Claim, Vehicle, Driver, Injury
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView

import utils

#TODO implement class based views for all views
#TODO implement a custom mixin for each role to avoid repeating the same code in each view

# class EnduserRequiredMixin:
#     def test_func(self):
#         return utils.is_engineer(self.request.user)

# class ClaimDashboardView(EnduserRequiredMixin, LoginRequiredMixin, DetailView):

@never_cache
@login_required
@user_passes_test(utils.is_engineer, login_url='role_redirect')
def engineer_page(request):
    context = {
        'accidents': Accident.objects.all(),
        'claims': Claim.objects.all(),
        'vehicles': Vehicle.objects.all(),
        'drivers': Driver.objects.all(),
        'injuries': Injury.objects.all(),
    }
    return render(request, 'engineer/engineer.html', context)