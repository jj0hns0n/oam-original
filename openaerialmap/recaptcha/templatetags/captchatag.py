from django import template
from django.conf import settings
from openaerialmap.recaptcha import captcha

register = template.Library()

@register.simple_tag
def recaptcha_html():
	return captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY)
