from django.test import TestCase, RequestFactory


class TestAPI(TestCase):
    def test_exception(self):
        from djsonapi import api

        response = api.exception(Exception(), log_error=False)
        self.assertEqual(response.status_code, 500)

        response = api.exception(Exception(), debug=True, log_error=False)
        self.assertEqual(response.status_code, 500)


    def test_catch500(self):
        from djsonapi import api
        from djsonapi import serial

        @api.catch500(log_error=False)
        def raise_exc(request):
            raise Exception("Failure")

        factory = RequestFactory()
        request = factory.get("/")

        response = raise_exc(request)

        self.assertEqual(response.status_code, 500)

        json = serial.loads(response.content)
        self.assertFalse(json["ok"])

    def test_required_method_put(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method("PUT", debug=True)
        def view(request, put=None):
            self.assertIsNotNone(put)
            return api.ok(put=put)

        ## test put

        data = {"test": 123}
        json = serial.dumps(data)

        factory = RequestFactory()
        request = factory.put("/", content_type="application/json", data=json)
        response = view(request)
        response_data = serial.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, response_data["body"]["put"])

        ## test debug

        factory = RequestFactory()
        request = factory.put("/", content_type="application/json", data="FAILJSON")
        response = view(request)
        response_data = serial.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response_data["ok"])
        self.assertIsNotNone(response_data["body"]["exception"])


    def test_form_valid(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class SomeForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method("GET", "POST", "PUT")
        @api.post_form(SomeForm)
        def view(request, form=None):
            return api.ok(form=form.cleaned_data if form  else None, method=request.method)

        ## Valid

        data = {"field": 123}
        json = serial.dumps(data)

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data=json)
        response = view(request)
        response_data = serial.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["body"]["method"], "POST")
        self.assertEqual(response_data["body"]["form"]["field"], data["field"])

        ## Invalid

        data = {"xxx": 123}
        json = serial.dumps(data)

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data=json)
        response = view(request)
        response_data = serial.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response_data["body"]["errors"]["field"])

    def test_error404(self):
        from djsonapi import api
        from djsonapi import serial

        response = api.error404(user=123)
        self.assertEqual(response.status_code, 404)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], False)
        self.assertEqual(response_data["message"], "Not Found")
        self.assertEqual(response_data["body"]["user"], 123)

    def test_error405(self):
        from djsonapi import api
        from djsonapi import serial

        response = api.error405(user=123)
        self.assertEqual(response.status_code, 405)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], False)
        self.assertEqual(response_data["message"], "Method Not Supported")
        self.assertEqual(response_data["body"]["user"], 123)


    def test_login_required_fail(self):
        from djsonapi import api
        from djsonapi import serial

        class AnonUser:
            def is_authenticated(self):
                return False

        @api.login_required()
        def view(request):
            pass

        factory = RequestFactory()
        request = factory.get("/", content_type="application/json")
        request.user = AnonUser()
        response = view(request)
        self.assertEqual(response.status_code, 401)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data["ok"], False)
        self.assertEqual(response_data["message"], "Unauthorized")
        self.assertEqual(response_data.get("body", not_found), not_found)


    def test_login_required_fail_url(self):
        from djsonapi import api
        from djsonapi import serial

        class AnonUser:
            def is_authenticated(self):
                return False

        @api.login_required(login_url="/abc123/")
        def view(request):
            pass

        factory = RequestFactory()
        request = factory.get("/", content_type="application/json")
        request.user = AnonUser()
        response = view(request)
        self.assertEqual(response.status_code, 401)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], False)
        self.assertEqual(response_data["message"], "Unauthorized")
        self.assertEqual(response_data["body"]["login_url"], "/abc123/")


    def test_login_required_ok(self):
        from djsonapi import api
        from djsonapi import serial

        class User:
            def is_authenticated(self):
                return True

        @api.login_required()
        def view(request):
            return api.ok(user=123)

        factory = RequestFactory()
        request = factory.get("/", content_type="application/json")
        request.user = User()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data["ok"], True)
        self.assertEqual(response_data.get("message", not_found), not_found)
        self.assertEqual(response_data["body"]["user"], 123)

    def test_required_methods_post_invalid_json(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method("POST")
        def view(request, post=None):
            pass

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data="garbage23*(%*@")
        response = view(request)
        self.assertEqual(response.status_code, 400)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data["ok"], False)
        self.assertEqual(response_data.get("message", not_found), "Invalid JSON POST")
        self.assertEqual(response_data.get("body", not_found), not_found)

    def test_required_methods_post_no_data(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method("POST")
        def view(request, post=None):
            return api.ok(post=post)

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data="")
        response = view(request)
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data["ok"], True)
        self.assertEqual(response_data.get("message", not_found), not_found)
        self.assertEqual(response_data["body"]["post"], {})

    def test_required_methods_post_to_get(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method("GET")
        def view(request, post=None):
            return api.ok(post=post)

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data="")
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 405)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], False)
        self.assertEqual(response_data["message"], "Method Not Supported")
        self.assertEqual(response_data.get("body", not_found), not_found)

    def test_required_methods_get(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method("GET")
        def view(request, post=None):
            return api.ok(post=post)

        factory = RequestFactory()
        request = factory.get("/", content_type="application/json", data="")
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], True)
        self.assertEqual(response_data.get("message", not_found), not_found)
        self.assertEqual(response_data["body"]["post"], None)


    def test_post_form_lambda(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class TestForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method("POST")
        @api.post_form(lambda request, data: TestForm(data=data))
        def view(request, form=None):
            return api.ok(data=form.cleaned_data)

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data=serial.dumps({"field": 123}))
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], True)
        self.assertEqual(response_data.get("message", not_found), not_found)
        self.assertEqual(response_data["body"]["data"]["field"], 123)


    def test_post_form_lambda_dict(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class TestForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method("POST")
        @api.post_form(lambda request, data: {"POST": TestForm(data=data)})
        def view(request, form=None):
            return api.ok(data=form.cleaned_data)

        factory = RequestFactory()
        request = factory.post("/", content_type="application/json", data=serial.dumps({"field": 123}))
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], True)
        self.assertEqual(response_data.get("message", not_found), not_found)
        self.assertEqual(response_data["body"]["data"]["field"], 123)


    def test_post_form_get(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class TestForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method("GET", "POST")
        @api.post_form(lambda request, data: TestForm(data=data))
        def view(request, form=None):
            return api.ok(data=form.cleaned_data if form else None)

        factory = RequestFactory()
        request = factory.get("/", content_type="application/json")
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data["ok"], True)
        self.assertEqual(response_data.get("message", not_found), not_found)
        self.assertEqual(response_data["body"]["data"], None)


class TestSerialization(TestCase):
    def test_datetimeserializes(self):
        from datetime import datetime
        from djsonapi import serial

        json = serial.dumps({"datetime": datetime.now()})
        self.assertIsInstance(json, (unicode, str))

    def test_dateserializes(self):
        from datetime import date
        from djsonapi import serial

        json = serial.dumps({"datetime": date.today()})
        self.assertIsInstance(json, (unicode, str))

    def test_nowserializes(self):
        from django.utils import timezone
        from djsonapi import serial

        json = serial.dumps({"datetime": timezone.now()})
        self.assertIsInstance(json, (unicode, str))

    def test_serialize_model(self):
        from example.testapp.models import Report
        from djsonapi import serial

        m = Report(title="YES", message="It Worked!", status=1)
        m.save()
        not_found = object()

        d = serial.serialize_model(m, debug_fields=False)
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get("title", not_found), "YES")
        self.assertEqual(d.get("message", not_found), "It Worked!")
        self.assertEqual(d.get("status", not_found), 1)
        self.assertEqual(d.get("_debug_pk", not_found), not_found)
        self.assertEqual(d.get("_debug_model", not_found), not_found)

        d = serial.serialize_model(m, ("message",), debug_fields=False)
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get("title", not_found), not_found)
        self.assertEqual(d.get("message", not_found), "It Worked!")
        self.assertEqual(d.get("status", not_found), not_found)
        self.assertEqual(d.get("_debug_pk", not_found), not_found)
        self.assertEqual(d.get("_debug_model", not_found), not_found)

        d = serial.serialize_model(m, ("message",), debug_fields=True)
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get("title", not_found), not_found)
        self.assertEqual(d.get("message", not_found), "It Worked!")
        self.assertEqual(d.get("status", not_found), not_found)
        self.assertEqual(d.get("_debug_pk", not_found), m.pk)
        self.assertEqual(d.get("_debug_model", not_found), "testapp.Report")

    def test_dump(self):
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        from djsonapi import serial

        io = StringIO()

        data = {"test": "test"}
        serial.dump(data, io)
        io_out = io.getvalue()
        reg_out = serial.dumps(data)

        self.assertEqual(io_out, reg_out)

    def test_serializer(self):
        from djsonapi import serial

        class Foop(object):
            flim = "flam"

            def __init__(self):
                self.flop = "flap"

            def foof(self):
                return "foop!"

        @serial.serializer(Foop)
        def serialize_foop(obj, **kwargs):
            return serial.serialize_fields(obj, ("flim", "flop", "foof"))

        data = serial.serialize(Foop())

        self.assertEqual(data["flim"], "flam")
        self.assertEqual(data["flop"], "flap")
        self.assertEqual(data["foof"], "foop!")

    def test_serializer_no_class(self):
        from djsonapi import serial

        class Foop(object):
            flim = "flam"

            def __init__(self):
                self.flop = "flap"

            def foof(self):
                return "foop!"

        self.assertRaises(serial.NoSerializerFound, serial.serialize, Foop())

    def test_serializer_no_mode(self):
        from djsonapi import serial

        class Foop(object):
            flim = "flam"

            def __init__(self):
                self.flop = "flap"

            def foof(self):
                return "foop!"

        @serial.serializer(Foop)
        def serialize_foop(obj, **kwargs):
            return serial.serialize_fields(obj, ("flim", "flop", "foof"))

        self.assertRaises(serial.NoSerializerFound, serial.serialize, Foop(), mode="fiippy")

    def test_serializer_list(self):
        from djsonapi import serial

        class Foop(object):
            flim = "flam"

            def __init__(self):
                self.flop = "flap"

            def foof(self):
                return "foop!"

        @serial.serializer(Foop)
        def serialize_foop(obj, **kwargs):
            return serial.serialize_fields(obj, ("flim", "flop", "foof"))

        data_items = serial.serialize([Foop() for x in xrange(10)])
        self.assertEqual(len(data_items), 10)
        for data in data_items:
            self.assertEqual(data["flim"], "flam")
            self.assertEqual(data["flop"], "flap")
            self.assertEqual(data["foof"], "foop!")

    def test_serializer_list_multi_obj(self):
        from djsonapi import serial

        class A(object):
            a = 'a'

        class B(object):
            b = 'b'

        @serial.serializer(A)
        def serialize_A(a, **kwargs):
            return serial.serialize_fields(a, ("a",))

        @serial.serializer(B)
        def serialize_B(b, **kwargs):
            return serial.serialize_fields(b, ("b",))

        data_items = serial.serialize([(A if x % 2 == 0 else B)() for x in xrange(10)])
        self.assertEqual(len(data_items), 10)
        for index, data in enumerate(data_items):
            if index % 2 == 0:
                self.assertEqual(data['a'], 'a')
            else:
                self.assertEqual(data['b'], 'b')

    def test_serializer_gen(self):
        from djsonapi import serial

        class Foop(object):
            flim = "flam"

            def __init__(self):
                self.flop = "flap"

            def foof(self):
                return "foop!"

        @serial.serializer(Foop)
        def serialize_foop(obj, **kwargs):
            return serial.serialize_fields(obj, ("flim", "flop", "foof"))

        data_items = serial.iserialize([Foop() for x in xrange(10)])
        self.assertTrue(callable(data_items.next))
        for data in data_items:
            self.assertEqual(data["flim"], "flam")
            self.assertEqual(data["flop"], "flap")
            self.assertEqual(data["foof"], "foop!")

    def test_serializer_gets_kwargs(self):
        from djsonapi import serial

        class Foop(object):
            flim = "flam"

            def __init__(self):
                self.flop = "flap"

            def foof(self):
                return "foop!"

        @serial.serializer(Foop)
        def serialize_foop(obj, **kwargs):
            data = serial.serialize_fields(obj, ("flim", "flop", "foof"))
            kwargs.update(data)
            return kwargs

        data = serial.serialize(Foop(), whiz="bang", bang="boom")

        self.assertEqual(data["flim"], "flam")
        self.assertEqual(data["flop"], "flap")
        self.assertEqual(data["foof"], "foop!")
        self.assertEqual(data["whiz"], "bang")
        self.assertEqual(data["bang"], "boom")






