from django.utils.deprecation import MiddlewareMixin
# from django.utils import translation
# from django.conf import settings


class LangMiddleware(MiddlewareMixin):
    pass
    # def process_request(self, request):
    #     lang = request.headers.get('Accept-Language', 'en')
    #     # if lang:
    #     #     lang_code = lang.split(',')[0].replace('_', '-')
    #     #     print(lang_code, dict(settings.LANGUAGES).keys())
    #     #     if lang_code in dict(settings.LANGUAGES).keys():
    #     #         print("HEREE")
    #     #         translation.activate(lang_code)
    #     #         request.LANGUAGE_CODE = lang_code
    #     #     else:
    #     #         translation.activate(settings.LANGUAGE_CODE)
    #     #         request.LANGUAGE_CODE = settings.LANGUAGE_CODE
    #     # else:
    #     #     translation.activate(settings.LANGUAGE_CODE)
    #     #     request.LANGUAGE_CODE = settings.LANGUAGE_CODE

    # def process_response(self, request, response):
    #     translation.deactivate()
    #     return response
