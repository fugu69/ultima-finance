from django import forms
from .models import Comment, PresentationComment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("comment",)

class PresentationCommentForm(forms.ModelForm):
    class Meta:
        model = PresentationComment
        fields = ("comment",)