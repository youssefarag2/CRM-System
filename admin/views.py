from django.shortcuts import render, redirect
from core.views import settings,validate_file
from core.models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.middleware.csrf import CsrfViewMiddleware
from nedialo.constants import countries, us_states, discovery_options
import json
from core.decorators import *
from datetime import datetime,timedelta
import calendar
from core.models import DIALERS
from collections import defaultdict
from django.utils.safestring import mark_safe
from django.template.defaultfilters import date as _date
from discord_app.views import get_ip_info
import pytz
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from discord_app.views import send_discord_message_contract
from urllib.parse import quote












@login_required
def admin_home(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    return render(request,'admin/admin-home.html',context)




@permission_required('admin_home')
@login_required
def applications_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['skills'] = dict(APPLICATION_SKILLS_CHOICES)
    context['applications'] = Application.objects.filter(active=True).order_by('-submission_date')
                                                  


    return render(request,'admin/applications.html',context)




@permission_required('admin_home')
@login_required
def application_stages(request, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['year'] = year

    apps = Application.objects.filter(active=True, submission_date__year=year).order_by('-submission_date')

    # Create a dictionary to hold lists of sales leads for each status choice
    apps_grouped = {choice[0]: [] for choice in APPLICATION_PANEL_CHOICES}  # Initialize with empty lists

    # Iterate over each sales lead and group by status
    for app in apps:
        apps_grouped[app.status].append(app)

    # Prepare the context with grouped sales leads
    context['applications'] = apps_grouped

    # Include the names of the statuses in your context as well
    context['app_choices'] = dict(APPLICATION_PANEL_CHOICES)



   

    return render(request, 'applications/application_stages.html', context)





@permission_required('admin_applications')
@login_required
def application_report(request, app_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['app_status'] = APPLICATION_PANEL_CHOICES
    context['discovery_options'] = APPLICATION_DISCOVERY
    context['skills'] = APPLICATION_SKILLS_CHOICES
    context['lang_exp'] = APPLICATION_LANG_CHOICES
    context['app'] = Application.objects.get(id=app_id)


    server_settings = ServerSetting.objects.first()
    whatsapp_temp = server_settings.whatsapp_template

    
     # Fetch application details
    app = Application.objects.get(id=app_id)
    
    dynamic_data = {
        'name': app.full_name,
        'position': app.get_position_display(),
        'date': app.submission_date.strftime('%Y-%m-%d'),
    }

    template = whatsapp_temp
    for var, value in dynamic_data.items():
        template = template.replace(f'$${var}$$', str(value))

    # URL encode the template message to preserve spaces, line breaks, etc.
    encoded_message = quote(template)

    phone_number = app.phone
    whatsapp_link = f"https://wa.me/{phone_number}?text={encoded_message}"

    # Add the WhatsApp link to the context
    context['whatsapp_link'] = whatsapp_link


    if request.method == "POST":
        data = request.POST

        status = data.get('status')
 
        
        app = Application.objects.get(id=app_id)

        
        app.status=status
        app.handled_by=request.user
        app.language_exp = data.get('language_exp')
        app.skills = request.POST.getlist('skills')
        app.comments = data.get('comments')
        app.save()
        
            
        

        return redirect('/admin')
    return render(request,'admin/application_report.html', context)



@permission_required('admin_campaigns')
@login_required
def campaigns_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['campaigns'] = Campaign.objects.filter(active=True)


    return render(request,'admin/campaigns/campaigns.html',context)



@permission_required('admin_campaigns')
@login_required
def campaign_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)

    client_role = Role.objects.get(role_name="Client")

    context['profile'] = profile
    context['clients'] = ClientProfile.objects.filter(role=client_role, active=True)
    context['countries'] = countries
    context['sources'] = DataSource.objects.filter(active=True, data_source=True)
    context['campaign_types'] = SERVICE_TYPES
    context['dialers'] = Dialer.objects.filter(active=True)



    if request.method == "POST":
        data = request.POST
        campaign_name = data.get('campaign_name')
        client = data.get('client')
        agents_count = data.get('agents_count')
        agents_rate = data.get('hourly_rate')
        weekly_hours = data.get('weekly_hours')
        weekly_leads = data.get('weekly_leads')
        lead_points = data.get('lead_points')
        campaign_type = data.get('campaign_type')
        campaign_dialer = data.get('campaign_dialer')
        selected_sources_ids = data.getlist('campaign_sources')

        sources = DataSource.objects.filter(id__in=selected_sources_ids)

        camp_client = ClientProfile.objects.get(user=User.objects.get(username=client))
        if campaign_dialer == "none":
            camp_dialer = None
        else:
            camp_dialer = Dialer.objects.get(id=campaign_dialer)

        campaign = Campaign.objects.create(
            name = campaign_name,
            client = camp_client,
            agents_count = agents_count,
            agents_rate = agents_rate,
            weekly_hours = weekly_hours,
            weekly_leads = weekly_leads,
            lead_points = lead_points,

            campaign_type = campaign_type,
            dialer = camp_dialer,

        )
        campaign.datasources.add(*sources)

        return redirect('/admin-campaigns')

            
    
    return render(request,'admin/campaigns/campaign_create.html',context)




@permission_required('admin_campaigns')
@login_required
def campaign_modify(request,camp_id):

    context = {}


    context['profile'] = Profile.objects.get(user=request.user)
    context['sources'] = DataSource.objects.filter(active=True, data_source=True)
    context['campaign_types'] = SERVICE_TYPES
    context['dialers'] = Dialer.objects.filter(active=True)
    context['camp'] = Campaign.objects.get(active=True, id=camp_id)
    context['camp_status'] = CAMP_ACTIVITY

    leadsettings = LeadHandlingSettings.objects.filter(active=True, activated=True, campaign=context['camp']).first()
    context['leadsettings'] = leadsettings
    context['leadsettingslength'] = leadsettings.count_non_none_slot_names() if leadsettings else 0

    campaigndispos = CampaignDispoSetting.objects.filter(active=True, campaign=context['camp']).first()
    context['campaigndispos'] = campaigndispos
    context['campaigndisposlength'] = campaigndispos.count_non_none_slot_names() if campaigndispos else 0

    context['dialer_types'] = DIALERS

    if request.method == "POST":

        if 'general_campaign_settings' in request.POST :
            data = request.POST
            camp_name = data.get('campaign_name')
            agents_count = data.get('agents_count')
            hourly_rate = data.get('hourly_rate')
            weekly_hours = data.get('weekly_hours')
            weekly_leads = data.get('weekly_leads')

            lead_points = data.get('lead_points')
            campaign_type = data.get('campaign_type')
            campaign_dialer = data.get('dialer')
            camp_status = data.get('campaign_status')

            selected_sources_ids = data.getlist('sources')

            campaign_sources = DataSource.objects.filter(id__in=selected_sources_ids)

            camp = Campaign.objects.get(id=camp_id)

            if campaign_dialer == "none":
                camp_dialer = None
            else:
                camp_dialer = Dialer.objects.get(id=campaign_dialer)

            camp.name = camp_name
            camp.agents_count = agents_count
            camp.agents_rate = hourly_rate
            camp.weekly_hours = weekly_hours
            camp.weekly_leads = weekly_leads
            camp.lead_points = lead_points
            camp.campaign_type = campaign_type
            camp.dialer = camp_dialer
            camp.status = camp_status 
            if not selected_sources_ids:
                camp.datasources.clear()  
            else:
                
                camp.datasources.set(campaign_sources)
            camp.save()

            return redirect(request.get_full_path())
        
        if "lead_handling" in request.POST:
            
            campaign = Campaign.objects.get(active=True, id=camp_id)
            data = request.POST

            slot1_name = data.get('slot1_name')
            slot1_percentage = data.get('slot1_percentage')
            slot2_name = data.get('slot2_name')
            slot2_percentage = data.get('slot2_percentage')
            slot3_name = data.get('slot3_name')
            slot3_percentage = data.get('slot3_percentage')
            slot4_name = data.get('slot4_name')
            slot4_percentage = data.get('slot4_percentage')
            slot5_name = data.get('slot5_name')
            slot5_percentage = data.get('slot5_percentage')
            slot6_name = data.get('slot6_name')
            slot6_percentage = data.get('slot6_percentage')
            slot7_name = data.get('slot7_name')
            slot7_percentage = data.get('slot7_percentage')
            slot8_name = data.get('slot8_name')
            slot8_percentage = data.get('slot8_percentage')
            slot9_name = data.get('slot9_name')
            slot9_percentage = data.get('slot9_percentage')
            slot10_name = data.get('slot10_name')
            slot10_percentage = data.get('slot10_percentage')
            
            lead_handling_settings, created = LeadHandlingSettings.objects.update_or_create(
            campaign=campaign,
            defaults={
                'slot1_name': slot1_name if slot1_name not in ["None", None, ""] else None,
                'slot1_percentage': float(slot1_percentage) if slot1_percentage not in ["None", None, ""] else 0.0,
                'slot2_name': slot2_name if slot2_name not in ["None", None, ""] else None,
                'slot2_percentage': float(slot2_percentage) if slot2_percentage not in ["None", None, ""] else 0.0,
                'slot3_name': slot3_name if slot3_name not in ["None", None, ""] else None,
                'slot3_percentage': float(slot3_percentage) if slot3_percentage not in ["None", None, ""] else 0.0,
                'slot4_name': slot4_name if slot4_name not in ["None", None, ""] else None,
                'slot4_percentage': float(slot4_percentage) if slot4_percentage not in ["None", None, ""] else 0.0,
                'slot5_name': slot5_name if slot5_name not in ["None", None, ""] else None,
                'slot5_percentage': float(slot5_percentage) if slot5_percentage not in ["None", None, ""] else 0.0,
                'slot6_name': slot6_name if slot6_name not in ["None", None, ""] else None,
                'slot6_percentage': float(slot6_percentage) if slot6_percentage not in ["None", None, ""] else 0.0,
                'slot7_name': slot7_name if slot7_name not in ["None", None, ""] else None,
                'slot7_percentage': float(slot7_percentage) if slot7_percentage not in ["None", None, ""] else 0.0,
                'slot8_name': slot8_name if slot8_name not in ["None", None, ""] else None,
                'slot8_percentage': float(slot8_percentage) if slot8_percentage not in ["None", None, ""] else 0.0,
                'slot9_name': slot9_name if slot9_name not in ["None", None, ""] else None,
                'slot9_percentage': float(slot9_percentage) if slot9_percentage not in ["None", None, ""] else 0.0,
                'slot10_name': slot10_name if slot10_name not in ["None", None, ""] else None,
                'slot10_percentage': float(slot10_percentage) if slot10_percentage not in ["None", None, ""] else 0.0,
                'activated': True,
                }
            )

            return redirect(request.get_full_path())
        
        if "camp_dispos" in request.POST:
            campaign = Campaign.objects.get(active=True, id=camp_id)
            data = request.POST

            dispo_data = {f"slot{i}_dispo": data.get(f"slot{i}_dispo") for i in range(1, 16)}

            defaults = {
                f'slot{i}_dispo': dispo_data[f"slot{i}_dispo"] if dispo_data[f"slot{i}_dispo"] not in ["None", None, ""] else None
                for i in range(1, 16)
            }
            defaults['active'] = True 

            campaign_dispo_setting, created = CampaignDispoSetting.objects.update_or_create(
                campaign=campaign,
                defaults=defaults
            )
            return redirect(request.get_full_path())
        
        if "campaign_dialer_api" in request.POST:
            campaign = Campaign.objects.get(active=True, id=camp_id)
            data = request.POST
            dialer_type = data.get('dialer_api_type')
            api_key = data.get('dialer_api_key')

            campaign.dialer_type = dialer_type
            campaign.dialer_api_key = api_key



            campaign.save()

            return redirect(request.get_full_path())
        

        if "campaign_lookerstudio" in request.POST:
            campaign = Campaign.objects.get(active=True, id=camp_id)
            data = request.POST
            lookerstudio = data.get('lookerstudio_link')

            campaign.lookerstudio = lookerstudio



            campaign.save()

            return redirect(request.get_full_path())


        if "campaign_doc" in request.POST:
            campaign = Campaign.objects.get(active=True, id=camp_id)
            data = request.POST
            docs = data.get('editor')

            campaign.documentation = docs



            campaign.save()

            return redirect(request.get_full_path())
        

        if "campaign_sop" in request.POST:
            campaign = Campaign.objects.get(active=True, id=camp_id)
            data = request.POST
            docs = data.get('editor2')

            campaign.qa_sop = docs



            campaign.save()

            return redirect(request.get_full_path())


        
            

    return render(request,'admin/campaigns/campaign_modify.html',context)


@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteCampaignView(View):
    def post(self, request, camp_id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_camp = get_object_or_404(Campaign, id=camp_id)
            target_camp.delete()
            return JsonResponse({'message': 'Campaign deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)



@permission_required('admin_contactlists')
@login_required
def contactlists_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['contactlists'] = ContactList.objects.filter(active=True)


    return render(request,'admin/campaigns/contactlists.html',context)



@permission_required('admin_contactlists')
@login_required
def contactlist_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)

    client_role = Role.objects.get(role_name="Client")

    context['profile'] = profile
    context['campaigns'] = Campaign.objects.filter(active=True)

    context['sources'] = DataSource.objects.filter(active=True, source_type__in=["pulling","skip_pull"])
    context['skiptracing'] = DataSource.objects.filter(active=True, source_type__in=['skip_tracing','skip_pull',])
    context['campaign_types'] = SERVICE_TYPES
    context['states'] = US_STATES_CHOICES
    context['statuses'] = LIST_STATUS_CHOICES



    if request.method == "POST":
        data = request.POST
        list_name = data.get('list_name')
        campaign = int(data.get('camp'))
        contacts = int(data.get('contacts'))
        status = data.get('status')
        source = int(data.get('source'))
        skip_tracing = int(data.get('skiptracing'))
        states = data.getlist('states')
        
        source = DataSource.objects.get(id=source)
        skip_tracing = DataSource.objects.get(id=skip_tracing)

        campaign = Campaign.objects.get(id=campaign)
        dialer = campaign.dialer
        contactlist = ContactList.objects.create(
            name = list_name,
            campaign = campaign,
            contacts = contacts,
            dialer = dialer,
            source = source,
            skip_tracing = skip_tracing,
            states = states,
            status = status,
        )

        return redirect('/admin-contactlists')

            
    
    return render(request,'admin/campaigns/contactlist_create.html',context)






@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteContactListView(View):
    def post(self, request, contactlist_id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_list = get_object_or_404(ContactList, id=contactlist_id)
            target_list.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)



@permission_required('admin_campaigns')
@login_required
def dialer_creds_table(request,campaign_id):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaign = Campaign.objects.get(id=campaign_id)
    context['campaign'] = campaign
    context['dialer_creds'] = DialerCredentials.objects.filter(campaign=campaign,active=True)


    return render(request,'admin/credentials/dialer_creds.html',context)



@permission_required('admin_campaigns')
@login_required
def dialer_cred_create(request,campaign_id):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaign = Campaign.objects.get(id=campaign_id)
    context['campaign'] = campaign
    context['account_types'] = DIALER_ACCOUNT_TYPE



    if request.method == "POST":
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        account_type = data.get('account_type')

        campaign = Campaign.objects.get(id=campaign_id)
        
        dialer_cred = DialerCredentials.objects.create(
            campaign=campaign,
            dialer=campaign.dialer,
            username=username,
            password=password,
            account_type=account_type,
        )

        return redirect('/dialercredentials/'+str(campaign_id))

            
    
    return render(request,'admin/credentials/dialer_cred_create.html',context)




@permission_required('admin_campaigns')
@login_required
def dialer_cred_modify(request,cred_id):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    cred = DialerCredentials.objects.get(id=cred_id)
    context['campaign'] = cred.campaign
    context['account_types'] = DIALER_ACCOUNT_TYPE

    context['cred'] = cred



    if request.method == "POST":
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        account_type = data.get('account_type')

        cred = DialerCredentials.objects.get(id=cred_id)

        cred.username = username
        cred.password = password
        cred.account_type = account_type
        cred.save()
        
        

        return redirect('/dialercredentials/'+str(cred.campaign.id))

            
    
    return render(request,'admin/credentials/dialer_cred_modify.html',context)






@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteDialerCredView(View):
    def post(self, request, cred_id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_cred = get_object_or_404(DialerCredentials, id=cred_id)
            
            target_cred.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)






@permission_required('admin_campaigns')
@login_required
def source_creds_table(request,campaign_id):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaign = Campaign.objects.get(id=campaign_id)
    context['campaign'] = campaign
    context['source_creds'] = DataSourceCredentials.objects.filter(campaign=campaign,active=True)


    return render(request,'admin/credentials/source_creds.html',context)







@permission_required('admin_campaigns')
@login_required
def source_cred_create(request,campaign_id):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaign = Campaign.objects.get(id=campaign_id)
    context['campaign'] = campaign
    context['sources'] = DataSource.objects.filter(active=True)
    context['account_types'] = SOURCE_ACCOUNT_TYPE



    if request.method == "POST":
        data = request.POST
        source_id = data.get('source')
        username = data.get('username')
        password = data.get('password')
        account_type = data.get('account_type')

        campaign = Campaign.objects.get(id=campaign_id)
        source = DataSource.objects.get(id=source_id)
        source_cred = DataSourceCredentials.objects.create(
            campaign=campaign,
            datasource=source,
            username=username,
            password=password,
            account_type=account_type,
        )

        return redirect('/sourcecredentials/'+str(campaign_id))

            
    
    return render(request,'admin/credentials/source_cred_create.html',context)


@permission_required('admin_campaigns')
@login_required
def source_cred_modify(request,cred_id):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    cred = DataSourceCredentials.objects.get(id=cred_id)
    context['campaign'] = cred.campaign
    context['cred'] = cred
    context['sources'] = DataSource.objects.filter(active=True)
    context['account_types'] = SOURCE_ACCOUNT_TYPE



    if request.method == "POST":
        data = request.POST
        source_id = data.get('source')
        username = data.get('username')
        password = data.get('password')
        account_type = data.get('account_type')

        
        source_type = DataSource.objects.get(id=source_id)
        source = DataSourceCredentials.objects.get(id=cred_id)

        source.username=username
        source.password=password
        source.account_type=account_type
        source.datasource=source_type
        source.save()
            

        return redirect('/sourcecredentials/'+str(cred.campaign.id))

            
    
    return render(request,'admin/credentials/source_cred_modify.html',context)







@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteSourceCredView(View):
    def post(self, request, cred_id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_cred = get_object_or_404(DataSourceCredentials, id=cred_id)
            
            target_cred.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)








@permission_required('admin_accounts')
@login_required
def agents_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    excluded_roles = []
    excluded_roles.append(Role.objects.get(role_name="Client"))
    context['accounts'] = Profile.objects.all().exclude(role__in=excluded_roles)

    return render(request,'admin/agents/agents.html',context)



@permission_required('admin_accounts')
@login_required
def agent_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['roles'] = Role.objects.filter(active=True)
    context['teams'] = Team.objects.filter(active=True)
    context['countries'] = countries



    if request.method == "POST":
        data = request.POST
        full_name = data.get('full_name')
        username = data.get('username')
        password = data.get('password')
        phone_name = data.get('phone_name')
        phone = data.get('phone')
        discord = data.get('discord')
        residence = data.get('residence')
        birth_date = data.get('birth_date')
        role = data.get('role')
        team = data.get('team')
        login_time = data.get('login_time')
        hiring_date = data.get('hiring_date')
        hourly_rate = data.get('hourly_rate')
        monthly_salary = data.get('monthly_salary')
        salary_type = data.get('salary_type')
        national_id = request.FILES.get('national_id')  # Get the uploaded file
        role = Role.objects.get(id=int(role), active=True)
        team = Team.objects.get(id=int(team), active=True)            
        agent_user = User.objects.create(username=username)
        agent_user.set_password(password)
        agent_user.save()
        agent = Profile.objects.create(
            full_name=full_name,
            user=agent_user,
            password=password,
            phone_name=phone_name,
            phone_number=phone,
            discord=discord,
            residence=residence,
            birth_date=birth_date,
            role=role,
            team=team,
            login_time=login_time,
            hiring_date=hiring_date,
            hourly_rate=hourly_rate,
            monthly_salary=monthly_salary,
            salary_type=salary_type,
            national_id=national_id  # Save the file to the model
        )

        return redirect('/admin-agents')
            
    
    return render(request,'admin/agents/agent_create.html',context)



inactive_statuses = ['hold','dropped','blacklisted']

@permission_required('admin_accounts')
@login_required
def agent_modify(request,username):

    context = {}
    user = User.objects.get(username=username)

    context['agent_profile'] = Profile.objects.get(user=user)

    context['profile'] = Profile.objects.get(user=request.user)
    context['roles'] = Role.objects.filter(active=True)
    context['teams'] = Team.objects.filter(active=True)
    context['countries'] = countries
    context['account_statuses'] = STATUS_CHOICES
    unavailable_roles = ['Client', 'Affiliate']
    if context['agent_profile'].role.role_name in unavailable_roles:
        return redirect('/admin')

    if request.method == "POST":

        if 'payment_method' in request.POST :
            data = request.POST
            payoneer_account = data.get('payoneer_account')
            instapay_account = data.get('instapay_account')
            salary_type = data.get('salary_type')
            salary_account = data.get('salary_account')
            hourly_rate = data.get('hourly_rate')
            monthly_salary = data.get('monthly_salary')

            agent_profile = Profile.objects.get(user=user)
            
            agent_profile.payoneer = payoneer_account
            agent_profile.instapay = instapay_account
            agent_profile.salary_type = salary_type
            agent_profile.payment_method = salary_account
            if salary_type == "hourly":
                agent_profile.hourly_rate = float(hourly_rate)
            elif salary_type == "monthly":
                agent_profile.monthly_salary = float(monthly_salary)
            else:
                pass
            agent_profile.save()
            return redirect(request.get_full_path())
        if 'account_info' in request.POST :
            data = request.POST
            full_name = data.get('full_name')
            email = data.get('email')
            phone_number = data.get('phone_number')
            discord = data.get('discord')
            birth_date = data.get('birth_date')
            hiring_date = data.get('hiring_date')
            login_time = data.get('login_time')
            team = data.get('team')
            role = data.get('role')
            residence = data.get('residence')
            status = data.get('account_status')


            
            team_obj = Team.objects.get(id=int(team))
            role_obj = Role.objects.get(id=int(role))

            agent_profile = Profile.objects.get(user=user)
            agent_profile.full_name = full_name
            agent_profile.email = email
            agent_profile.phone_number = phone_number
            agent_profile.discord = discord
            agent_profile.birth_date = birth_date
            agent_profile.hiring_date = hiring_date
            agent_profile.login_time = login_time
            agent_profile.team = team_obj
            agent_profile.role = role_obj
            agent_profile.residence = residence

            agent_profile.status = status

            if status in inactive_statuses:
                agent_profile.active = False
            else:
                agent_profile.active = True

            agent_profile.save()

            return redirect(request.get_full_path())

        



    
    return render(request,'admin/agents/agent_modify.html',context)




@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteUserView(View):
    def post(self, request, username):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_user = get_object_or_404(User, username=username)
            target_profile = get_object_or_404(Profile, user=target_user)
            target_profile.active=False
            target_profile.save()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)



def upload_id(request, userid):
    if request.method == 'POST':
        if 'national_id' in request.FILES:  # Match with the name attribute in the form
            file = request.FILES['national_id']  # Use the same key as the file input
            # Check if the uploaded file is an image
            if file.content_type.startswith('image'):
                # Example: Save the file to a Profile model instance
                profile = get_object_or_404(Profile, id=userid)
                profile.national_id = file
                profile.save()
                return redirect('/agent-modify/'+str(profile.user))
            else:
                return JsonResponse({'error': 'File is not an image.'}, status=400)
        else:
            return JsonResponse({'error': 'File not provided.'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@permission_required('admin_clients')
@login_required
def clients_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    client_role = Role.objects.get(role_name='Client')
    context['accounts'] = ClientProfile.objects.filter(active=True, role=client_role)

    return render(request,'admin/clients/clients.html',context)


@permission_required('admin_clients')
@login_required
def client_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['us_states'] = us_states
    context['services'] = Service.objects.filter(active=True, status="active")
    context['discovery_options'] = discovery_options

    context['affiliates'] = AffiliateProfile.objects.filter(client_status='active')


    if request.method == "POST":
        data = request.POST
        full_name = data.get('full_name')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        state = data.get('residence')
        joining_date = data.get('joining_date')
        selected_services_ids = data.getlist('services')
        discovery_method = data.get('discovery_method')
        affiliate_id = data.get('affiliate')

        if affiliate_id == "0":
            affiliate_profile = None
        else:  
            affiliate_profile = AffiliateProfile.objects.get(id=affiliate_id)

        services = Service.objects.filter(id__in=selected_services_ids)
        role = Role.objects.get(role_name="Client")
        agent_user = User.objects.create(username=username)
        agent_user.set_password(password)
        agent_user.save()
        

        agent_profile = Profile.objects.create(
            full_name=full_name,
            user=agent_user,
            password=password,
           
            phone_number=phone,
            hourly_rate=0,

            role=role,
        )

        agent = ClientProfile.objects.create(
            full_name=full_name,
            user=agent_user,
            password=password,
            email=email,
            phone_number=phone,
            state=state,
            role=role,
            joining_date=joining_date,
            discovery_method=discovery_method,
            affiliate = affiliate_profile,

        )
        agent.services.add(*services)
        return redirect('/admin-clients')
            
    
    return render(request,'admin/clients/client_create.html',context)




@permission_required('admin_clients')
@login_required
def client_modify(request,username):

    context = {}
    user = User.objects.get(username=username)

    context['agent_profile'] = ClientProfile.objects.get(user=user)
    context['profile'] = Profile.objects.get(user=request.user)
    context['us_states'] = us_states
    context['discovery_options'] = discovery_options
    context['services'] = Service.objects.filter(active=True, status="active")
    context['affiliates'] = AffiliateProfile.objects.filter(client_status='active')
    context['statuses'] = dict(CAMP_ACTIVITY)


    if request.method == "POST":

        if 'account_info' in request.POST :
            data = request.POST
            full_name = data.get('full_name')
            email = data.get('email')
            phone_number = data.get('phone_number')
            joining_date = data.get('joining_date')
            discovery_method = data.get('discovery_method')
            selected_services_ids = data.getlist('services')
            state = data.get('residence')
            affiliate_id = data.get('affiliate')
            status = data.get('client_status')

            if affiliate_id == "0":
                affiliate_profile = None
            else:  
                affiliate_profile = AffiliateProfile.objects.get(id=affiliate_id)

            
            services = Service.objects.filter(id__in=selected_services_ids)
            


            agent_profile = ClientProfile.objects.get(user=user)
            agent_profile.full_name = full_name
            agent_profile.email = email
            agent_profile.phone_number = phone_number
            agent_profile.joining_date = joining_date
            agent_profile.state = state
            agent_profile.discovery_method = discovery_method
            agent_profile.affiliate = affiliate_profile
            agent_profile.client_status = status
            if not selected_services_ids:
                agent_profile.services.clear()  
            else:
                
                agent_profile.services.set(services)
            agent_profile.save()

            return redirect(request.get_full_path())
    return render(request,'admin/clients/client_modify.html',context)


@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteClientView(View):
    def post(self, request, username):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_user = get_object_or_404(User, username=username)
            target_profile = get_object_or_404(ClientProfile, user=target_user)
            target_profile.active=False
            target_profile.save()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)





@permission_required('client_dashboard')
@login_required
def client_dashboard(request, month, year):


    context = {}

    now = tz.now()
    current_year = year
    current_month = month
    current_month_name = _date(now, "F")
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]


    client_profile = ClientProfile.objects.get(user=request.user)


    campaign = Campaign.objects.get(client=client_profile)
    

    context['profile'] = Profile.objects.get(user=request.user)

    context['qualified'] = Lead.objects.filter(
        campaign=campaign,
        pushed__year=current_year,
         status="qualified",
        active=True
        ).count()

    context['disqualified'] = Lead.objects.filter(
        campaign=campaign,
        pushed__year=current_year,
         status__in=["disqualified","callback"],
        active=True
        ).count()

    
    
    context['duplicated'] = Lead.objects.filter(
        campaign=campaign,
        pushed__year=current_year,
         status="duplicated",
        active=True
        ).count()

    
    

    context['total'] =  Lead.objects.filter(
        campaign=campaign,
        pushed__year=current_year,
         active=True
        ).count()
    

    

    char_data_qualified = []
    for month in range(1, 13):
        total_count = Lead.objects.filter(
            campaign=campaign,
            pushed__month=month,
            pushed__year=current_year,
            status="qualified",
            active=True
        ).count()
        char_data_qualified.append(total_count)
    context['char_data_qualified'] = char_data_qualified


    char_data_disqualified = []
    for month in range(1, 13):
        total_count = Lead.objects.filter(
            campaign=campaign,
            pushed__month=month,
            pushed__year=current_year,
            status="disqualified",
            active=True
        ).count()
        char_data_disqualified.append(total_count)
    context['char_data_disqualified'] = char_data_disqualified




        # Determine the first and last days of the current month
    first_day = datetime(current_year, current_month, 1)
    if current_month == 12:
        last_day = datetime(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(current_year, current_month + 1, 1) - timedelta(days=1)

    # Get ISO week numbers for the first and last days of the month
    first_week = first_day.isocalendar()[1]
    last_week = last_day.isocalendar()[1]

    # Initialize a dictionary to store total leads per week
    weekly_leads_count = defaultdict(int)

    # Get leads for the current month and year
    leads = Lead.objects.filter(
        campaign=campaign,
        pushed__year=current_year,
        pushed__month=current_month,
        active=True
    )

    # Order and limit the number of leads in the context for display

    # Count total leads for each week
    for lead in leads:
        week_number = lead.pushed.isocalendar()[1]  # Get ISO week number
        weekly_leads_count[week_number] += 1

    # Ensure that all weeks from first to last are represented
    weeks_in_month = range(first_week, last_week + 1)

    # Prepare list with total leads for each week
    weekly_total_leads_list = [weekly_leads_count.get(week, 0) for week in weeks_in_month]

    # Convert week numbers to "Week 1", "Week 2", etc.
    week_labels = [f"Week {i + 1}" for i in range(len(weeks_in_month))]

    # Update context with week labels and total leads per week
    context['week_numbers'] = week_labels
    context['weekly_total_leads'] = weekly_total_leads_list


    qualified = Lead.objects.filter(
        campaign=campaign,
        pushed__month=current_month,
        pushed__year=current_year,
        status="qualified",
        active=True
        )
    
    qualified_dict = {
        str(lead.lead_id): {
            'longitude': lead.longitude,
            'latitude': lead.latitude,
            'seller_name': lead.seller_name
        }
        for lead in qualified
        if lead.longitude != 0 and lead.latitude != 0
    }
    context['locations'] = mark_safe(json.dumps(qualified_dict))

    state_lead_count = defaultdict(int)

    # Iterate through qualified leads and count by state
    for lead in qualified:
        state = lead.state
        state_lead_count[state] += 1

    # Convert defaultdict to a regular dict
    state_lead_count = dict(state_lead_count)

    # Sort states by lead count in descending order
    sorted_states = sorted(state_lead_count.items(), key=lambda x: x[1], reverse=True)

    # Initialize the dictionary for the top three and the remainder
    top_three_states = {}
    other_states_count = 0

    for i, (state, count) in enumerate(sorted_states):
        if i < 3:
            top_three_states[state] = count
        else:
            other_states_count += count

    # Add the "other states" to the dictionary
    if other_states_count > 0:
        top_three_states['Other'] = other_states_count

    # Update the context
    context['state_lead_count'] = top_three_states

    # Print the top three states and other states count
    


    context['all_leads'] = Lead.objects.filter(active=True,campaign=campaign,      
                                                pushed__year=current_year,
                                                pushed__month=current_month).order_by('-pushed')
    

    return render(request,'admin/clients/client_dashboard.html',context)




@permission_required('client_dashboard')
@login_required
def client_lead_report(request, lead_id):

    context = {}

    context['profile'] = Profile.objects.get(user=request.user)

    client_profile = ClientProfile.objects.get(user=request.user)
    campaign = Campaign.objects.get(client=client_profile)

    lead = Lead.objects.get(lead_id=lead_id,active=True)

    if lead.campaign != campaign:
        return HttpResponseForbidden("You do not have permission to access this resource.")


    context['lead'] = lead

    context['agent_profile'] = lead.agent_profile
    context['property_types'] = PROPERTY_CHOICES
    context['timelines'] = TIMELINE_CHOICES
    context['lead_status'] = LEAD_CHOICES


    
    
    
    

   
        
    return render(request, 'admin/clients/client_lead_report.html', context)



@permission_required('client_lookerstudio')
@login_required
def client_lookerstudio(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    client_profile = ClientProfile.objects.get(user=request.user)
    campaign = Campaign.objects.get(client=client_profile)

    context['lookerstudio'] = campaign.lookerstudio

    return render(request, 'admin/clients/client_lookerstudio.html', context)




@permission_required('affiliate_dashboard')
@login_required
def affiliate_dashboard(request, month, year):


    context = {}
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')

    combined_date = f"{year}-{month:02d}"  # Ensure month is always two digits
    context['combined_date'] = combined_date
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]


    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['us_states'] = us_states
    context['discovery_options'] = discovery_options

    affiliate = AffiliateProfile.objects.get(user=request.user)
   
    context['affiliate'] = affiliate
    clients =  ClientProfile.objects.filter(affiliate=affiliate)

    context['clients'] = clients

    return render(request,'admin/affiliates/affiliate_dashboard.html',context)



@permission_required('admin_affiliates')
@login_required
def affiliates_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    client_role = Role.objects.get(role_name='Affiliate')
    context['accounts'] = AffiliateProfile.objects.filter(active=True, role=client_role)

    return render(request,'admin/affiliates/affiliates.html',context)



@permission_required('admin_affiliates')
@login_required
def affiliate_data(request, username, month, year):


    context = {}
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')

    combined_date = f"{year}-{month:02d}"  # Ensure month is always two digits
    context['combined_date'] = combined_date
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]


    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['us_states'] = us_states
    context['discovery_options'] = discovery_options

    affiliate = AffiliateProfile.objects.get(user=User.objects.get(username=username))
   
    context['affiliate'] = affiliate
    clients =  ClientProfile.objects.filter(affiliate=affiliate)

    context['clients'] = clients

    return render(request,'admin/affiliates/affiliate_data.html',context)






@permission_required('admin_affiliates')
@login_required
def affiliate_invoice_create(request, username):

    now = timezone.now()
    current_year = now.year
    current_month = now.month

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    affiliate = AffiliateProfile.objects.get(user=User.objects.get(username=username))
   
    context['affiliate'] = affiliate
    clients =  ClientProfile.objects.filter(affiliate=affiliate)

    context['clients'] = clients


    if request.method == "POST":
        data = request.POST
        client_id = data.get('client')
        date = data.get('date')
        revenue = data.get('revenue')
        notes = data.get('notes')
        
        client = ClientProfile.objects.get(id=client_id)        

        AffiliateInvoice.objects.create(

            affiliate=affiliate,
            client=client,
            revenue=revenue,
            notes=notes,
            date=date,
        )

        redirecturl = '/affiliate-data/'+str(affiliate.user)+'-'+str(current_month)+'-'+str(current_year)
        
        return redirect(redirecturl)
            
    
    return render(request,'admin/affiliates/affiliate_invoice_create.html',context)



@permission_required('admin_affiliates')
@login_required
def affiliate_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['us_states'] = us_states
    context['discovery_options'] = discovery_options


    if request.method == "POST":
        data = request.POST
        full_name = data.get('full_name')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        state = data.get('residence')
        joining_date = data.get('joining_date')
        discovery_method = data.get('discovery_method')
        commission_percentage = data.get('commission_percentage')
        role = Role.objects.get(role_name="Affiliate")
        agent_user = User.objects.create(username=username)
        agent_user.set_password(password)
        agent_user.save()        

        agent_affiliate = AffiliateProfile.objects.create(
            full_name=full_name,
            user=agent_user,
            password=password,
            email=email,
            phone_number=phone,
            state=state,
            role=role,
            joining_date=joining_date,
            discovery_method=discovery_method,
            commission_percentage=commission_percentage,
        )


        agent_profile = Profile.objects.create(
            full_name=full_name,
            user=agent_user,
            password=password,
           
            phone_number=phone,
            hourly_rate=0,

            role=role,
        )

        


        return redirect('/admin-affiliates')
            
    
    return render(request,'admin/affiliates/affiliate_create.html',context)



@permission_required('admin_affiliates')
@login_required
def affiliate_modify(request,username):

    context = {}
    user = User.objects.get(username=username)

    context['agent_profile'] = AffiliateProfile.objects.get(user=user)
    context['profile'] = Profile.objects.get(user=request.user)
    context['us_states'] = us_states
    context['discovery_options'] = discovery_options


    if request.method == "POST":

        if 'account_info' in request.POST :
            data = request.POST
            full_name = data.get('full_name')
            email = data.get('email')
            phone_number = data.get('phone_number')
            joining_date = data.get('joining_date')
            discovery_method = data.get('discovery_method')
            state = data.get('residence')
            commission_percentage = data.get('commission_percentage')
            
            


            agent_profile = AffiliateProfile.objects.get(user=user)
            agent_profile.full_name = full_name
            agent_profile.email = email
            agent_profile.phone_number = phone_number
            agent_profile.joining_date = joining_date
            agent_profile.state = state
            agent_profile.discovery_method = discovery_method
            agent_profile.commission_percentage = commission_percentage
                
            agent_profile.save()

            return redirect(request.get_full_path())
    return render(request,'admin/affiliates/affiliate_modify.html',context)




@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteAffiliateView(View):
    def post(self, request, username):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_user = get_object_or_404(User, username=username)
            target_profile = get_object_or_404(AffiliateProfile, user=target_user)
            target_profile.active=False
            target_profile.save()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)




@permission_required('admin_provided_services')
@login_required
def services_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['services'] = Service.objects.filter(active=True)
 
    return render(request,'admin/services/services.html',context)


@permission_required('admin_provided_services')
@login_required
def service_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['us_states'] = us_states
    context['services'] = SERVICE_TYPES

    if request.method == "POST":
        data = request.POST
        service_name = data.get('service_name')
        service_type = data.get('service_type')
        

        service = Service.objects.create(
            name=service_name,
            service_type=service_type,
        )

        return redirect('/admin-services')
            
    
    return render(request,'admin/services/service_create.html',context)



@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteServiceView(View):
    def post(self, request, service_id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_service = get_object_or_404(Service, id=service_id)
            target_service.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)



@permission_required('admin_dialers')
@login_required
def dialers_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['dialers'] = Dialer.objects.filter(active=True)
 
    return render(request,'admin/dialers/dialers.html',context)


@permission_required('admin_dialers')
@login_required
def dialer_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['dialer_types'] = DIALER_TYPES

    if request.method == "POST":
        data = request.POST
        dialer_name = data.get('dialer_name')
        dialer_type = data.get('dialer_type')
        

        service = Dialer.objects.create(
            name=dialer_name,
            dialer_type=dialer_type,
        )

        return redirect('/admin-dialers')
            
    
    return render(request,'admin/dialers/dialer_create.html',context)



@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteDialerView(View):
    def post(self, request, dialer_id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_service = get_object_or_404(Dialer, id=dialer_id)
            target_service.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)




@permission_required('admin_sources')
@login_required
def dataSources_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['datasources'] = DataSource.objects.filter(active=True)
 
    return render(request,'admin/datasources/datasources.html',context)


@permission_required('admin_sources')
@login_required
def dataSource_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['source_types'] = DATASOURCE_TYPES

    if request.method == "POST":
        data = request.POST
        source_name = data.get('source_name')
        source_type = data.get('source_type')
        
        if source_type == "crm" or source_type == "data_management":
            data_source = False
        else:
            data_source = True

        service = DataSource.objects.create(
            name=source_name,
            source_type=source_type,
            data_source=data_source,
        )

        return redirect('/admin-datasources')
            
    
    return render(request,'admin/datasources/datasource_create.html',context)



@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteDataSourceView(View):
    def post(self, request, source_id):
        current_user = request.user
        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            target_source = get_object_or_404(DataSource, id=source_id)
            target_source.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)












@permission_required('admin_roles')
@login_required
def roles_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['roles'] = Role.objects.filter(active=True)
                                                  


    return render(request,'admin/roles/roles.html',context)



def role_modify(request, role_id):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    role = Role.objects.get(id=role_id)
    role_fields = role.get_field_labels()

    role_permissions = {
        role_fields[field_name]: getattr(role, field_name, False) 
        for field_name in role_fields.keys()
        if field_name not in ['id', 'role_name','active']
        }


    context['role'] =  role
    context['role_fields'] = role_fields
    context['role_permissions'] = role_permissions

    try:
        role_fields.pop('id')
        role_fields.pop('role_name')
    except:
        pass



    if request.method == "POST":
        # Loop through the form data
        role = Role.objects.get(id=role_id)
        for key, value in role_fields.items():
            # Fetch the new value from POST data


            selected_value = request.POST.get(key)

            
            # Update the role permission based on the selected value (e.g., 'yes' or 'no')
            if selected_value == "yes":
                role.__dict__[key] = True 
            else:
                role.__dict__[key] = False 
        
        # Save the updated role

        role.active=True
        role.save()

        return redirect(request.get_full_path())




    
    return render(request, 'admin/roles/role_modify.html', context)




@permission_required('admin_packages')
@login_required
def packages_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['packages'] = Package.objects.filter(active=True)

    return render(request,'admin/packages/packages.html',context)






@permission_required('admin_packages')
@login_required
def package_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['services'] = Service.objects.filter(active=True, status="active")




    if request.method == "POST":
        data = request.POST


        name = data.get('name')
        description = data.get('description')

        count_va = data.get('count_va')
        rate_va = data.get('rate_va')

        count_lm = data.get('count_lm')
        rate_lm = data.get('rate_lm')

        count_acq = data.get('count_acq')
        rate_acq = data.get('rate_acq')

        count_dm = data.get('count_dm')
        rate_dm = data.get('rate_dm')


        

        package = Package.objects.create(
            name=name,
            description=description,
            count_va=count_va,
            rate_va=rate_va,
            count_lm=count_lm,
            rate_lm=rate_lm,
            count_acq=count_acq,
            rate_acq=rate_acq,
            count_dm=count_dm,
            rate_dm=rate_dm,

        )

        

        
        
        

        return redirect('/admin-packages')
            
    
    return render(request,'admin/packages/package_create.html',context)




@permission_required('admin_packages')
@login_required
def package_modify(request, id):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['services'] = Service.objects.filter(active=True, status="active")

    context['package'] = Package.objects.get(id=id)




    if request.method == "POST":
        data = request.POST

        name = data.get('name')
        description = data.get('description')

        count_va = data.get('count_va')
        rate_va = data.get('rate_va')

        count_lm = data.get('count_lm')
        rate_lm = data.get('rate_lm')

        count_acq = data.get('count_acq')
        rate_acq = data.get('rate_acq')

        count_dm = data.get('count_dm')
        rate_dm = data.get('rate_dm')


        

        package = Package.objects.get(id=id)
        package.name=name
        package.description=description
        package.count_va=count_va
        package.rate_va=rate_va
        package.count_lm=count_lm
        package.rate_lm=rate_lm
        package.count_acq=count_acq
        package.rate_acq=rate_acq
        package.count_dm=count_dm
        package.rate_dm=rate_dm

        package.save()

        
        

        return redirect('/admin-packages')
            
    
    return render(request,'admin/packages/package_modify.html',context)




@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeletePackageView(View):
    def post(self, request, id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            package = get_object_or_404(Package, id=id)
            package.active=False
            package.save()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)
        












@permission_required('admin_contracts')
@login_required
def contract_samples_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['contract_samples'] = ContractSample.objects.filter(active=True)

    return render(request,'admin/contracts/samples.html',context)






@permission_required('admin_contracts')
@login_required
def sample_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['fields'] = CONTRACT_FIELD_TYPES




    if request.method == "POST":
        data = request.POST


        name = data.get('name')
        field = data.get('field')

        editor = data.get('editor')

        ContractSample.objects.create(name=name, field=field, description=editor, creator=profile)
        


        
        

        return redirect('/admin-contract-samples')
            
    
    return render(request,'admin/contracts/sample_create.html',context)




@permission_required('admin_packages')
@login_required
def sample_modify(request, id):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['fields'] = CONTRACT_FIELD_TYPES

    context['sample'] = ContractSample.objects.get(id=id)




    if request.method == "POST":
        data = request.POST

        name = data.get('name')
        field = data.get('field')

        editor = data.get('editor')


        

        sample = ContractSample.objects.get(id=id)
        sample.name=name
        sample.description=editor
        sample.field=field
 
        sample.save()

        
        

        return redirect('/admin-contract-samples')
            
    
    return render(request,'admin/contracts/sample_modify.html',context)




@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteSampleView(View):
    def post(self, request, id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            sample = get_object_or_404(ContractSample, id=id)
            sample.active=False
            sample.save()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)
        





@permission_required('admin_contracts')
@login_required
def contracts_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['contracts'] = Contract.objects.filter(active=True).order_by('-created')

    return render(request,'admin/contracts/contracts_table.html',context)






@permission_required('admin_contracts')
@login_required
def contract_create(request):


    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['packages'] = Package.objects.filter(active=True)
    context['samples'] = ContractSample.objects.filter(active=True)
    context['fields'] = CONTRACT_FIELD_TYPES





    if request.method == "POST":
        data = request.POST

        package = data.get('package')
        sample = data.get('sample')
        field = data.get('field')


        return redirect(f'/contract-create-actual?package={package}&sample={sample}&field={field}')


        

       

        


            
    
    return render(request,'admin/contracts/contract_create.html',context)




@permission_required('admin_contracts')
@login_required
def contract_create_actual(request):
    # Get the package_id and sample_id from the URL query parameters
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    package_id = request.GET.get('package')
    sample_id = request.GET.get('sample')
    field = request.GET.get('field')

    


    package = Package.objects.get(id=package_id)
    sample = ContractSample.objects.get(id=sample_id)


    context['package'] = package
    context['sample'] = sample
    # Check if both parameters exist
    if package_id and sample_id:
        # Fetch the Package and Sample objects based on the passed IDs
        if request.method == "POST":
            package = Package.objects.get(id=package_id)
            sample = ContractSample.objects.get(id=sample_id)

            data = request.POST

            client_name = data.get('client_name')
            client_phone = data.get('client_phone')
            client_email = data.get('client_email')

            checkout_link = data.get('checkout_link')


            count_va = data.get('count_va')
            rate_va = data.get('rate_va')
            
            count_lm = data.get('count_lm')
            rate_lm = data.get('rate_lm')

            count_acq = data.get('count_acq')
            rate_acq = data.get('rate_acq')

            count_dm = data.get('count_dm')
            rate_dm = data.get('rate_dm')
            
            contract_text = data.get('editor')

            contract = Contract.objects.create(
                client_name=client_name,
                client_phone=client_phone,
                client_email=client_email,
                strip_link = checkout_link,
                package=package,
                sample=sample,
                count_va=count_va,
                rate_va=rate_va,
                count_lm=count_lm,
                rate_lm=rate_lm,
                count_acq=count_acq,
                rate_acq=rate_acq,
                count_dm=count_dm,
                rate_dm=rate_dm,
                contract_text=contract_text,
                field = field,

            )

            utc_now = datetime.utcnow()

            # Get the timezone object for 'America/New_York'
            est_timezone = pytz.timezone('America/New_York')

            # Convert UTC time to Eastern timezone
            est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

            # Format the time as HH:MM:SS string
            est = est_time.strftime('%I:%M:%S %p')


            # Construct the content of the embed with quote formatting
            request_ip = request.META.get('REMOTE_ADDR')
            try:

            

                content = f'**Agent:** {profile.full_name}\n\n**Action:** Created a **{contract.get_field_display()} Contract** for **{contract.client_name}**\n\n**ID:** {contract.unique_id} \n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

                send_discord_message_contract(content, 'created')
                
            except Exception as e:
                pass

            return redirect('/admin-contracts')

        # Pass the objects to the template

    return render(request, 'admin/contracts/contract_create_actual.html', context)








def contract_view(request, id):


    context = {}
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = "Guest"
    context['profile'] = profile

    contract = Contract.objects.get(unique_id = id)
    context['contract'] = Contract.objects.get(unique_id = id)

    



    # Construct the content of the embed with quote formatting
    request_ip = request.META.get('REMOTE_ADDR')
    data = get_ip_info(request_ip)

    ContractVisit.objects.create(contract=context['contract'], ip_address=request_ip, isp=data['isp'], location=data['location'])
    utc_now = datetime.utcnow()

    # Get the timezone object for 'America/New_York'
    est_timezone = pytz.timezone('America/New_York')

    # Convert UTC time to Eastern timezone
    est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

    # Format the time as HH:MM:SS string
    est = est_time.strftime('%I:%M:%S %p')

    location = data['location']
    isp = data['isp']

    try:

        
        content = f'**Agent:** {profile}\n\n**Action:** Viewed **{contract.client_name}\'s Contract**\n\n**ID:** {contract.unique_id}  \n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}\n\n**Location:** {location}\n\n**Service Provider:** {isp}'

        send_discord_message_contract(content, 'visit')
        
    except Exception as e:
        print(e)
        pass

    if request.method == "POST":
        data = request.POST

        contract = Contract.objects.get(unique_id=id)
        contract.clicked=True
        contract.save()

        redirect_link = "/contract-pref/"+str(contract.unique_id)




        return redirect(redirect_link)

        

       

        


            
    
    return render(request,'admin/contracts/contract_view.html',context)





@csrf_exempt
def contract_pref(request, id):
    context = {}
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = "Guest"
    context['profile'] = profile

    

    context['contract_id'] = id

    context['prices'] = CONTRACT_PREF_PRICE_RANGES

    context['property_types'] = CONTRACT_PREF_PROPERTY_TYPE
    context['property_types_re'] = CONTRACT_PREF_PROPERTY_TYPE_RE
    context['residential_types'] = CONTRACT_PREF_RE_RESD_TYPES
    
    
    context['owner_types'] = CONTRACT_PREF_OWNER_TYPE

    contract = Contract.objects.get(unique_id=id)

    # Get IP information
    request_ip = request.META.get('REMOTE_ADDR')
    ip_data = get_ip_info(request_ip)

    if contract.pref_submitted:
        return redirect('/contract-pref-success/'+contract.unique_id)
    
    # Handle POST request
    if request.method == "POST":
        data = request.POST

        file=None
        if contract.field == "roofing":
            name = data.get('name')
            phone = data.get('phone')
            email = data.get('email')
            company_name = data.get('company_name')
            company_mention = data.get('company_mention')
            property_type = data.get('property_type')
            owner_type = data.get('owner_type')
            price_ranges = request.POST.getlist('price_ranges')
            coverage = data.get('coverage')
            standout = data.get('standout')
            questions = data.get('qualifying_questions')
            company_info = data.get('company_more_info')
            extra_notes = data.get('extra_notes')

            if company_mention == "yes":
                company_mention = True
            else:
                company_mention = False
            



            if 'file_upload' in request.FILES:
                file = request.FILES.get('file_upload')
                try:
                    validate_file(file)
                    
                except ValidationError as e:
                    file= None


            ContractPref.objects.create(
                contract=contract,
                name=name,
                phone=phone,
                email=email,
                company_name=company_name,
                mention_company = company_mention,
                property_type=property_type,
                owner_type=owner_type,
                price_range=price_ranges,
                coverage=coverage,
                standout=standout,
                questions=questions,
                company_info=company_info,
                extra_notes=extra_notes,
                script_file=file if file else None
            )

            contract.pref_submitted = True
            contract.save()



            request_ip = request.META.get('REMOTE_ADDR')
            data = get_ip_info(request_ip)

            utc_now = datetime.utcnow()

            # Get the timezone object for 'America/New_York'
            est_timezone = pytz.timezone('America/New_York')

            # Convert UTC time to Eastern timezone
            est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

            # Format the time as HH:MM:SS string
            est = est_time.strftime('%I:%M:%S %p')

            location = data['location']
            isp = data['isp']

            try:

                
                content = f'**User:** {profile}\n\n**Action:** Filled **{contract.client_name}\'s Preferences**\n\n**ID:** {contract.unique_id}  \n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}\n\n**Location:** {location}\n\n**Service Provider:** {isp}'

                send_discord_message_contract(content, 'filled')
                
            except Exception as e:
                print(e)
                pass




            return redirect('/contract-pref-success/'+contract.unique_id)
        elif contract.field == "realestate":
            name = data.get('name')
            phone = data.get('phone')
            email = data.get('email')
            company_name = data.get('company_name')
            remodeled = data.get('remodeled')
            on_market = data.get('on_market')
            listed_owner = data.get('listed_owner')
            closing_fees = data.get('closing_fees')
            realtor_fees = data.get('realtor_fees')
            re_license = data.get('re_license')
            company_mention = data.get('company_mention')
            property_type_re = request.POST.getlist('property_type_re')
            owner_type = data.get('owner_type')
            price_ranges = request.POST.getlist('price_ranges')
            lots_type = data.get('lots_type')
            res_type = request.POST.getlist('res_types')
            equity = data.get('equity')
            above_market_perc = data.get('above_market_perc')
            coverage = data.get('coverage')
            questions = data.get('qualifying_questions')
            extra_notes = data.get('extra_notes')

            if company_mention == "yes":
                company_mention = True
            else:
                company_mention = False

            if remodeled == "yes":
                remodeled = True
            else:
                remodeled = False


            if on_market == "yes":
                on_market = True
            else:
                on_market = False    


            if listed_owner == "yes":
                listed_owner = True
            else:
                listed_owner = False  



            if closing_fees == "yes":
                closing_fees = True
            else:
                closing_fees = False  

            if realtor_fees == "yes":
                realtor_fees = True
            else:
                realtor_fees = False  


            if re_license == "yes":
                re_license = True
            else:
                re_license = False  




            if 'file_upload' in request.FILES:
                file = request.FILES.get('file_upload')
                try:
                    validate_file(file)
                    
                except ValidationError as e:
                    file= None


            ContractPref.objects.create(
                contract=contract,
                name=name,
                phone=phone,
                email=email,
                company_name=company_name,
                remodeled=remodeled,
                on_market=on_market,
                listed_owner=listed_owner,
                closing_fees=closing_fees,
                realtor_fees=realtor_fees,
                re_license=re_license,
                property_type_re=property_type_re,
                mention_company = company_mention,
                owner_type=owner_type,
                price_range=price_ranges,
                lots_type=lots_type,
                res_type=res_type,
                equity=equity,
                above_market_perc=above_market_perc,
                coverage=coverage,
                questions=questions,
                extra_notes=extra_notes,
                script_file=file if file else None
            )

            contract.pref_submitted = True
            contract.save()

            request_ip = request.META.get('REMOTE_ADDR')
            data = get_ip_info(request_ip)

            utc_now = datetime.utcnow()

            # Get the timezone object for 'America/New_York'
            est_timezone = pytz.timezone('America/New_York')

            # Convert UTC time to Eastern timezone
            est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

            # Format the time as HH:MM:SS string
            est = est_time.strftime('%I:%M:%S %p')

            location = data['location']
            isp = data['isp']

            try:

                
                content = f'**User:** {profile}\n\n**Action:** Filled **{contract.client_name} Preferences**\n\n**ID:** {contract.unique_id}  \n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}\n\n**Location:** {location}\n\n**Service Provider:** {isp}'

                send_discord_message_contract(content, 'filled')
                
            except Exception as e:
                print(e)
                pass


            return redirect('/contract-pref-success/'+contract.unique_id)



    # Render templates based on the 'field' value
    if contract.field == 'roofing':
        return render(request, 'admin/contracts/pref_form_roofing.html', context)
    elif contract.field == 'realestate':
        return render(request, 'admin/contracts/pref_form_re.html', context)




@permission_required('admin_contracts')
@login_required
def contract_pref_view(request, id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['contract_id'] = id

    context['prices'] = CONTRACT_PREF_PRICE_RANGES

    context['property_types'] = CONTRACT_PREF_PROPERTY_TYPE
    context['property_types_re'] = CONTRACT_PREF_PROPERTY_TYPE_RE
    context['residential_types'] = CONTRACT_PREF_RE_RESD_TYPES
    
    
    context['owner_types'] = CONTRACT_PREF_OWNER_TYPE

    contract = Contract.objects.get(unique_id=id)

    context['pref'] = ContractPref.objects.get(contract=contract)

    # Get IP information
    request_ip = request.META.get('REMOTE_ADDR')
    ip_data = get_ip_info(request_ip)

    
    

    # Render templates based on the 'field' value
    if contract.field == 'roofing':
        return render(request, 'admin/contracts/pref_view_roofing.html', context)
    elif contract.field == 'realestate':
        return render(request, 'admin/contracts/pref_view_re.html', context)


def contract_pref_success(request, id):

    context = {}
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = "Guest"
    context['profile'] = profile

    contract = Contract.objects.get(unique_id=id)

    context['contract'] = contract


    return render(request, 'statuses/contract_200.html', context)






@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteContractView(View):
    def post(self, request, id):
        current_user = request.user

        # Ensure correct data access
        try:
            body = json.loads(request.body)
            password = body['password']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Password not provided.'}, status=400)

        # Authenticate user based on current_user and provided password
        user = authenticate(username=current_user.username, password=password)

        if user is not None:
            # Check if the authenticated user can delete the target user
            contract = get_object_or_404(Contract, id=id)
            contract.active=False
            contract.save()
            return JsonResponse({'message': 'Contract deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)











@permission_required('admin_server_settings')
@login_required
def server_settings(request):

    context = {}


    context['profile'] = Profile.objects.get(user=request.user)

    server_settings = ServerSetting.objects.first()

    context['settings'] = server_settings



    context['dialer_types'] = DIALERS

    if request.method == "POST":

        if 'general_info' in request.POST :
            data = request.POST

            server_settings = ServerSetting.objects.first()

            company_name = data.get('company_name')
            company_domain = data.get('company_domain')
            crm_domain = data.get('crm_domain')
            logo_height = data.get('logo_height')
            logo_width = data.get('logo_width')
            terms = data.get('terms')
            privacy = data.get('privacy')

            server_settings.company_name = company_name
            server_settings.company_website = company_domain
            server_settings.crm_domain = crm_domain
            server_settings.logo_dashboard_height = logo_height
            server_settings.logo_dashboard_width = logo_width
            server_settings.terms = terms
            server_settings.privacy = privacy

            if request.FILES.get('main_logo'):
                server_settings.logo_main =  request.FILES.get('main_logo')
                print('main')
                
            if request.FILES.get('login_logo'):
                server_settings.logo_login =  request.FILES.get('login_logo')
                print('login')

            if request.FILES.get('favicon'):
                server_settings.favicon =  request.FILES.get('favicon')
                print('favicon')

            if request.FILES.get('apple_touch'):
                server_settings.apple_touch_icon =  request.FILES.get('apple_touch')
                print('apple')

            server_settings.save()

            

            
             
            return redirect(request.get_full_path())
        
        if "discord_settings" in request.POST:
            
            data = request.POST

            sales_looker = data.get('sales_lookerstudio')
            login = data.get('discord_login')
            activity = data.get('discord_activity')
            leads = data.get('discord_leads')
            requests = data.get('discord_requests')
            applications = data.get('discord_applications')
            prepayments = data.get('discord_prepayments')
            tasks = data.get('discord_tasks')
            sales = data.get('discord_sales')
            clients = data.get('discord_clients')

            server_settings = ServerSetting.objects.first()

            server_settings.sales_lookerstudio = sales_looker
            server_settings.logins_webhook = login
            server_settings.activity_webhook = activity
            server_settings.leads_webhook = leads
            server_settings.requests_webhook = requests
            server_settings.applications_webhook = applications
            server_settings.prepayments_webhook = prepayments
            server_settings.tasks_webhook = tasks
            server_settings.sales_webhook = sales
            server_settings.clients_webhook = clients

            server_settings.save()

        if "general_settings" in request.POST:

            data = request.POST

            break_payable = data.get('break')
            target_points = data.get('target_points')
            whatsapp_template = data.get('whatsapp_template')

            if break_payable == "yes":

                break_paid = True

            else:

                break_paid = False
            
            server_settings = ServerSetting.objects.first()

            server_settings.break_paid = break_paid
            server_settings.monthly_leadpoints_target = int(target_points)
            server_settings.whatsapp_template = whatsapp_template

            server_settings.save()



             

            return redirect(request.get_full_path())
 
            

            

    return render(request,'admin/settings/settings.html',context)








from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import user_passes_test

# This view will log out all other users except the currently logged-in user
@user_passes_test(lambda u: u.is_superuser)  # Ensure only superusers can access this view
def logout_all(request):
    # Get the currently logged-in user
    current_user = request.user

    # Logout the current user (but don't remove their session)

    # Invalidate all user sessions except for the current user's session
    sessions = Session.objects.all()
    for session in sessions:
        # If the session user is not the currently logged-in user, delete the session
        if session.get_decoded().get('_auth_user_id') != str(current_user.id):
            session.delete()

    return redirect('/')  # Redirect to the homepage or any other page




import re
# Define the formatting function (same as before)
def format_phone_number(number):
    # Remove spaces, dashes, and parentheses
    number = re.sub(r'[^\d+]', '', number)
    
    # Check if it's already in international format
    if number.startswith("+") and not number.startswith("+20"):
        return number  # Foreign number, do nothing
    
    # Remove leading zeros, country codes, or '00' international prefixes
    number = re.sub(r'^(00|0+20|0+)', '', number)

    # Prepend +20 to numbers that aren't already formatted
    if not number.startswith("+"):
        return "+20" + number
    return number

# Function to format all phone numbers in the Application model
def update_numbers():
    # Get all applications that have a phone number
    applications = Application.objects.all()
    
    for application in applications:
        # Check if the phone field is not empty
        if application.phone:
            # Format the phone number using the defined function

            formatted_phone = format_phone_number(application.phone)
            print(f"Old: {application.phone} / New: {formatted_phone}")
            # Save the updated phone number to the database
            application.phone = formatted_phone
            application.save()  # Save the changes for each application

    print("Phone numbers have been updated.")

# Call the function to update the phone numbers
