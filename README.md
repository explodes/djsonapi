##### v0.9.9

Django JSON API Made Simple
===========================

No more forcing your JSON to be bound to models.

This is a JSON api framework, the way it should be.

- Simple
- Flexible / Dynamic
- Useful

The API framework uses Django Forms, so no more bull trying to validate input a certain way.

# !!! Get to the code !!!

How about this?


```language=python
from djsonapi import api, serial

@serial.serializer(User, mode="current_user")
def current_user_serializer(obj):
    return serial.serialize_model(obj, fields=("name", "email", "last_login", "date_joined"))
    
@serial.serializer(User, mode="public")
def public_user_serializer(obj):
    return serial.serialize_model(obj, fields=("name", "date_joined"))

@csrf_exempt
@api.login_required
@api.require_method("GET", "POST") # passes post/put down, 405's if method is incorrect
@api.post_form(forms.UserUpdateForm) # validates post/put data with form
def profile(request, form):
    if form:
        user = form.save()
    else:
        user = request.user
    data = serial.serialize(user, mode="current_user")
    return api.ok(message="Hello World!", user=user)
```
The response could look like:
```
{
  "message": "Hello World!",
  "body": {
    "name": "Evan Leis",
    "last_login": "2014-04-09T22:48:21.957Z",
    "date_joined": "2014-04-09T22:47:08.153Z",
    "email": "foo@example.com",
  },
  "ok": true
}
```

##### TODO: Better documentation for y'all


## `djsonapi.serial`

Methods for serializing objects into dicts, and dicts into JSON.

## `djsonapi.api`

Methods for returning HttpResponses with JSON data.

License
----
The MIT License (MIT)

Copyright (c) 2014 Evan Leis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
    
