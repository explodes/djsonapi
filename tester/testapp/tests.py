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
            raise Exception('Failure')

        factory = RequestFactory()
        request = factory.get('/')

        response = raise_exc(request)

        self.assertEqual(response.status_code, 500)

        json = serial.loads(response.content)
        self.assertFalse(json['ok'])

    def test_required_method_put(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method('PUT', debug=True)
        def view(request, put=None):
            self.assertIsNotNone(put)
            return api.ok(put=put)

        ## test put

        data = {'test': 123}
        json = serial.dumps(data)

        factory = RequestFactory()
        request = factory.put('/', content_type='application/json', data=json)
        response = view(request)
        response_data = serial.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, response_data['body']['put'])

        ## test debug

        factory = RequestFactory()
        request = factory.put('/', content_type='application/json', data="FAILJSON")
        response = view(request)
        response_data = serial.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response_data['ok'])
        self.assertIsNotNone(response_data['body']['exception'])


    def test_form_valid(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class SomeForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method('GET', 'POST', 'PUT')
        @api.post_form(SomeForm)
        def view(request, form=None):
            return api.ok(form=form.cleaned_data if form  else None, method=request.method)

        ## Valid

        data = {'field': 123}
        json = serial.dumps(data)

        factory = RequestFactory()
        request = factory.post('/', content_type='application/json', data=json)
        response = view(request)
        response_data = serial.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['body']['method'], 'POST')
        self.assertEqual(response_data['body']['form']['field'], data['field'])

        ## Invalid

        data = {'xxx': 123}
        json = serial.dumps(data)

        factory = RequestFactory()
        request = factory.post('/', content_type='application/json', data=json)
        response = view(request)
        response_data = serial.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response_data['body']['errors']['field'])

    def test_error404(self):
        from djsonapi import api
        from djsonapi import serial

        response = api.error404(user=123)
        self.assertEqual(response.status_code, 404)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], False)
        self.assertEqual(response_data['message'], "Not Found")
        self.assertEqual(response_data['body']['user'], 123)

    def test_error405(self):
        from djsonapi import api
        from djsonapi import serial

        response = api.error405(user=123)
        self.assertEqual(response.status_code, 405)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], False)
        self.assertEqual(response_data['message'], "Method Not Supported")
        self.assertEqual(response_data['body']['user'], 123)


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
        request = factory.get('/', content_type='application/json')
        request.user = AnonUser()
        response = view(request)
        self.assertEqual(response.status_code, 401)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data['ok'], False)
        self.assertEqual(response_data['message'], "Unauthorized")
        self.assertEqual(response_data.get('body', not_found), not_found)


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
        request = factory.get('/', content_type='application/json')
        request.user = AnonUser()
        response = view(request)
        self.assertEqual(response.status_code, 401)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], False)
        self.assertEqual(response_data['message'], "Unauthorized")
        self.assertEqual(response_data['body']['login_url'], "/abc123/")


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
        request = factory.get('/', content_type='application/json')
        request.user = User()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data['ok'], True)
        self.assertEqual(response_data.get('message', not_found), not_found)
        self.assertEqual(response_data['body']['user'], 123)

    def test_required_methods_post_invalid_json(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method('POST')
        def view(request, post=None):
            pass

        factory = RequestFactory()
        request = factory.post('/', content_type='application/json', data='garbage23*(%*@')
        response = view(request)
        self.assertEqual(response.status_code, 400)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data['ok'], False)
        self.assertEqual(response_data.get('message', not_found), "Invalid JSON POST")
        self.assertEqual(response_data.get('body', not_found), not_found)

    def test_required_methods_post_no_data(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method('POST')
        def view(request, post=None):
            return api.ok(post=post)

        factory = RequestFactory()
        request = factory.post('/', content_type='application/json', data='')
        response = view(request)
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        not_found = object()
        self.assertEqual(response_data['ok'], True)
        self.assertEqual(response_data.get('message', not_found), not_found)
        self.assertEqual(response_data['body']['post'], {})

    def test_required_methods_post_to_get(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method('GET')
        def view(request, post=None):
            return api.ok(post=post)

        factory = RequestFactory()
        request = factory.post('/', content_type='application/json', data='')
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 405)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], False)
        self.assertEqual(response_data['message'], "Method Not Supported")
        self.assertEqual(response_data.get('body', not_found), not_found)

    def test_required_methods_get(self):
        from djsonapi import api
        from djsonapi import serial

        @api.required_method('GET')
        def view(request, post=None):
            return api.ok(post=post)

        factory = RequestFactory()
        request = factory.get('/', content_type='application/json', data='')
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], True)
        self.assertEqual(response_data.get('message', not_found), not_found)
        self.assertEqual(response_data['body']['post'], None)


    def test_post_form_lambda(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class TestForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method('POST')
        @api.post_form(lambda request, data: TestForm(data=data))
        def view(request, form=None):
            return api.ok(data=form.cleaned_data)

        factory = RequestFactory()
        request = factory.post('/', content_type='application/json', data=serial.dumps({'field': 123}))
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], True)
        self.assertEqual(response_data.get('message', not_found), not_found)
        self.assertEqual(response_data['body']['data']['field'], 123)


    def test_post_form_get(self):
        from django import forms
        from djsonapi import api
        from djsonapi import serial

        class TestForm(forms.Form):
            field = forms.IntegerField()

        @api.required_method('GET', 'POST')
        @api.post_form(lambda request, data: TestForm(data=data))
        def view(request, form=None):
            return api.ok(data=form.cleaned_data if form else None)

        factory = RequestFactory()
        request = factory.get('/', content_type='application/json')
        response = view(request)
        not_found = object()
        self.assertEqual(response.status_code, 200)
        response_data = serial.loads(response.content)
        self.assertEqual(response_data['ok'], True)
        self.assertEqual(response_data.get('message', not_found), not_found)
        self.assertEqual(response_data['body']['data'], None)


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
        from tester.testapp.models import TestModel
        from djsonapi import serial

        m = TestModel()
        not_found = object()

        d = serial.serialize_model(m)
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get('field_1', not_found), None)
        self.assertEqual(d.get('field_2', not_found), "blankity")
        self.assertEqual(d.get('field_3', not_found), 7)
        self.assertEqual(d.get('_debug_pk', not_found), not_found)
        self.assertEqual(d.get('_debug_model', not_found), not_found)

        d = serial.serialize_model(m, ('field_2',))
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get('field_1', not_found), not_found)
        self.assertEqual(d.get('field_2', not_found), "blankity")
        self.assertEqual(d.get('field_3', not_found), not_found)
        self.assertEqual(d.get('_debug_pk', not_found), not_found)
        self.assertEqual(d.get('_debug_model', not_found), not_found)

        d = serial.serialize_model(m, ('field_2',), debug_fields=True)
        self.assertIsInstance(d, dict)
        self.assertEqual(d.get('field_1', not_found), not_found)
        self.assertEqual(d.get('field_2', not_found), "blankity")
        self.assertEqual(d.get('field_3', not_found), not_found)
        self.assertEqual(d.get('_debug_pk', not_found), None)
        self.assertEqual(d.get('_debug_model', not_found), "testapp.TestModel")