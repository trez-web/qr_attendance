from django import forms
from django.contrib.auth.models import User
from .models import Meeting, MeetingStaff
from django.utils import timezone

class MeetingForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'border rounded p-2 w-full'}),
        label="Meeting Date & Time",
        input_formats=['%Y-%m-%dT%H:%M'],
        initial=timezone.now().strftime('%Y-%m-%dT%H:%M')
    )
    location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 w-full'}),
        label="Meeting Location"
    )

    class Meta:
        model = Meeting
        fields = ['title', 'date', 'location']

class MeetingStaffForm(forms.ModelForm):
    class Meta:
        model = MeetingStaff
        fields = ['meeting', 'staff']
        widgets = {
            'meeting': forms.Select(attrs={'class': 'border rounded p-2 w-full'}),
            'staff': forms.Select(attrs={'class': 'border rounded p-2 w-full'}),
        }

class CustomStaffForm(forms.ModelForm):
    staff = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        label="Select Staff",
        widget=forms.Select(attrs={'class': 'border rounded p-2 w-full'})
    )

    meeting = forms.ModelChoiceField(
        queryset=Meeting.objects.all(),
        label="Select Meeting",
        widget=forms.Select(attrs={'class': 'border rounded p-2 w-full'})
    )

    class Meta:
        model = MeetingStaff
        fields = ['meeting', 'staff']