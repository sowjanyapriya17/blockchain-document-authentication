from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):

    class Meta:

        model = Document

        fields = [
            'document_id',
            'title',
            'document_type',
            'description',
            'file',
            'issue_date',
            'expiry_date',
        ]

        widgets = {

            'issue_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'expiry_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }