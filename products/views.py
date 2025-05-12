from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
from django.views.generic import ListView
from .models import Product, Line, ProductImage, Comment, Brand, SkinType, SkinCondition, ProductModel
from .forms import CommentForm
from django.db.models import Prefetch, Avg, Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .utils import convert_to_english_digits
from cart.forms import CartAddProductForm

# Create your views here.

@csrf_exempt
def upload_file(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    upload = request.FILES.get('upload')
    if not upload:
        return JsonResponse({'error': 'No file provided'}, status=400)

    # ایجاد مسیر ذخیره‌سازی
    file_name = upload.name
    file_path = os.path.join('ckeditor5', file_name)
    
    # ذخیره فایل
    saved_path = default_storage.save(file_path, upload)
    url = default_storage.url(saved_path)

    return JsonResponse({
        'url': url,
        'uploaded': '1',
        'fileName': file_name
    })


def line_products(request, slug):
    # دریافت لاین با اطلاعات برند
    line = get_object_or_404(
        Line.objects.select_related('brand').only(
            'name', 
            'slug', 
            'brand__name',
            'brand__image'
        ),
        slug=slug
    )
    
    # دریافت نوع مصرف از پارامتر GET
    usage_type = request.GET.get('usage_type', 'مصرف خانگی(Home care)')
    
    # فیلتر کردن محصولات فقط بر اساس لاین و نوع مصرف
    products_list = Product.objects.filter(line=line)
    if usage_type:
        products_list = products_list.filter(usage_type__name=usage_type)
    
    # بهینه‌سازی کوئری
    products_list = products_list.prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.only('image', 'product_id')
        )
    ).select_related(
        'brand',
        'line',
        'usage_type',
        'model',
        'volume_unit'
    ).only(
        'name',
        'slug',
        'short_description',
        'price_level_1',
        'price_level_2',
        'stock',
        'brand__name',
        'brand__image',
        'line__name',
        'usage_type__name',
        'model__name',
        'volume_value',
        'volume_unit__name'
    )

    # ایجاد Pagination
    paginator = Paginator(products_list, 12)  # 12 محصول در هر صفحه
    page = request.GET.get('page')
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # اگر page عدد نباشد، صفحه اول نمایش داده می‌شود
        products = paginator.page(1)
    except EmptyPage:
        # اگر page خارج از محدوده باشد، آخرین صفحه نمایش داده می‌شود
        products = paginator.page(paginator.num_pages)
    
    context = {
        'line': line,
        'products': products,
        'current_usage_type': usage_type
    }
    return render(request, 'product_list.html', context)

def product_detail(request, slug):
    # بهینه‌سازی کوئری برای نمایش جزئیات محصول
    product = get_object_or_404(
        Product.objects.prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.only('image', 'product_id')
            ),
            'skin_types',
            'skin_conditions',
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(status='approved')
                    .select_related('user')
                    .order_by('-created_at')
            )
        ).select_related(
            'brand',
            'line',
            'usage_type',
            'model',
            'volume_unit'
        ).only(
            'name',
            'slug',
            'short_description',
            'price_level_1',
            'price_level_2',
            'brand__name',
            'brand__image',
            'line__name',
            'line__slug',
            'usage_type__name',
            'model__name',
            'volume_value',
            'volume_unit__name'
        ),
        slug=slug
    )
    
    # محاسبه میانگین امتیاز
    avg_rating = product.comments.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    # دریافت محصولات مرتبط
    related_products = Product.objects.filter(
        usage_type=product.usage_type
    ).exclude(
        id=product.id
    )
    
    if product.skin_types.exists():
        related_products = related_products.filter(
            skin_types__in=product.skin_types.all()
        ).distinct()
    
    if product.skin_conditions.exists():
        related_products = related_products.filter(
            skin_conditions__in=product.skin_conditions.all()
        ).distinct()
    related_products = related_products.prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.only('image', 'product_id')
        ),
        'skin_types',
        'skin_conditions',
    ).select_related(
        'brand',
        'line',
        'usage_type',
    ).only(
        'name',
        'slug',
        'price_level_1',
        'price_level_2',
        'brand__name',
        'brand__image',
        'line__name',
        'usage_type__name',
    ).order_by('?')[:4]
    
    cart_add_form = CartAddProductForm()
    
    context = {
        'product': product,
        'related_products': related_products,
        'avg_rating': avg_rating,
        'comment_form': CommentForm() if request.user.is_authenticated else None,
        'cart_add_form': cart_add_form
    }
    return render(request, 'product_details.html', context)

@login_required
def submit_comment(request, slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            comment.user = request.user
            comment.save()
            messages.success(request, 'نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد.')
        else:
            messages.error(request, 'خطا در ثبت نظر. لطفاً دوباره تلاش کنید.')
    return redirect('products:product_detail', slug=slug)

@staff_member_required
def approve_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.status = 'approved'
    comment.save()
    messages.success(request, 'نظر با موفقیت تایید شد.')
    return redirect('admin:products_comment_changelist')

@staff_member_required
def reject_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.status = 'rejected'
    comment.save()
    messages.success(request, 'نظر با موفقیت رد شد.')
    return redirect('admin:products_comment_changelist')

@login_required
def search_page(request):
    """صفحه اصلی جستجو"""
    return render(request, 'products/search.html')

@login_required
def product_search(request):
    query = request.GET.get('q', '').strip()
    usage_type = request.GET.get('usage_type', 'مصرف خانگی(Home care)')
    model_id = request.GET.get('model')

    products = Product.objects.all()

    # اگر کاربر بارکد را با کیبورد فارسی وارد کرد، تبدیل به انگلیسی
    if query:
        query = convert_to_english_digits(query)

    # جستجوی متنی
    if query:
        products = products.filter(
            Q(barcode__icontains=query) |
            Q(name__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(line__name__icontains=query) |
            Q(short_description__icontains=query) |
            Q(long_description__icontains=query) |
            Q(model__name__icontains=query)
        )

    # فیلتر نوع مصرف (همیشه فعال است)
    if usage_type:
        products = products.filter(usage_type__name=usage_type)

    # فیلتر مدل محصول (در صورت نیاز)
    if model_id:
        products = products.filter(model__id=model_id)

    products = products.select_related('brand', 'line', 'usage_type', 'model').prefetch_related('images').distinct()

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'query': query,
        'current_usage_type': usage_type,
        'is_consult': False,
    }
    return render(request, 'products/search_results.html', context)

@login_required
def consult_search(request):
    usage_type = request.GET.get('usage_type', 'مصرف خانگی(Home care)')
    skin_type_id = request.GET.get('skin_type')
    skin_condition_id = request.GET.get('skin_condition')
    model_id = request.GET.get('model')

    products = Product.objects.all()

    if usage_type:
        products = products.filter(usage_type__name=usage_type)

    # Annotate only once for all ManyToMany fields
    products = products.annotate(
        num_skin_types=Count('skin_types', distinct=True),
        num_skin_conditions=Count('skin_conditions', distinct=True)
    )

    # AND logic for all consult fields
    if skin_type_id:
        products = products.filter(
            skin_types__id=skin_type_id,
            num_skin_types__gt=0
        )
    if skin_condition_id:
        products = products.filter(
            skin_conditions__id=skin_condition_id,
            num_skin_conditions__gt=0
        )
    if model_id:
        products = products.filter(model__id=model_id).exclude(model=None)

    products = products.select_related('brand', 'line', 'usage_type', 'model').prefetch_related('images').distinct()

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'query': '',
        'current_usage_type': usage_type,
        'is_consult': True,
        'skin_type_id': skin_type_id,
        'skin_condition_id': skin_condition_id,
        'model_id': model_id,
    }
    return render(request, 'products/search_results.html', context)

def consult_view(request):
    skin_types = SkinType.objects.all()
    skin_conditions = SkinCondition.objects.all()
    models = ProductModel.objects.all()
    return render(request, 'products/consult.html', {
        'skin_types': skin_types,
        'skin_conditions': skin_conditions,
        'models': models,
    })







