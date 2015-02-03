""" Welborn Productions - img - Forms
    Holds the django forms that are used by the img app.
    -Christopher Welborn 2-2-15
"""
from django import forms


class ImageUploadForm(forms.Form):

    """ Simple form to upload an image with a title and description. """

    image = forms.FileField(
        label='Image to upload',
        required=True)

    title = forms.CharField(
        label='Title',
        required=False)

    description = forms.CharField(
        label='Description',
        widget=forms.Textarea,
        required=False)

    album = forms.CharField(label='Album', required=False)

    private = forms.BooleanField(label='Private')
