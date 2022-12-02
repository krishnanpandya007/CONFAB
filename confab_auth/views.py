import hashlib
from confab import settings
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from confab_auth.forms import SignInForm
from django.contrib import messages
from django.contrib.auth import login
from django.core.mail import send_mail
from math import ceil

from confab_auth.models import Account
# from constants import FRONTEND_ROOT_URL
# Create your views here.
FRONTEND_ROOT_URL = "http://127.0.0.1:8000/"
universities_names_to_email = {
    'CHARUSAT': '@charusat.edu.in',
    'NIRMA': '@nirmauniversity.ac.in',
    'IIIT': '@iiit.ac.in',
    'OXFORD': '@ox.ac.uk',
    'DDU': '@ddu.ac.in',
}

# h.update(b"Nobody inspects the spammish repetition")

def simple_signin(request):
    # Defines SignIn Method
    if request.method == 'GET':
        return render(request, 'signin.html')
    elif request.method == 'POST':
        form = SignInForm(request.POST)

        if(form.is_valid()):
            try:
                print("THis is ", form.cleaned_data['email'])
                email_hash = hashlib.sha256(form.cleaned_data['email'].encode('utf-8')).hexdigest()
                target_account = Account.objects.get(email_hash=email_hash[:40])
                target_user = target_account.user
            except (User.DoesNotExist, Account.DoesNotExist) as e:
                print("No such Email Exists")
                messages.error(request,"No such email Associated with any User")
                return render(request, 'signin.html')
            
            try:
                assert target_user.check_password(form.cleaned_data['password']), "Password is incorrect"
            except AssertionError as e:
                print("Password is incorrect")
                messages.error(request,"Password is incorrect")
                return render(request, 'signin.html')

            messages.success(request, "Successfully Signed In")
            login(request, target_user)
            return redirect("qa:home")
        else:
            print("Password is incorrect")
            messages.info(request,"Please try again later")
            return render(request, 'signin.html')

def simple_signup2(request, email_hash):
    if request.method == "GET":

        try:
            target_account = Account.objects.get(email_hash=email_hash)
        except Account.DoesNotExist as e:
            print("No such Email Exists")
            messages.error(request,"No such email Associated with any User")
            return render(request, 'signup2.html', status=404)

        try:
            assert not target_account.is_valid, "Account is already verified"
        except AssertionError as e:
            print("Account is already verified")
            messages.error(request,"Account is already verified")
            return render(request, 'signup2.html', context={'email_hash': email_hash})

        return render(request, 'signup2.html', context={'email_hash': email_hash})
    elif request.method == "POST":

        university = request.POST.get('university')
        sem = request.POST.get('sem')
        year = ceil(int(sem)/2)
        major = request.POST.get('major')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')
        print("Here", year, major, university, password, re_password)

        try:
            assert password == re_password, "Password do not match!"
        except (AssertionError,) as e:
            messages.error(request, e)
            return redirect('signup')

        try:
            target_account = Account.objects.get(email_hash=email_hash)
            target_account.year = int(year)
            tu = target_account.user
            tu.set_password(password)
            tu.save()
            target_account.major = major
            target_account.save()
            login(request,target_account.user)
        except Account.DoesNotExist as e:
            print("No such Email Exists")
            messages.error(request,"No such email Associated with any User")
            return render(request, 'signup2.html', status=404)
        return redirect("qa:home")


def simple_signup2_submit(request,email_hash):
    university = request.POST.get('university')
    year = request.POST.get('year')
    major = request.POST.get('major')
    password = request.POST.get('password')
    re_password = request.POST.get('re_password')
    print("Here", year, major, university, password, re_password)

    try:
        assert password == re_password, "Password do not match!"
    except (AssertionError,) as e:
        messages.error(request, e)
        return redirect('signup')

    try:
        target_account = Account.objects.get(email_hash=email_hash)
        target_account.year = int(year)
        tu = target_account.user
        tu.set_password(password)
        tu.save()
        target_account.major = major
        target_account.save()
        login(request,target_account.user)
    except Account.DoesNotExist as e:
        print("No such Email Exists")
        messages.error(request,"No such email Associated with any User")
        return render(request, 'signup2.html', status=404)
    return redirect("qa:home") 


def verify_email(request):

    if request.method == "GET":
        return render(request, 'verify_email.html')
    
    elif request.method == "POST":
        user_email = request.POST.get('student_email')

        try:
            valid_student_email = [uni[0] for uni in universities_names_to_email.items() if user_email.endswith(uni[1])]
            assert len(valid_student_email) > 0, "Not Registered Student Email!"
        except AssertionError as e:
            print("Error while sending email", e)
            messages.error(request, "Error: "+str(e))
            return render(request, 'verify_email.html') 

        email_hash = hashlib.sha256(user_email.encode('utf-8')).hexdigest()
        try:

            new_user = User.objects.create(username=email_hash)

            new_account = Account.objects.create(email_hash=email_hash[:40], user=new_user)

            subject = "Verify Student Email - Confab"
            html_message_raw = "Hello " + "There, " + "!! \n" + f'Welcome to Confab Community!! \nThank you for visiting our website\n. We have also sent you a confirmation email, please confirm your email address By Clicking the link below.\n\n<a href="{FRONTEND_ROOT_URL}auth/signup/final/{email_hash[:40]}/">Verify Email</a> \n\nThanking You\n\nConfab Team'       
            from_email = settings.EMAIL_HOST_USER
            print("Debugger::", from_email)
            to_list = [user_email]
            status = send_mail(subject, "Please Confirm Your Email Address", from_email, to_list, fail_silently=False, html_message=html_message_raw)

            assert status == 1, "Email not sent"
            new_account.university = valid_student_email[0]
            new_user.save()
            new_account.save()
        except (Exception, AssertionError) as e:
            print("Error while sending email", e)
            messages.error(request, "Error While sending email")
            return render(request, 'verify_email.html')    

        messages.success(request, "Verification Email Sent to: "+ user_email)
        return render(request, 'verify_email.html')

def forgot_password(request):

    return render(request, 'forgot_password.html')

def whatisconfab(request):
    return render(request,'whatisconfab.html')
        