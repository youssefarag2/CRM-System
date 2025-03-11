from django import template
from django.utils import timezone as tz
from django.db.models import Sum
from core.models import WorkStatus, ServerSetting
from datetime import timedelta


register = template.Library()

@register.filter
def total_time_for_status(user, status):
    now = tz.now()
    start_of_month = now.replace(day=1)

    # Filter WorkStatus records for the current month and specific user
    work_statuses = WorkStatus.objects.filter(date__gte=start_of_month, user=user)

    # Define a dictionary to map status names to field names
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    # Get the corresponding field name for the given status
    field_name = status_field_mapping.get(status)

    if not field_name:
        return "00:00:00"  # If the status is not valid, return 0

    # Aggregate total time for the specified status
    total_time = work_statuses.aggregate(total_time=Sum(field_name))

    # Convert the timedelta object to total seconds
    total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0

    # Convert total seconds to hours, minutes, and seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    # Format the time as HH:MM:SS
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time




@register.filter
def total_worked_time(user):
    now = tz.now()
    start_of_month = now.replace(day=1)

    # Filter WorkStatus records for the current month and specific user
    work_statuses = WorkStatus.objects.filter(date__gte=start_of_month, user=user)

    # Aggregate total time for each status
    totals = work_statuses.aggregate(
        total_ready_time=Sum('ready_time'),
        total_meeting_time=Sum('meeting_time'),
        total_break_time=Sum('break_time'),
    )

    # Sum up all statuses to get the total worked time in seconds
    total_seconds = sum([
        (totals['total_ready_time'] or timedelta()).total_seconds(),
        (totals['total_meeting_time'] or timedelta()).total_seconds(),
        (totals['total_break_time'] or timedelta()).total_seconds(),
    ])

    # Convert total seconds to hours, minutes, and seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    # Format the time as HH:MM:SS
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time



@register.filter
def total_payable_time(user):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    now = tz.now()
    start_of_month = now.replace(day=1)

    # Filter WorkStatus records for the current month and specific user
    work_statuses = WorkStatus.objects.filter(date__gte=start_of_month, user=user)

    # Aggregate total time for each status
    totals = work_statuses.aggregate(
        total_ready_time=Sum('ready_time'),
        total_meeting_time=Sum('meeting_time'),
        total_break_time=Sum('break_time')
    )

    # Convert total times to seconds
    ready_time_seconds = (totals['total_ready_time'] or timedelta()).total_seconds()
    meeting_time_seconds = (totals['total_meeting_time'] or timedelta()).total_seconds()
    break_time_seconds = (totals['total_break_time'] or timedelta()).total_seconds()

    # Calculate total payable time
    break_paid = settings.break_paid  # Assuming 'BREAK_PAID' is a boolean in your settings
    total_hours_paid = ready_time_seconds + meeting_time_seconds + (break_time_seconds if break_paid else 0)

    # Convert total payable seconds to hours, minutes, and seconds
    hours = int(total_hours_paid // 3600)
    minutes = int((total_hours_paid % 3600) // 60)
    seconds = int(total_hours_paid % 60)

    # Format the time as HH:MM:SS
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time




@register.filter
def duration_to_hms(duration):
    """Converts a timedelta or duration to HH:MM:SS format."""
    if duration is None:
        return "00:00:00"
    
    # Handle timedelta object
    if isinstance(duration, timedelta):
        total_seconds = int(duration.total_seconds())
    else:
        # If duration is not a timedelta, assume it's already in seconds
        total_seconds = int(duration)

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"



@register.filter
def decimal_to_hms(decimal_hours):
    """Converts decimal hours to HH:MM:SS format."""
    if decimal_hours is None:
        return "00:00:00"
    
    try:
        # Calculate total seconds
        total_seconds = int(decimal_hours * 3600)
        
        # Convert to HH:MM:SS
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except (ValueError, TypeError):
        return "00:00:00"





@register.filter
def instance_total_worked_time(work_status_instance):
    # Aggregate total time for the provided WorkStatus instance
    totals = {
        'total_ready_time': work_status_instance.ready_time,
        'total_meeting_time': work_status_instance.meeting_time,
        'total_break_time': work_status_instance.break_time
    }

    # Sum up all statuses to get the total worked time in seconds
    total_seconds = sum([
        (totals['total_ready_time'] or timedelta()).total_seconds(),
        (totals['total_meeting_time'] or timedelta()).total_seconds(),
        (totals['total_break_time'] or timedelta()).total_seconds(),
    ])

    # Convert total seconds to hours, minutes, and seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    # Format the time as HH:MM:SS
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time

@register.filter
def instance_total_payable_time(work_status_instance):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None

    # Aggregate total time for the provided WorkStatus instance
    totals = {
        'total_ready_time': work_status_instance.ready_time,
        'total_meeting_time': work_status_instance.meeting_time,
        'total_break_time': work_status_instance.break_time
    }

    # Convert total times to seconds
    ready_time_seconds = (totals['total_ready_time'] or timedelta()).total_seconds()
    meeting_time_seconds = (totals['total_meeting_time'] or timedelta()).total_seconds()
    break_time_seconds = (totals['total_break_time'] or timedelta()).total_seconds()

    # Calculate total payable time
    break_paid = settings.break_paid if settings else False
    total_hours_paid = ready_time_seconds + meeting_time_seconds + (break_time_seconds if break_paid else 0)

    # Convert total payable seconds to hours, minutes, and seconds
    hours = int(total_hours_paid // 3600)
    minutes = int((total_hours_paid % 3600) // 60)
    seconds = int(total_hours_paid % 60)

    # Format the time as HH:MM:SS
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return formatted_time





@register.simple_tag
def get_current_status(profile):
    """
    Template tag to get the current status of a profile.
    """
    if profile:
        return profile.get_current_status()
    return 'offline'  # Default value if profile is not available



@register.filter
def format_integer(value):
    if isinstance(value, (int, float)):
        return "{:.1f}".format(value).rstrip('0').rstrip('.')
    return value



@register.filter
def format_abs_value(value):
    if isinstance(value, (int, float)):
        abs_value = abs(value)  # Get the absolute value
        return "{:.1f}".format(abs_value).rstrip('0').rstrip('.')  # Format to one decimal place
    return value


@register.filter
def multiply(value, multiplier):
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return value