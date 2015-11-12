import logging
from functools import wraps

from django import http
from django.conf import settings

from djsonapi import serial

log = logging.getLogger("djsonapi")

FORM_METHOD_TYPES = ["POST", "PUT", "PATCH"]

## JSON Builder ##

def json_response(status, ok, message, **body):
    """
    Return an HttpResponse with a content type of "application/json" and the given status code.
    The JSON will have an "ok" status, message, and optional body.
    """
    bag = {
        "ok": ok,
    }
    if body:
        bag["body"] = body
    if message:
        bag["message"] = message
    response = http.HttpResponse(serial.dumps(bag), status=status)
    response["Content-type"] = "application/json; charset=utf-8"
    return response


## JSON Returners ##

def ok(message=None, **body):
    """
    Return a JSON response with an 200 status code, "ok" flag, optional message, and optional body.
    """
    return json_response(200, True, message, **body)


def error(status, message=None, **body):
    """
    Return a JSON response with a specific status code, "error" flag, optional message, and optional body.
    """
    return json_response(status, False, message, **body)


def error400(**body):
    """
    Return a JSON response with a 400 status code, "error" flag, "Not Found" message, and optional body.
    """
    return json_response(400, False, "Bad Request", **body)


def error403(**body):
    """
    Return a JSON response with a 403 status code, "error" flag, "Not Found" message, and optional body.
    """
    return json_response(403, False, "Forbidden", **body)


def error404(**body):
    """
    Return a JSON response with a 404 status code, "error" flag, "Not Found" message, and optional body.
    """
    return json_response(404, False, "Not Found", **body)


def error405(**body):
    """
    Return a JSON response with a 405 status code, "error" flag, "Method Not Supported" message, and optional body.
    """
    return json_response(405, False, "Method Not Supported", **body)


def invalid(message, **body):
    """
    Return a JSON response with a 400 status code, "error" flag, custom message, and optional body.
    """
    return error(400, message=message, **body)


def invalid_form(form):
    """
    Return a JSON response containing form error information.
    """
    return invalid("Invalid Form", errors=form.errors)


def exception(exc, debug=settings.DEBUG, log_error=True, **body):
    """
    Return a JSON response with a 500 status code, "error" flag, message, and optional body.

    The message will be "Internal Server Error" when `DEBUG` is `False`
    Otherwise, debug information about the exception will be given.

    Optionally, the error can be logged using the "djsonapi" logger.
    """
    log.error("Returning internal server error",
              exc_info=True) if log_error else None
    if debug:
        return error(500, "DEBUG: %s" % (str(exc)))
    else:
        return error(500, "Internal Server Error")


## Decorators ##

def catch500(log_error=True):
    """
    Wrap the whole view in an exception handler that returns an `exception` response if an exception occurs.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                return func(request, *args, **kwargs)
            except Exception as exc:
                return exception(exc, args=args, kwargs=kwargs,
                                 log_error=log_error)

        return wrapper

    return decorator


def login_required(login_url=None):
    """
    Validate that the request has a user who is authenticated.
    Otherwise return 401 "Unauthorized" and an optional login_url location in the body.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated():
                return func(request, *args, **kwargs)
            else:
                if login_url:
                    return error(401, "Unauthorized", login_url=login_url)
                else:
                    return error(401, "Unauthorized")

        return wrapper

    return decorator


def required_method(*methods, **kwargs):
    """
    Require specific HTTP Methods.

    Return 405 "Method Not Supported" if the condition is not met.

    ex.
    @require_method("POST")
    def home(request, post=None):
        pass

    @require_method("POST", "PUT", "GET")
    def home(request, post=None, put=None):
        pass

    When the method is "POST" or "PUT", load the body as JSON and
    pass the data down into the decorated function as
    `post=<json_data>` or `put=<json_data>`

    If the request body fails to parse as JSON, 400 "Invalid JSON POST" or "Invalid JSON PUT" will be returned.

    Optional kwarg: "debug" : by default it is `True` in `DEBUG` mode.
    When `True`, if the body fails to parse as JSON, an exception will be contained in the response body.
    @require_method("POST", debug=True)
    """

    debug = kwargs.get("debug", settings.DEBUG)

    def required_methods_decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # if the request method is acceptable
            if request.method in methods:
                # if its post
                if request.method in FORM_METHOD_TYPES:
                    # convert the body into JSON
                    if request.body:
                        try:
                            # parse that body
                            post = serial.loads(request.body)
                        except Exception as exc:
                            # unless it doesnt parse
                            if debug:
                                return invalid(
                                    "Invalid JSON %s" % request.method,
                                    exception=str(exc))
                            else:
                                return invalid(
                                    "Invalid JSON %s" % request.method)
                    else:
                        post = {}
                    # and return the result
                    kwarg_name = request.method.lower()
                    kwargs[kwarg_name] = post
                    return func(request, *args, **kwargs)
                # if its not post, return the function
                return func(request, *args, **kwargs)
            else:
                # invalid request method
                return error405()

        return wrapper

    return required_methods_decorator


def post_form(form_klass, form_method_types=FORM_METHOD_TYPES,
              add=lambda request: {}):
    """
    Intercept posts/puts and send that data to a form.

    `form_klass` can be a factory that accepts (request, data) or a django.forms.Form that accepts data=<post>

    If the form validates, pass the form as a kwarg to the view function.

    If the form does not validate, respond with json describing the form errors (400 "Invalid Form")

    This decorator must be used in conjunction with `@required_method`

    e.x.

    @csrf_exempt
    @required_method("GET", "POST")
    @post_form_decorator(forms.NewUserForm)
    def user(request, form=None):
        if form:
            user = form.save()
        else:
            user = request.user

        data = serial.serialize(user, mode="current_user")
        return api.ok(user=data)
    """

    def post_form_decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method in form_method_types:

                # Retrieve POST/PUT data from kwargs
                if request.method in FORM_METHOD_TYPES:
                    kwarg_name = request.method.lower()
                    post = kwargs.pop(kwarg_name, None)
                else:
                    # GET
                    post = dict(request.GET.iteritems())

                # Add extras
                add_this = add(request)
                post.update(add_this)

                # Create form
                if isinstance(form_klass, type(
                        lambda: None)) and form_klass.__name__ == "<lambda>":
                    form = form_klass(request, post)
                    if isinstance(form, dict):
                        form = form[request.method]
                else:
                    form = form_klass(data=post)

                # Validate form
                if form.is_valid():
                    kwargs["form"] = form
                    return func(request, *args, **kwargs)
                else:
                    return invalid_form(form)
            else:
                return func(request, *args, **kwargs)

        return wrapper

    return post_form_decorator
