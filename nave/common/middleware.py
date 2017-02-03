import logging
import os

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.middleware.locale import LocaleMiddleware
from django.utils.functional import cached_property


logger = logging.getLogger(__name__)


class FallBackLanguageMiddleware(LocaleMiddleware):
    response_redirect_class = HttpResponseRedirect
    response_default_language_redirect_class = HttpResponsePermanentRedirect

    @property
    def default_lang(self):
        return settings.LANGUAGE_CODE \
                if hasattr(settings, 'LANGUAGE_CODE') else None

    @property
    def fallback_languages(self):
        return settings.LANGUAGE_CODE_FALLBACK \
                if hasattr(settings, 'LANGUAGE_CODE_FALLBACK') else None

    @property
    def fallback_to_default(self):
        return settings.LANGUAGE_DEFAULT_FALLBACK \
                if hasattr(settings, 'LANGUAGE_DEFAULT_FALLBACK') else None

    @cached_property
    def fall_back_dict(self):
        fall_backs = self.fallback_languages if self.fallback_languages else {}
        if self.fallback_to_default:
            for lang in self.fallback_to_default:
                fall_backs[lang] = self.default_lang
        return fall_backs

    def process_request(self, request):
        if self.fall_back_dict:
            request_path = request.path.strip('/').split('/')
            if len(request_path) > 0:
                possible_language = request_path[0]
                if possible_language in self.fall_back_dict:
                    redirect_language = self.fall_back_dict.get(
                        possible_language
                    )
                    if redirect_language is not None:
                        redirect_uri = "/{}/".format(
                            os.path.join(
                                redirect_language, *request_path[1:]
                            )
                        )
                        return HttpResponseRedirect(redirect_uri)
