from django import forms

from example.testapp import models


class ReportForm(forms.ModelForm):
    class Meta:
        model = models.Report
