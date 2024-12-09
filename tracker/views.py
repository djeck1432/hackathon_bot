from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import CreateView
from django.views.generic.list import ListView

from .forms import SignUpForm

class CreateUserView(CreateView):
    form_class = SignUpForm
    success_url = "/admin/"
    template_name = "signup.html"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """
        A GET request for this view.
        :param request: HttpRequest
        :param args: tuple
        :param kwargs: dict
        :return: HttpResponse
        """
        form = self.form_class()

        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """
        A POST request for this view.
        :param request: HttpRequest
        :param args: tuple
        :param kwargs: dict
        :return: HttpResponse
        """
        form = self.form_class(request.POST)

        if form.is_valid():
            new_user = form.save()
            login(request, new_user)

            return redirect(self.success_url)

        [messages.error(request, error_) for error_ in form.errors.values()]

        return render(request, self.template_name, {"form": form})