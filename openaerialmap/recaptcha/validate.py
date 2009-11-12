from recaptcha import captcha
from django.conf import settings

def verify_captcha(sender, comment, request, **kwargs):
	challenge_field = request.POST.get('recaptcha_challenge_field')
	response_field = request.POST.get('recaptcha_response_field')
	client = request.META['REMOTE_ADDR']
	
	check_captcha = captcha.submit(challenge_field, response_field,
		settings.RECAPTCHA_PRIVATE_KEY, client)
		
	if check_captcha.is_valid is False:
		return False
		
	return True