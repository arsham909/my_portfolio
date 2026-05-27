from django import forms

from common.utils import sanitize_header


class ContactMe(forms.Form):
    name = forms.CharField(max_length=50)
    email = forms.EmailField()
    subject = forms.CharField(max_length=250)
    request = forms.CharField(
        required=True,
        widget=forms.Textarea
    )


def contact_me_form(cd):
    name = sanitize_header(cd['name'])
    email = sanitize_header(cd['email'])
    user_subject = sanitize_header(cd['subject'])
    subject = f"{name} ({email})  {user_subject}"
    message = f"{cd['request']}"
    return {'subject': subject, 'message': message}
