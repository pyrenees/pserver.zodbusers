from datetime import datetime
from datetime import timedelta
from plone.server import app_settings
from plone.server import configure
from plone.server.api.service import Service
from plone.server.auth.validators import SaltedHashPasswordValidator
from plone.server.browser import UnauthorizedResponse
from plone.server.interfaces import ISite
from plone.server.utils import get_authenticated_user

import jwt


@configure.service(
    context=ISite,
    name="@login",
    method="POST",
    permission="plone.NotAuthenticated")
class Login(Service):
    token_timeout = 60 * 60 * 1

    async def __call__(self):
        data = await self.request.json()
        creds = {
            'token': data['password'],
            'id': data['username']
        }
        validator = SaltedHashPasswordValidator(self.request)
        user = await validator.validate(creds)
        if user is None:
            return UnauthorizedResponse('login failed')

        data = {
            'exp': datetime.utcnow() + timedelta(seconds=self.token_timeout),
            'id': user.id
        }
        jwt_token = jwt.encode(data, app_settings['jwt']['secret']).decode('utf-8')

        return {
            'exp': data['exp'],
            'token': jwt_token
        }


@configure.service(
    context=ISite,
    name="@refresh_token",
    method="POST",
    permission="plone.Authenticated")
class Refresh(Login):
    async def __call__(self):
        user = get_authenticated_user(self.request)
        if user is None:
            return UnauthorizedResponse('user not authorized')

        data = {
            'exp': datetime.utcnow() + timedelta(seconds=self.token_timeout),
            'id': user.id
        }
        jwt_token = jwt.encode(data, app_settings['jwt']['secret']).decode('utf-8')
        return {
            'exp': data['exp'],
            'token': jwt_token
        }
