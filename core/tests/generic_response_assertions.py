from django.urls import reverse

from core.fixtures import NO_PERMISSION, NOT_FOUND, NOT_AUTHENTICATED


def _msg_from_user(user):
    return user.profile_type


class ResponseAssertionsForUsers:
    def __init__(self, assert_response, users, msg_from_user=_msg_from_user):
        self._users = users
        self._assert_response = assert_response
        self._msg_from_user = msg_from_user

    def __getattr__(self, item):
        def call_for_every_user(*args, **kwargs):
            client = self._assert_response.test_case.client

            for user in self._users:
                client.force_login(user)
                getattr(self._assert_response, item)(
                    *args, **kwargs, msg=self._msg_from_user(user)
                )

        return call_for_every_user


class GenericResponseAssertionSet:
    def __init__(self, test_case):
        self.test_case = test_case

    def get_serializer_errors(self, serializer_class, data, request=None):
        serializer_kwargs = {'data': data}

        if request is not None:
            serializer_kwargs['context'] = {'request': request}

        serializer = serializer_class(**serializer_kwargs)
        serializer.is_valid()

        return serializer.errors

    def assert_response(self, response, expected_status, expected_data=None, msg=None):
        self.test_case.assertEqual(
            response.status_code, expected_status, msg=join_msg(response.content, msg)
        )
        if expected_data:
            self.test_case.assertEqual(
                response.json(), expected_data, msg=join_msg(response.status_code, msg)
            )

    def assert_view_response(
        self,
        expected_status,
        expected_data,
        method,
        view_name,
        pk=None,
        data=None,
        serializer_class=None,
        *args,
        params=None,
        format=None,
        lookup_url_kwarg='pk',
        msg=None,
    ):
        url_kwargs = {'viewname': view_name}
        if pk is not None:
            url_kwargs['kwargs'] = {lookup_url_kwarg: pk}

        path = reverse(**url_kwargs)

        if params:
            path = '{path}?{params}'.format(
                path=path,
                params='&'.join([f'{key}={value}' for key, value in params.items()]),
            )

        request_kwargs = {'path': path, 'format': format or 'json'}
        if data is not None:
            request_kwargs['data'] = data

        response = getattr(self.test_case.client, method)(**request_kwargs)

        if serializer_class is not None and expected_data is None:
            expected_data = self.get_serializer_errors(
                serializer_class, data, response.wsgi_request
            )

        self.assert_response(
            response=response,
            expected_status=expected_status,
            expected_data=expected_data,
            msg=msg,
        )
        return response

    def bad_request(
        self,
        method,
        view_name,
        pk=None,
        data=None,
        expected_data=None,
        serializer_class=None,
        *args,
        params=None,
        format=None,
        msg=None,
    ):
        return self.assert_view_response(
            400,
            expected_data,
            method,
            view_name,
            pk,
            data,
            serializer_class,
            format=format,
            params=params,
            msg=msg,
        )

    def no_permission(
        self,
        method,
        view_name,
        pk=None,
        data=None,
        *args,
        params=None,
        format=None,
        msg=None,
    ):
        return self.assert_view_response(
            403,
            NO_PERMISSION,
            method,
            view_name,
            pk,
            data,
            format=format,
            params=params,
            msg=msg,
        )

    def not_authenticated(
        self,
        method,
        view_name,
        pk=None,
        data=None,
        *args,
        format=None,
        params=None,
        msg=None,
    ):
        return self.assert_view_response(
            403,
            NOT_AUTHENTICATED,
            method,
            view_name,
            pk,
            data,
            format=format,
            params=params,
            msg=msg,
        )

    def not_found(
        self,
        method,
        view_name,
        pk=None,
        data=None,
        *args,
        format=None,
        params=None,
        lookup_url_kwarg='pk',
        msg=None,
    ):
        return self.assert_view_response(
            404,
            NOT_FOUND,
            method,
            view_name,
            pk,
            data,
            format=format,
            params=params,
            lookup_url_kwarg=lookup_url_kwarg,
            msg=msg,
        )

    def created(
        self,
        method,
        view_name,
        pk=None,
        data=None,
        expected_data=None,
        *args,
        format=None,
        params=None,
        msg=None,
    ):
        return self.assert_view_response(
            201,
            expected_data,
            method,
            view_name,
            pk,
            data,
            format=format,
            params=params,
            msg=msg,
        )

    def ok(
        self,
        method,
        view_name,
        pk=None,
        data=None,
        expected_data=None,
        *args,
        format=None,
        params=None,
        msg=None,
    ):
        return self.assert_view_response(
            200,
            expected_data,
            method,
            view_name,
            pk,
            data,
            format=format,
            params=params,
            msg=msg,
        )

    def no_content(
        self, method, view_name, pk=None, data=None, *args, format=None, msg=None
    ):
        return self.assert_view_response(
            204, None, method, view_name, pk, data, format=format, msg=None,
        )

    def for_users(self, users):
        return ResponseAssertionsForUsers(self, users)


def join_msg(response_data, msg=None):
    if msg is None:
        return response_data
    return f'{msg}\n{response_data}'
