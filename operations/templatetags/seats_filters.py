from django import template
from core.models import DialerCredentials,Profile, WorkStatus
from django.utils import timezone as tz

register = template.Library()

@register.filter
def format_float(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value



@register.filter
def count_services(queryset):
    return queryset.count()


@register.filter
def seats(campaign):

    seats = DialerCredentials.objects.filter(campaign=campaign, account_type="agent").count()

    return seats


@register.filter
def seats_available(campaign):

    seats_available_all = DialerCredentials.objects.filter(campaign=campaign, account_type="agent", agent_profile__isnull=True).count()

    return seats_available_all


@register.filter
def seats_used(campaign):

    seats_used_all = DialerCredentials.objects.filter(campaign=campaign, account_type="agent", agent_profile__isnull=False).count()

    return seats_used_all


@register.filter
def seats_accounts(campaign):
    seats = DialerCredentials.objects.filter(campaign=campaign, account_type="agent")

    return seats


@register.filter
def agent_status(agent_profile):
    today = (tz.localtime(tz.now())).date()
    user = agent_profile.user
    
    try:
        work_status = WorkStatus.objects.get(user=user, date=today)
    except WorkStatus.DoesNotExist:
        return False
    status =  work_status.current_status
    if status == "offline":
        return False
    else:
        return status

