from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Workshop, WorkshopBrand, WorkshopRegistration
from .forms import WorkshopRegistrationForm
from django.conf import settings
from accounts.tasks import send_message_task
from django.db.models import Q

# Create your views here.

class WorkshopListView(ListView):
    model = Workshop
    template_name = 'workshop/workshop_list.html'
    context_object_name = 'workshops'
    paginate_by = 9

    def get_queryset(self):
        """
        نمایش ورکشاپ‌های آینده با ترتیب تاریخ
        همراه با اطلاعات برند برای بهینه‌سازی کوئری
        """
        return Workshop.objects.select_related('brand').filter(
            date__gte=timezone.now().date()
        ).order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ورکشاپ‌های آموزشی'
        return context


class WorkshopBrandView(ListView):
    model = Workshop
    template_name = 'workshop/workshop_brand.html'
    context_object_name = 'workshops'
    paginate_by = 9

    def get_queryset(self):
        """
        نمایش ورکشاپ‌های یک برند خاص
        """
        self.brand = get_object_or_404(WorkshopBrand, id=self.kwargs['brand_id'])
        return Workshop.objects.select_related('brand').filter(
            brand=self.brand,
            date__gte=timezone.now().date()
        ).order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        context['page_title'] = f'ورکشاپ‌های {self.brand.name}'
        return context


class WorkshopDetailView(DetailView):
    model = Workshop
    template_name = 'workshop/workshop_detail.html'
    context_object_name = 'workshop'

    def get_queryset(self):
        """
        بهینه‌سازی کوئری با select_related
        """
        return Workshop.objects.select_related('brand')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        workshop = self.object
        # ظرفیت و تعداد ثبت‌نام‌ها
        total_approved = workshop.registrations.filter(status='approved').count()
        total_pending = workshop.registrations.filter(status='pending').count()
        context['capacity'] = workshop.capacity
        context['approved_registrations_count'] = total_approved
        context['pending_registrations_count'] = total_pending
        context['remaining_capacity'] = max(0, workshop.capacity - (total_approved + total_pending))
        if self.request.user.is_authenticated:
            # بررسی وضعیت ثبت‌نام کاربر در این ورکشاپ
            context['user_registration'] = WorkshopRegistration.objects.filter(
                workshop=workshop,
                user=self.request.user
            ).select_related('user').first()
        return context

class WorkshopRegistrationView(LoginRequiredMixin, CreateView):
    model = WorkshopRegistration
    form_class = WorkshopRegistrationForm
    template_name = 'workshop/workshop_register.html'
    
    def get_workshop(self):
        return get_object_or_404(Workshop, id=self.kwargs['workshop_id'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workshop = self.get_workshop()
        # ظرفیت و تعداد ثبت‌نام‌ها
        total_approved = workshop.registrations.filter(status='approved').count()
        total_pending = workshop.registrations.filter(status='pending').count()
        context['workshop'] = workshop
        context['capacity'] = workshop.capacity
        context['approved_registrations_count'] = total_approved
        context['pending_registrations_count'] = total_pending
        context['remaining_capacity'] = max(0, workshop.capacity - (total_approved + total_pending))
        context['page_title'] = f'ثبت‌نام در {workshop.title}'
        return context
    
    def form_valid(self, form):
        workshop = self.get_workshop()
        # ظرفیت را چک کن
        total_approved = workshop.registrations.filter(status='approved').count()
        total_pending = workshop.registrations.filter(status='pending').count()
        if (total_approved + total_pending) >= workshop.capacity:
            form.add_error(None, 'ظرفیت این ورکشاپ تکمیل شده است و امکان ثبت‌نام جدید وجود ندارد.')
            return self.form_invalid(form)
        form.instance.workshop = workshop
        form.instance.user = self.request.user
        response = super().form_valid(form)
        # ارسال پیامک به کاربر و ادمین (همانند قبل)
        message = f"..."
        send_message_task.delay(
            self.request.user.phone_number,
            message,
            template='workshop-registration'
        )
        message = f"{self.request.user.phone_number}"
        send_message_task.delay(
            settings.ADMIN_PHONE,
            message,
            template='manager-workshop-notification'
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('workshop:workshop_detail', kwargs={'pk': self.kwargs['workshop_id']})

class ApprovedRegistrationsView(ListView):
    model = WorkshopRegistration
    template_name = 'workshop/approved_registrations.html'
    context_object_name = 'registrations'
    paginate_by = 10

    def get_queryset(self):
        queryset = WorkshopRegistration.objects.filter(
            status='approved'
        ).select_related('workshop', 'user').order_by('-workshop__date')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(workshop__title__icontains=search_query) |
                Q(barcode__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'لیست شرکت‌کنندگان تایید شده'
        context['search_query'] = self.request.GET.get('search', '')
        return context
