from django import forms
from .models import NGO

class NGOProfileForm(forms.ModelForm):
    class Meta:
        model = NGO
        fields = [
            'name', 'mission', 'contact_person', 'contact_number', 
            'email', 'website', 'address', 'bank_name', 'account_number',
            'ifsc_code', 'services', 'facebook', 'instagram', 'other_social', 'documents'
        ]
    
    # Optional fields: website, social media URLs can be blank or None
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'E.g. www.example.com'}))
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'Facebook URL'}))
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'Instagram URL'}))
    other_social = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'Other Social URL'}))

    # Services: checkbox group, handle multiple selections
    services = forms.MultipleChoiceField(
        choices=[
            ('educational', 'Educational'),
            ('healthcare', 'Healthcare'),
            ('clothing', 'Clothing'),
            ('food', 'Food'),
            ('shelter', 'Shelter'),
            ('animal', 'Animal')
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False  # Not mandatory
    )

    # Document upload: allow for optional document uploads
    documents = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))

    # You can add any additional validation for other fields if necessary
    def clean_services(self):
        services = self.cleaned_data.get('services')
        # Ensure services is a list or None if empty
        return services if services else None
