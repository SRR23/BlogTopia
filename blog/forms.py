from django import forms

from .models import Blog
from tinymce.models import HTMLField

class TextForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, required=True)
    


class AddBlogForm(forms.ModelForm):
    description = HTMLField()
    
    class Meta:
        model = Blog
        fields = (
            "title",
            "category",
            "banner",
            "description"
        )