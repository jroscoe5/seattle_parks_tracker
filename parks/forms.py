from django import forms
from .models import Visit, VisitPhoto


class VisitForm(forms.ModelForm):
    """Form for recording a park visit."""
    
    class Meta:
        model = Visit
        fields = ['visit_date', 'notes', 'rating']
        widgets = {
            'visit_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'How was your visit?'
                }
            ),
            'rating': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
        }


class VisitPhotoForm(forms.ModelForm):
    """Form for uploading a photo."""
    
    class Meta:
        model = VisitPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),
            'caption': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Photo caption (optional)'
                }
            ),
        }


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads."""
    allow_multiple_selected = True


class MultiplePhotoForm(forms.Form):
    """Form for uploading multiple photos at once."""
    
    photos = forms.FileField(
        widget=MultipleFileInput(
            attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }
        ),
        required=False
    )
