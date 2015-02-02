""" Welborn Productions - img - Forms
    Holds the django forms that are used by the img app.
    -Christopher Welborn 2-2-15
"""
from django import forms


class ImageUploadForm(forms.Form):
    image = forms.FileField(label='Image to upload')
