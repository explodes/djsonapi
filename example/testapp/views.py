from djsonapi import api
from djsonapi import serial

from example.testapp import forms
from example.testapp import models


@api.required_method("GET")
def home(request):
    """
    Return a standard welcome message
    """
    return api.ok(message="Welcome")


@api.required_method("GET", "POST")
@api.post_form(forms.ModelForm)
def report(request, form=None):
    # Choose the mode we're going to return report data back as
    mode = "full" if request.user.is_staff else "limited"

    # If we got a form
    if form:
        # save the report (form is guaranteed to be valid)
        new_report = form.save()
        # serialize the new report using the appropriate mode (turn into python dict)
        new_report_data = serial.serialize(new_report, mode=mode)
        # echo back the report
        return api.ok(report=new_report_data)
    else:
        # return the latest report
        try:
            # get the instance
            lastest_report = models.TestModel.objects.order_by("-pk").get()
            # serialize it using the appropriate mode (turn into python dict)
            lastest_report_data = serial.serialize(lastest_report, mode=mode)
            # return response as json
            return api.ok(latest_report=lastest_report_data)
        except models.TestModel.DoesNotExist:
            # latest report not found
            return api.error404()