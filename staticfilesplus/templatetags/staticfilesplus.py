from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()


class StaticFileNotFound(Exception):
    pass


@register.simple_tag
def static(path):
    if settings.DEBUG:
        # Any errors in the processing pipeline will get raised here
        found = finders.find(path)
        if not found:
            raise StaticFileNotFound(path)
    return staticfiles_storage.url(path)
