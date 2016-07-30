import os
import traceback

from PIL import Image
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.conf import settings as django_settings
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from bootcamp.feeds.models import Feed
from bootcamp.feeds.views import feeds
from bootcamp.feeds.views import FEEDS_NUM_PAGES
from bootcamp.core.forms import ProfileForm, ChangePasswordForm


def home(request):
    return feeds(request)


def network(request):
    users = User.objects.filter(is_active=True).order_by('username')
    return render(request, 'core/network.html', {'users': users})


def profile(request, username):
    page_user = get_object_or_404(User, username=username)
    all_feeds = Feed.get_feeds().filter(user=page_user)
    paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
    feeds = paginator.page(1)
    from_feed = -1
    if feeds:
        from_feed = feeds[0].id
    return render(request, 'core/profile.html', {
        'page_user': page_user, 
        'feeds': feeds,
        'from_feed': from_feed,
        'page': 1
        })


@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.profile.job_title = form.cleaned_data.get('job_title')
            user.email = form.cleaned_data.get('email')
            user.profile.url = form.cleaned_data.get('url')
            user.profile.location = form.cleaned_data.get('location')
            user.save()
            messages.add_message(request, messages.SUCCESS, _('Your profile were successfully edited.'))
    else:
        form = ProfileForm(instance=user, initial={
            'job_title': user.profile.job_title,
            'url': user.profile.url,
            'location': user.profile.location
            })
    return render(request, 'core/settings.html', {'form':form})


@login_required
def picture(request):
    uploaded_picture = False

    if request.GET.get('upload_picture') == 'uploaded':
        uploaded_picture = True

    context = {'uploaded_picture': uploaded_picture,
               'media_url': django_settings.MEDIA_URL}
    return render(request, 'core/picture.html', context)


@login_required
def password(request):
    user = request.user

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)

        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            user.set_password(new_password)
            user.save()
            messages.add_message(request, messages.SUCCESS, _('Your password were successfully changed.'))
    else:
        form = ChangePasswordForm(instance=user)

    return render(request, 'core/password.html', {'form':form})


@login_required
def upload_picture(request):
    try:
        profile_pictures = django_settings.MEDIA_ROOT + '/profile_pictures/'
        if not os.path.exists(profile_pictures):
            os.makedirs(profile_pictures)

        f = request.FILES['picture']
        filename = profile_pictures + request.user.username + '_tmp.jpg'

        with open(filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        im = Image.open(filename)
        width, height = im.size

        if width > 350:
            new_width = 350
            new_height = (height * 350) / width
            new_size = new_width, new_height
            im.thumbnail(new_size, Image.ANTIALIAS)
            im.save(filename)
        return redirect('/settings/picture/?upload_picture=uploaded')
    except Exception as e:
        traceback.print_exc()
        return redirect('/settings/picture/')


@login_required
def save_uploaded_picture(request):
    try:
        x = int(request.POST.get('x'))
        y = int(request.POST.get('y'))
        w = int(request.POST.get('w'))
        h = int(request.POST.get('h'))

        tmp_filename = django_settings.MEDIA_ROOT + '/profile_pictures/' + request.user.username + '_tmp.jpg'
        filename = django_settings.MEDIA_ROOT + '/profile_pictures/' + request.user.username + '.jpg'
        im = Image.open(tmp_filename)

        cropped_im = im.crop((x, y, w+x, h+y))
        cropped_im.thumbnail((200, 200), Image.ANTIALIAS)
        cropped_im.save(filename)
        os.remove(tmp_filename)
    except Exception as e:
        traceback.print_exc()

    return redirect('/settings/picture/')
