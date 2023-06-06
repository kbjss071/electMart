from django import forms
from .models import Rating

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['subject', 'review', 'rating']