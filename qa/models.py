from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User as CustomUser
# from users.models import CustomUser


class QuestionManager(models.Manager):
    def new(self):
        return self.order_by('-added_at')

    def popular(self, limit=None):
        return self.order_by('-rating')[:limit] if limit else self.order_by('-rating')

    def get_starred(self, user):
        return self.filter(likes=user)


class QuestionCategoryManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    @staticmethod
    def popular_categories():
        # this method will return top 5 categories
        c = Category.objects.annotate(num_questions=models.Count('question'))
        cat = c.order_by('-num_questions')[:5]
        return cat


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    objects = QuestionCategoryManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.slug

    def get_url(self):
        return f"/category/{self.id}"

    def get_number(self):
        # this method returns a number of related questions
        c = Category.objects.annotate(num_questions=models.Count('question')).filter(id=self.id)
        return c[0].num_questions

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name) + str(self.id)
        super(Category, self).save(*args, **kwargs)


class Question(models.Model):
    title = models.CharField(blank=False, null=False, max_length=255)
    text = models.TextField()
    added_at = models.DateField(auto_now=True)
    edited_at = models.DateField(blank=True, null=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET(value='Deleted'))
    rating = models.IntegerField(default=0, blank=True)
    likes = models.ManyToManyField(CustomUser, related_name='get_likes', blank=True)
    category = models.ManyToManyField(Category, blank=True)

    objects = QuestionManager()

    def __str__(self):
        return self.title

    def get_url(self):
        return reverse('qa:question', kwargs={'qn_id': self.id})

    def get_like_toggle(self):
        print("THIS::", self.id)
        return reverse('qa:like', kwargs={'qn_id': self.id})

    def has_answer(self):
        res = len(self.answer_set.filter(best_answer=True))
        return True if res > 0 else False


class Answer(models.Model):
    added_at = models.DateField(auto_now=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, on_delete=models.SET(value='Deleted'))
    text = models.TextField(null=True)

    active = models.BooleanField(default=True)  # added in case i'll need to deactivate some answers fsr
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies',
                               on_delete=models.CASCADE)  # deals with comments on answers

    best_answer = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return self.text

