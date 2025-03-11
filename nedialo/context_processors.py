from core.models import Team, ServerSetting, WorkStatus, Campaign, Profile, Role
from django.utils import timezone as tz

def global_context_processor(request):
    # Initialize default context values
    settings = None
    teams = None
    work_status = None
    callers_campaigns = None
    sales_campaigns = None
    role_permissions = None
    current_year = tz.now().year
    current_month = tz.now().month
    current_day = tz.now().day
    settings = ServerSetting.objects.first()

    # Check if user is authenticated
    if request.user.is_authenticated:
        user = request.user
        today = (tz.localtime(tz.now())).date()

        # Fetch settings, teams, and other data only for authenticated users
        callers_list = ['callers', 'sales']
        teams = Team.objects.filter(team_type__in=callers_list)

        try:
            work_status = WorkStatus.objects.get(user=user, date=today)
        except WorkStatus.DoesNotExist:
            work_status = None

        callers_campaigns = Campaign.objects.filter(campaign_type="calling")
        sales_campaigns = Campaign.objects.filter(campaign_type="sales")

        # Retrieve profile and role permissions for the authenticated user
        try:
            profile = Profile.objects.get(user=user)
            user_role = profile.role
            try:
                role_permissions = Role.objects.get(role_name=user_role)
            except Role.DoesNotExist:
                role_permissions = None
        except Profile.DoesNotExist:
            profile = None
            user_role = None
            role_permissions = None

    # Return the context, even if the user is not authenticated
    context = {
        'callers_teams': teams,
        'settings': settings,
        "work_status": work_status,
        'callers_campaigns': callers_campaigns,
        'sales_campaigns': sales_campaigns,
        'current_year': current_year,
        'current_month': current_month,
        'current_day': current_day,
        'perms': role_permissions,
    }

    return context
