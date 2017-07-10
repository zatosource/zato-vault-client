# -*- coding: utf-8 -*-

"""
Copyright (C) 2017, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from logging import getLogger

# Vault
from hvac import Client as _Client

# ################################################################################################################################

logger = getLogger(__name__)

# ################################################################################################################################

class NameId(object):
    """ Wraps both an attribute's name and its ID.
    """
    def __init__(self, name, id):
        self.name = name
        self.id = id

# ################################################################################################################################

class VAULT:
    class DEFAULT:
        TIMEOUT = 10
        URL = 'http://localhost:8200'

    class HEADERS:
        TOKEN_VAULT = 'HTTP_X_ZATO_VAULT_TOKEN'
        TOKEN_GH = 'HTTP_X_ZATO_VAULT_TOKEN_GITHUB'
        USERNAME = 'HTTP_X_ZATO_VAULT_USERNAME'
        PASSWORD = 'HTTP_X_ZATO_VAULT_PASSWORD'
        MOUNT_POINT = 'HTTP_X_ZATO_VAULT_MOUNT_POINT'
        TOKEN_RESPONSE = 'X-Zato-Vault-Token'
        TOKEN_RESPONSE_LEASE = 'X-Zato-Vault-Token-Lease-Duration'

    class AUTH_METHOD:
        GITHUB = NameId('GitHub', 'github')
        TOKEN = NameId('Token', 'token')
        USERNAME_PASSWORD = NameId('Username/password', 'username-password')

        class __metaclass__(type):
            def __iter__(self):
                return iter((self.GITHUB, self.TOKEN, self.USERNAME_PASSWORD))

VAULT.METHOD_HEADER = {
    VAULT.AUTH_METHOD.GITHUB.id: VAULT.HEADERS.TOKEN_GH,
    VAULT.AUTH_METHOD.TOKEN.id: VAULT.HEADERS.TOKEN_VAULT,
    VAULT.AUTH_METHOD.USERNAME_PASSWORD.id: (VAULT.HEADERS.USERNAME, VAULT.HEADERS.PASSWORD, VAULT.HEADERS.MOUNT_POINT),
}

VAULT.WEB_SOCKET = {
    'github': {'secret': VAULT.HEADERS.TOKEN_GH},
    'token': {'secret': VAULT.HEADERS.TOKEN_VAULT},
    'username-password': {
        'username': VAULT.HEADERS.USERNAME,
        'secret': VAULT.HEADERS.PASSWORD,
    }
}

# ################################################################################################################################

class VaultResponse(object):
    """ A convenience class to hold individual attributes of responses from Vault.
    """
    __slots__ = ('action', 'client_token', 'lease_duration', 'accessor', 'policies')

    def __init__(self, action=None, client_token=None, lease_duration=None, accessor=None, policies=None):
        self.action = action
        self.client_token = client_token
        self.lease_duration = lease_duration
        self.accessor = accessor
        self.policies = policies

    def __str__(self):
        attrs = []
        for elem in sorted(self.__slots__):
            value = getattr(self, elem)
            attrs.append('{}:{}'.format(elem, value))

        return '<{} at {}, {}>'.format(self.__class__.__name__, hex(id(self)), ', '.join(attrs))

    @staticmethod
    def from_vault(action, response, main_key='auth', token_key='client_token', has_lease_duration=True):
        """ Builds a VaultResponse out of a dictionary returned from Vault.
        """
        auth = response[main_key]

        vr = VaultResponse(action)
        vr.client_token = auth[token_key]
        vr.accessor = auth['accessor']
        vr.policies = auth['policies']

        if has_lease_duration:
            vr.lease_duration = auth['lease_duration']

        return vr

# ################################################################################################################################

class Client(_Client):
    """ A thin wrapper around hvac.Client providing connectivity to Vault.
    """
    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self._auth_func = {
            VAULT.AUTH_METHOD.TOKEN.id: self._auth_token,
            VAULT.AUTH_METHOD.USERNAME_PASSWORD.id: self._auth_username_password,
            VAULT.AUTH_METHOD.GITHUB.id: self._auth_github,
        }

    def __str__(self):
        return '<{} at {}, {}>'.format(self.__class__.__name__, hex(id(self)), self._url)

    __repr__ = __str__

    def ping(self):
        return self.is_sealed()

    def _auth_token(self, client_token, _from_vault=VaultResponse.from_vault):
        if not client_token:
            raise ValueError('Client token missing on input')

        response = self.lookup_token(client_token)
        return _from_vault('auth_token', response, 'data', 'id', False)

    def _auth_username_password(self, username, password, _from_vault=VaultResponse.from_vault):
        return _from_vault('auth_userpass', self.auth_userpass(username, password, use_token=False))

    def _auth_github(self, gh_token, _from_vault=VaultResponse.from_vault):
        return _from_vault('auth_github', self.auth_github(gh_token, use_token=False))

    def renew(self, client_token, _from_vault=VaultResponse.from_vault):
        return _from_vault('renew', self.renew_token(client_token))

    def authenticate(self, auth_method, *credentials):
        return self._auth_func[auth_method](*credentials)

# ################################################################################################################################
