from django.forms import ModelForm
from .models import Question, Answer, Category

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field


class AskForm(ModelForm):
    """this is for creating new questions. Made it with ModelForm"""

    class Meta:
        """let's get field names from the model"""
        model = Question
        fields = ['title', 'text', 'author', 'category']
        exclude = ('author',)  # need to exclude this to pre-save form


class AnswerForm(ModelForm):
    """this is an answer form"""

    def __init__(self, *args, **kwargs):
        """here I am using the FormHelper class and its attributes to make the form look nicer"""

        super(AnswerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = "form-control"
        self.helper.form_id = 'id-answerForm'
        self.helper.layout = Layout(
            Field('text', style="height:15ch"),
        )

        self.helper.add_input(Submit('submit', 'Add Answer'))
        self.helper.form_show_labels = False  # don't want it to draw the actual model field name

    class Meta:
        model = Answer
        fields = ['text']
        exclude = ('author', 'question')


class CategoryForm(ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description']
