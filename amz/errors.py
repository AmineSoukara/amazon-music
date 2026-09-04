"""
Amazon-Music
~~~~~~~~~
A Python package for interacting with Amazon Music services.

:Copyright: (c) 2025 By Amine Soukara <https://github.com/AmineSoukara>.
:License: MIT, See LICENSE For More Details.
:Link: https://github.com/AmineSoukara/Amazon-Music
:Description: A comprehensive CLI tool and API wrapper for Amazon Music with download capabilities.
"""


class InvalidAccessToken(Exception):
    pass


class RateLimitExceeded(Exception):
    pass


class UserBanned(Exception):
    pass


class LoginError(Exception):
    pass


class ApiConnectionError(Exception):
    pass
