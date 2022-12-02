from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.generic import RedirectView

from .models import Question, Answer, Category
# from users.models import CustomUser
from django.contrib.auth.models import User as CustomUser
from .forms import AskForm, AnswerForm, CategoryForm


def home(request, a_id=None):
    """Here we're trying to serve two urls with one view: / and popular"""
    if(not request.user.is_authenticated):
        return redirect('signin')
    new_questions = Question.objects.new()
    top = Question.objects.popular(5)
    pref = ''
    title = 'Main Page: Most Recent'

    if 'popular' in request.path:
        # this part would return 'popular questions', sorted by rating field
        new_questions = Question.objects.popular()
        pref = '/popular/'
        title = 'Most Popular'

    if 'author' in request.path and a_id:
        # this case returns Questions by an Author chosen by an a_id
        auth = get_object_or_404(CustomUser, id=a_id)
        new_questions = auth.question_set.new()
        title = f'Questions by {auth.username}'

    if 'category' in request.path and a_id:
        cat = get_object_or_404(Category, id=a_id)
        new_questions = cat.question_set.new()
        title = f'Category: {cat.name}'

    if 'search' in request.GET:
        search_term = request.GET['search']
        new_questions = new_questions.filter(title__icontains=search_term) | \
                        new_questions.filter(text__icontains=search_term)
        title = f'Search results for {search_term}'
    is_all=True
    if 'college_filter' in request.GET:
        college_filter = request.GET['college_filter']
        if(college_filter != 'all'):
            is_all=False
            new_questions = Question.objects.filter(author__account__university=college_filter)
        title = college_filter.replace("_", " ").title()

    # let's create a paginator object
    limit = request.GET.get('limit', 10)
    page = int(request.GET.get('page', 1))
    paginator = Paginator(new_questions, limit)
    paginator.baseurl = pref + '?page='
    try:
        # try to deliver a page.
        questions = paginator.page(page)

    except EmptyPage:
        # If the page is out of range (e.g. 9999), serve the last one available.
        questions = paginator.page(paginator.num_pages)


    return render(request, 'qa/questions.html', {
        'questions': questions,
        'paginator': paginator,
        'title': title,
        'top': top,
        'top_categories': Category.objects.popular_categories(),
        'is_all': is_all
    })


def question(request, qn_id):
    """this view will return a single question + related answers by id and CREATE answers"""

    qn = get_object_or_404(Question, id=qn_id)
    top = Question.objects.popular(5)
    # list of active parent answers
    answers = qn.answer_set.filter(active=True, parent__isnull=True)
    ans_form = AnswerForm()

    if request.method == 'POST':
        # here is an answer form call(by question id)
        if request.user.is_authenticated:
            ans_form = AnswerForm(request.POST)

            if ans_form.is_valid():

                # here is a code for replies on answers (answers have 'parents'). It works (mostly),\
                # but I am not so sure if this feature is still relevant: think it over later

                try:  # get parent comment id from hidden input
                    parent_id = request.POST.get('parent_id')
                except (KeyError,):
                    parent_id = None

                if parent_id:  # if parent_id has been submitted get parent_obj id
                    parent_obj = Answer.objects.get(id=parent_id)
                    if parent_obj:  # if parent object exist
                        reply_answer = ans_form.save(commit=False)  # create reply object
                        reply_answer.parent = parent_obj  # assign parent_obj to reply
                        # end of the sub-answers code

                # normal answer (without 'parents')
                ans_form = ans_form.save(commit=False)
                # pre-save form, but don't commit changes to the DB yet
                ans_form.author = request.user
                ans_form.question = qn
                # here we are adding user and question objects to the form and finally save it to the DB
                ans_form.save()

            return redirect(qn.get_url())

        else:
            m = messages.warning(request, 'Sorry! You have to login first!')
            return redirect(f'/auth/signin?next={qn.get_url()}', m)
    print("QN::", qn.get_like_toggle)
    return render(request, 'qa/question.html', {'qn': qn, 'answers': answers,
                                                'ans_form': ans_form, 'top': top,
                                                'top_categories': Category.objects.popular_categories(), })


class QuestionLikeRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        qn_id = self.kwargs.get('qn_id')
        qn = get_object_or_404(Question, pk=qn_id)
        url_ = qn.get_url()
        user = self.request.user

        if user.is_authenticated:

            if user in qn.likes.all():
                qn.likes.remove(user)
                qn.rating -= 1
            else:
                qn.likes.add(user)
                qn.rating += 1

            qn.save()

        return url_


class QAnsweredRedirect(RedirectView):
    # here a question author can assign a
    # 'best answer' badge (and cancel it)

    def get_redirect_url(self, *args, **kwargs):
        a_id = self.kwargs.get('a_id')
        ans = get_object_or_404(Answer, id=a_id)
        url_ = ans.question.get_url()
        user = self.request.user
        if user.is_authenticated and user == ans.question.author:
            if ans.best_answer:
                ans.best_answer = False
            else:
                ans.best_answer = True
            ans.save()
        return url_


@login_required
def ask(request):
    """create new question"""

    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.author = request.user
            f.save()

            # When using commit=False, we have to call save_m2m() manually
            # m2m relationships require the parent object to be saved first
            # maybe it is best to move the whole thing to the forms
            # obviously the view is getting to fat

            form.save_m2m()
            m = messages.success(request, 'OK! The question was created')
            return redirect(f.get_url(), m)
    else:
        form = AskForm()

    return render(request, 'qa/askform.html', {'form': form})


@login_required
def delete(request, obj_type, o_id):
    """ this view simply deletes both Questions, Answers and Categories"""

    choose = {'q': [Question, 'question', '/'],
              'a': [Answer, 'answer', ''],
              'c': [Category, 'category', '/categories'], }
    try:
        obj = get_object_or_404(choose[obj_type][0], id=o_id)
        permission = True if obj_type == 'c' else obj.author == request.user
        if request.method == "POST" and permission:
            obj.delete()
            m = messages.success(request, f'OK! The {choose[obj_type][1]} was deleted')
            return HttpResponseRedirect(choose[obj_type][2], m) if obj_type in ['q', 'c'] \
                else redirect(obj.question.get_url(), m)
    except (KeyError,):
        return redirect('/')


@login_required
def edit(request, obj_type, o_id):
    """this is edit view for both Questions and Answers"""

    choose = {'q': [Question, AskForm, 'qa/askform.html', 'question'],
              'a': [Answer, AnswerForm, 'qa/edit.html', 'answer'],
              'c': [Category, CategoryForm, 'qa/askform.html', 'category']}

    try:
        obj = get_object_or_404(choose[obj_type][0], id=o_id)
        # now let's decide if the user can edit the object at all
        permission = True if obj_type == 'c' else obj.author == request.user
        red = '/categories'  # redirect afterwards

        if request.method == "POST" and permission:
            form = choose[obj_type][1](request.POST, instance=obj)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.added_at = timezone.now()
                m = messages.success(request, f"The {choose[obj_type][3]} was successfully edited")
                obj.save()
                form.save_m2m()

                if obj_type != 'c':
                    red = obj.get_url() if obj_type == 'q' else obj.question.get_url()

                return HttpResponseRedirect(red, m)
        else:
            form = choose[obj_type][1](instance=obj)

        return render(request, choose[obj_type][2], {'form': form})

    except (KeyError,):
        raise Http404


@login_required
def create_category(request):
    # with this view we create new category objects, login required

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            m = messages.success(request, f'Success! You\'ve just created a new category!')
            return HttpResponseRedirect('/categories', m)
    else:
        form = CategoryForm()

    return render(request, 'qa/askform.html', {'form': form})


def serve_categories(request):
    # the view will basically return a list of all categories ordered by id

    cat = Category.objects.all().order_by('id')
    top = Question.objects.popular(5)  # this is shown on the right widget

    title = 'Categories'
    limit = request.GET.get('limit', 10)
    page = int(request.GET.get('page', 1))
    paginator = Paginator(cat, limit)
    paginator.baseurl = '?page='
    categories = paginator.page(page)

    return render(request, 'qa/categories.html', {'categories': categories,
                                                  'paginator': paginator,
                                                  'title': title,
                                                  'top': top,
                                                  'top_categories': Category.objects.popular_categories(), })


@login_required
def activity(request, auth_id):
    auth = get_object_or_404(CustomUser, id=auth_id)

    if request.user.id == auth.id:

        my_questions = Question.objects.filter(author=auth)
        my_answers = Answer.objects.filter(author=auth)

        my_starred = Question.objects.get_starred(auth)

        return render(request, 'qa/activity.html', {'title': f'{auth.username}\'s personal page',
                                                    'my_questions': my_questions,
                                                    'my_answers': my_answers,
                                                    'my_starred': my_starred})
    else:
        return HttpResponseRedirect('/', messages.warning(request, 'Oooups! The Wrong Way!'))

def contactus(request):
    return render(request,'qa/contactus.html')

def about_us(request):
    return render(request,'qa/about_us.html')

def Feedback(request):
    return render(request,'qa/Feedback.html')