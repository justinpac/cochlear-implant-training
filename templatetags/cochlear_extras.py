# custon django template tags
# https://docs.djangoproject.com/en/1.8/howto/custom-template-tags/

from django import template

register = template.Library()

# Get an object at a certain index of a query set or array
@register.simple_tag
def get_obj_at_index(qset,*args):
	try:
		temp = qset
		for arg in args:
			temp = temp[int(arg)]
		return temp
	except:
		return "none"