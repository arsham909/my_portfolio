from django import forms

class ContactMe(forms.Form):
    name = forms.CharField(max_length=50)
    email = forms.EmailField()
    subject = forms.CharField(max_length=250)
    request = forms.CharField(
        required=True,
        widget=forms.Textarea
    )
    
def contact_me_form(cd):
    subject = (
                f"{cd['name']} ({cd['email']})  "
                f"{cd['subject']}"
            )
    message = (
        f"{cd['request']}"
    )
    return {'subject':subject,'message':message}
