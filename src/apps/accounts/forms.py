from django import forms


class RecruiterNotificationSettingsForm(forms.Form):
    notify_on_vote_overlap = forms.BooleanField(required=False)
    notify_on_contact_requests = forms.BooleanField(required=False)
    notify_on_security = forms.BooleanField(required=False)
