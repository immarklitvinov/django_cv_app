from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Profile
from itertools import chain
import random
from datetime import datetime
from django.template.loader import render_to_string
import pdfkit
import subprocess
from PIL import Image
import os
import tempfile
import fpdf

# Create your views here.

@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    return render(request, 'index.html', {'user_profile': user_profile})

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
            name = request.POST['name']
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.name = name
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            name = request.POST['name']
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.name = name
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        return redirect('settings')
    return render(request, 'setting.html', {'user_profile': user_profile})

def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                #log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                #create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
        
    else:
        return render(request, 'signup.html')

def signin(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')

    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


def export_pdf(request):
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=my_cv_' + str(datetime.now()) + '.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    
    user_profile = Profile.objects.get(user=request.user)
    html_string = render_to_string('./pdf-output.html', {'name': user_profile.name, 'bio': user_profile.bio, 'src': user_profile.profileimg, 'location': user_profile.location}) # pdf-output.html
    
    with open('render.html', 'w') as f:
        f.write(html_string)
    
    pdfkit.from_file('render.html', 'current_cv.pdf')
    
    with open('current_cv.pdf', "rb") as f:
        content = f.read()

    with tempfile.NamedTemporaryFile(delete=False) as output:
        output.write(content)        
        output.flush()
        
        output=open(output.name,'rb')
        response.write(output.read())
    
    
    return response