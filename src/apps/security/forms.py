from django import forms


class CaptchaInlineForm(forms.Form):
    captcha_id = forms.CharField(max_length=64)
    captcha_answer = forms.CharField(max_length=16)
    code = forms.CharField(max_length=6)
