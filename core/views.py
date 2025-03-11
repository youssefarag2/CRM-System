from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Application
from django.conf import settings as django_settings
from django.http import JsonResponse,HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
import uuid
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Q, Sum
from collections import defaultdict
from .signals import *
from discord_app.views import *
from pytz import timezone
import pytz
from django.apps import apps
from .models import *
from datetime import datetime,timedelta
import json
from django.utils import timezone as tz
from django.template.defaultfilters import date as _date
 
import calendar
from django.utils.timezone import now
from django.utils.safestring import mark_safe
import requests
from django.views.decorators.http import require_http_methods
from core.decorators import *

from discord_app.bot import queue_message as discord_private




try:
    settings = ServerSetting.objects.first()
except:
    settings = None

def format_timedelta(td):
    if td is None:
        return '00:00:00'
    
    # Get total seconds from timedelta
    total_seconds = int(td.total_seconds())
    
    # Calculate hours, minutes, and seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format as HH:MM:SS
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
    return formatted_time

def format_percentage(number):
    # Format the number to two decimal places and multiply by 100 for percentage
    formatted = f"{number * 100:.2f}"
    # Remove trailing zeros and decimal point if needed
    return formatted.rstrip('0').rstrip('.')




def maintenance(request):
    return render(request, 'maintenance.html')



active_statuses = ["active","upl","annual","casual","sick"]
inactive_statuses = ["hold","dropped","blacklisted"]


def loginview(request):
    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if str(profile.role) == "Client":
            return redirect(f'/client-dashboard/{current_month}-{current_year}')
        else:
            return redirect('/')
    else:
        if request.method == "POST":
            data = request.POST
            username=data.get('username')
            password = data.get('password')
            
            
            usera = authenticate(username=username,password=password)
            if not usera:
                context['error'] = "Wrong Username or Password"
                return render(request, "login.html", context)            

            userprofile = Profile.objects.get(user=usera)
            active = userprofile.active
            

            if not active or userprofile.status in inactive_statuses:
                context['error'] = "Your Account has been suspended."
                return render(request, "login.html", context)


            if active and userprofile.status in active_statuses:

                
                login(request,usera)



                try:
                    discord_crm_login(userprofile.full_name,True,request)
                except:
                    pass     
            
                return redirect('/')
                
    
    return render(request,'login.html',context)




@login_required
def logoutview(request):

    try:
        userprofile = Profile.objects.get(user=request.user)

    except:
        userprofile = ClientProfile.objects.get(user=request.user)

    try:
        discord_crm_login(userprofile.full_name,False,request)
    except:
        pass  

    logout(request)




    return redirect('/login')


@permission_required('caller_dashboard')
@login_required
def home(request):
    today = (tz.localtime(tz.now())).date()
    now = tz.now()
    current_year = now.year
    current_month = now.month
    user = request.user
    try:
        work_status = WorkStatus.objects.get(user=user, date=today)
    except:
        work_status = None

    try:
        settings = ServerSetting.objects.first()
    except:
        pass
    context = {
               
               "work_status":work_status,
               }
    profile = Profile.objects.get(user=request.user)

    if str(profile.role) == "Client":
        return redirect(f'/client-dashboard/{current_month}-{current_year}')



    context['profile'] = profile

    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_name = now.strftime('%B')
    context['month_name'] = month_name
    context['current_year'] = current_year
    monthly_qualified_count = []

    leads = Lead.objects.filter(agent_profile=profile,
                    pushed__year=current_year,
                    pushed__month=current_month)
    

    context['leads_count'] = leads.count()
    total_lead_flow = leads.aggregate(total_lead_flow=Sum('lead_flow'))['total_lead_flow']
    try:
        leads_flow_quality = round((total_lead_flow / leads.count()),2)
    except:
        leads_flow_quality = 0
    context['leads_flow'] = leads_flow_quality


    for month in range(1, 13):
        # Filter leads for the current month and year
        leads_count = Lead.objects.filter(
            agent_profile=profile,
            pushed__year=current_year,
            pushed__month=month,
            status="qualified",
        ).count()
        monthly_qualified_count.append(leads_count)

    monthly_disqualified_count = []

    for month in range(1, 13):
        # Filter leads for the current month and year
        leads_count = Lead.objects.filter(
            agent_profile=profile,
            pushed__year=current_year,
            pushed__month=month,
            status="disqualified",
        ).count()
        monthly_disqualified_count.append(leads_count)
        
    context['qualified_count'] = monthly_qualified_count
    context['disqualified_count'] = monthly_disqualified_count

    leads = Lead.objects.filter(agent_profile=profile,
                    pushed__year=current_year,
                    pushed__month=current_month,
                    status="qualified")

    leads_per_campaign = leads.values('campaign').annotate(lead_count=Count('lead_id')).order_by('campaign')

# Create a dictionary with campaign objects as keys and lead counts as values
    campaign_leads_count = {
        Campaign.objects.get(pk=item['campaign']).lead_points: item['lead_count']
        for item in leads_per_campaign
    }


    total_points = sum(key * value for key, value in campaign_leads_count.items())

    context['lead_points'] = total_points
    
    monthly_target = settings.monthly_leadpoints_target
    if monthly_target == 0:
        context['target_percentage'] = 0
    else:
        context['target_percentage'] = round((total_points / monthly_target) * 100, 2)


    qualified_count = Lead.objects.filter(
        agent_profile=profile,
        pushed__year=current_year,
        status="qualified",
    ).count()

    disqualified_count = Lead.objects.filter(
        agent_profile=profile,
        pushed__year=current_year,
        status="disqualified",
    ).count()

    callback_count = Lead.objects.filter(
        agent_profile=profile,
        pushed__year=current_year,

        status="callback",
    ).count()

    duplicated_count = Lead.objects.filter(
        agent_profile=profile,
        pushed__year=current_year,

        status="duplicated",
    ).count()
    context['lead_results_year'] = [qualified_count,
            disqualified_count,
            callback_count,
            duplicated_count
        ]



    agent = profile

    # Define status field mapping
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    try:
        settings = ServerSetting.objects.first()
        break_paid = settings.break_paid
    except:
        break_paid = False
    # Calculate total time for each status per agent
    status_totals = {}
    agent_totals = {}
    for status in ['ready', 'meeting', 'break', 'offline']:
        total_time = WorkStatus.objects.filter(
            user=agent.user,
            date__month=current_month,
            date__year=current_year
        ).aggregate(total_time=Sum(status_field_mapping[status]))

        total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

        status_totals[status] = formatted_time
        if status == "break":
            status_totals[f"{status}_total"] = round((total_seconds / 3600) * agent.hourly_rate, 2) if break_paid else 0
        else:
            status_totals[f"{status}_total"] = round((total_seconds / 3600) * agent.hourly_rate, 2)


    total_worked_time_seconds = sum([
        (WorkStatus.objects.filter(user=agent.user, date__month=current_month, date__year=current_year).aggregate(
            total_ready_time=Sum('ready_time'),
            total_meeting_time=Sum('meeting_time'),
            total_break_time=Sum('break_time')
        )[field] or timedelta()).total_seconds()
        for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
    ])
    status_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"



    total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=current_month, date__year=current_year).aggregate(
        total_ready_time=Sum('ready_time')
    )['total_ready_time'] or timedelta()).total_seconds()
    total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=current_month, date__year=current_year).aggregate(
        total_meeting_time=Sum('meeting_time')
    )['total_meeting_time'] or timedelta()).total_seconds()
    total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=current_month, date__year=current_year).aggregate(
        total_break_time=Sum('break_time')
    )['total_break_time'] or timedelta()).total_seconds()

    total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)

    # Fetch added and removed manual hours
    added_minutes = ManualHours.objects.filter(created__month=current_month, created__year=current_year, agent_profile=agent, positive=True, active=True).aggregate(total_added=Sum('hours'))['total_added'] or 0
    removed_minutes = ManualHours.objects.filter(created__month=current_month, created__year=current_year, agent_profile=agent, positive=False, active=True).aggregate(total_removed=Sum('hours'))['total_removed'] or 0
    deductions = Action.objects.filter(
        agent=agent.user,
        action_type="deduction",
        status="approved",
        active=True,
        submission_date__month=current_month,
        submission_date__year=current_year
    )

    ded_total = deductions.aggregate(total_deductions=Sum('deduction_amount'))['total_deductions'] or 0
    payments = Prepayment.objects.filter(
        agent=agent.user,
        status="approved",
        active=True,
        submission_date__month=current_month,
        submission_date__year=current_year
    )

    prepayment_total = payments.aggregate(total_prepayments=Sum('amount'))['total_prepayments'] or 0

    # Convert manual hours to seconds (assuming manual hours are in hours)
    added_seconds = added_minutes * 60
    removed_seconds = removed_minutes * 60
    deduction_seconds = ded_total * 3600

     

    # Adjust total payable time with manual hours
    total_positive = total_payable_time_seconds + added_seconds
    total_payable =  total_positive - removed_seconds - deduction_seconds


    

    
    status_totals['total_payable'] = f"{int(total_payable // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

    context['total_time'] = status_totals['total_payable']
    
    return render(request,'dashboard/agent.html',context)





@login_required
def user_profile(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    return render(request,'profile.html', context)


@permission_required('campaign_documentation')
@login_required
def camp_doc(request, id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaign = Campaign.objects.get(id=id)
    context['camp'] = campaign

    return render(request,'admin/campaigns/campaign_doc.html', context)


@permission_required('campaign_sop')
@login_required
def camp_sop(request, id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaign = Campaign.objects.get(id=id)
    context['camp'] = campaign

    return render(request,'admin/campaigns/campaign_sop.html', context)


@permission_required('lead_submission')
@login_required
def lead_submission_re(request):
    context = {"api_token":django_settings.HERE_API}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['campaigns'] = Campaign.objects.filter(campaign_type="calling", status="active")
    context['contactlists'] = ContactList.objects.filter(active=True)
    if request.method == "POST":
        lat,long = 0,0
        data = request.POST
        campid = data.get('campaign')
        contactlistid = data.get('dialer_list')
        prospect_name = data.get('owner_name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        property_type = data.get('property_type')
        address = data.get('address')
        asking_price = data.get('asking_price')
        market_value = data.get('market_value')
        reason = data.get('reason')
        timeline = data.get('timeline')
        zillow_url = data.get('zillow_url')
        callback_time = data.get('callback_time')
        general_info = data.get('general_info')
        extra_info = data.get('extra_info')
        lat,long = data.get('latitude'),data.get('longitude')
        state,county = data.get('state'), data.get('county')
        
    
        agent_profile = Profile.objects.get(user=request.user)
        campaign = Campaign.objects.get(id=campid)
        if int(contactlistid) == 0:
            contact_list = None
        else:
            contact_list = ContactList.objects.get(id=contactlistid)
        lead = Lead.objects.create(
            agent_user=request.user,
            agent_profile=agent_profile,
            campaign=campaign,
            lead_type="realestate",
            contact_list=contact_list,
            property_type=property_type,
            seller_name = prospect_name,
            seller_phone= phone_number,
            seller_email= email,
            timeline=timeline,
            reason=reason,
            property_address=address,
            asking_price=asking_price,
            market_value=market_value,
            general_info=general_info,
            property_url=zillow_url,
            callback=callback_time,
            extra_notes=extra_info,
            latitude=lat,
            longitude=long,
            state=state,
            county=county,
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

           
            lead_id = lead.lead_id

            content = f'**Agent:** {profile.full_name}\n\n**Action:** Posted a New Lead on **{str(lead.campaign).upper()}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

            send_discord_message_lead(content,lead_id)
            
        except:
            pass
    

        return redirect('/')


    return render(request,'leads/lead_submission_re.html', context)





@permission_required('lead_submission')
@login_required
def lead_submission_roofing(request):
    context = {"api_token":django_settings.HERE_API}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['campaigns'] = Campaign.objects.filter(campaign_type="calling", status="active")
    context['contactlists'] = ContactList.objects.filter(active=True)
    if request.method == "POST":
        lat,long = 0,0
        data = request.POST
        campid = data.get('campaign')
        contactlistid = data.get('dialer_list')
        prospect_name = data.get('owner_name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        property_type = data.get('property_type')
        address = data.get('address')


        roof_age = data.get('roof_age')
        appointment_time = data.get('appointment_time')
        known_issues = data.get('known_issues')






        extra_info = data.get('extra_info')
        lat,long = data.get('latitude'),data.get('longitude')
        state,county = data.get('state'), data.get('county')
        
    
        agent_profile = Profile.objects.get(user=request.user)
        campaign = Campaign.objects.get(id=campid)
        if int(contactlistid) == 0:
            contact_list = None
        else:
            contact_list = ContactList.objects.get(id=contactlistid)
        lead = Lead.objects.create(
            agent_user=request.user,
            agent_profile=agent_profile,
            lead_type="roofing",
            campaign=campaign,
            contact_list=contact_list,
            property_type=property_type,
            seller_name = prospect_name,
            seller_phone= phone_number,
            seller_email= email,

            property_address=address,

            roof_age=roof_age,
            appointment_time=appointment_time,
            known_issues=known_issues,
            extra_notes=extra_info,
            latitude=lat,
            longitude=long,
            state=state,
            county=county,
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

           
            lead_id = lead.lead_id

            content = f'**Agent:** {profile.full_name}\n\n**Action:** Posted a New Lead on **{str(lead.campaign).upper()}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

            send_discord_message_lead(content,lead_id)
            
        except:
            pass
    

        return redirect('/')


    return render(request,'leads/lead_submission_roofing.html', context)





@permission_required('my_leads')
@login_required
def my_leads(request, month, year):

 
    context = {}

    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['profile'] = Profile.objects.get(user=request.user)

    context['pending_leads'] = Lead.objects.filter(agent_user=request.user,status="pending", active=True).order_by('-pushed')[:5]

    context['qualified'] = Lead.objects.filter(
        pushed__month=month,
        pushed__year=year,
        agent_user=request.user,
        status="qualified",
        active=True
        ).count()

    context['disqualified'] = Lead.objects.filter(
        pushed__month=month,
        pushed__year=year,
        agent_user=request.user,
        status__in = ["disqualified", "duplicate"],
        active=True
        ).count()

    pending_leads = Lead.objects.filter(
        pushed__month=month,
        pushed__year=year,
        agent_user=request.user,
        status="pending",
        active=True
        )
    
    context['pending'] = pending_leads.count()

    context['callback'] = Lead.objects.filter(
        pushed__month=month,
        pushed__year=year,
        agent_user=request.user,
        status="callback",
        active=True
        ).count()
    

    context['total'] =  Lead.objects.filter(
        pushed__month=month,
        pushed__year=year,
        agent_user=request.user,
        active=True
        ).count()
    

    context['leads_list'] =  Lead.objects.filter(
        pushed__month=month,
        pushed__year=year,
        agent_user=request.user,
        active=True
        ).order_by("-pushed")[:6]
    
   
    

    def calculate_percentage(part, whole):
        if whole == 0:
            return 0
        return (part / whole) * 100

    qualified_percentage = calculate_percentage(context['qualified'], context['total'])
    disqualified_percentage = calculate_percentage(context['disqualified'], context['total'])
    pending_percentage = calculate_percentage(context['pending'], context['total'])
    callback_percentage = calculate_percentage(context['callback'], context['total'])

    # Format percentages
    def format_percentage(value):
        return '{:.2f}'.format(value).rstrip('0').rstrip('.')

    context['qualified_perc'] = format_percentage(qualified_percentage)
    context['disqualified_perc'] = format_percentage(disqualified_percentage)
    context['pending_perc'] = format_percentage(pending_percentage)
    context['callback_perc'] = format_percentage(callback_percentage)


    
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile


    negative_threshold = settings.negative_percentage
    neutral_threshold = settings.neutral_percentage


    leads = Lead.objects.filter(agent_profile=profile,
                    pushed__year=year,
                    pushed__month=month).exclude(status="pending").order_by('-pushed')
    
    context['contacts'] = leads[:10]
    lead_flows = list(leads.values_list('lead_flow', flat=True))
    total_count = len(lead_flows)

    negative_count = sum(1 for flow in lead_flows if flow < negative_threshold)
    neutral_count = sum(1 for flow in lead_flows if negative_threshold <= flow < neutral_threshold)
    positive_count = sum(1 for flow in lead_flows if flow >= neutral_threshold)

    
    negative_percentage = round((negative_count / total_count * 100),2) if total_count > 0 else 0
    neutral_percentage = round((neutral_count / total_count * 100),2) if total_count > 0 else 0
    positive_percentage = round((positive_count / total_count * 100),2) if total_count > 0 else 0

    context.update({
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_percentage': negative_percentage,
        'neutral_percentage': neutral_percentage,
        'positive_percentage': positive_percentage,
    })


    


    return render(request, 'leads/my_leads.html', context)



@login_required
def lead_report(request, lead_id):


    today = (tz.localtime(tz.now())).date()
    now = tz.now()
    current_year = now.year
    current_month = now.month


    context = {}

    context['profile'] = Profile.objects.get(user=request.user)

    lead = Lead.objects.get(lead_id=lead_id,active=True)

    if lead.agent_user != request.user:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    context['campaigns'] = Campaign.objects.filter(status="active")
    context['contactlists'] = ContactList.objects.filter(active=True)

    context['lead'] = lead

    context['agent_profile'] = lead.agent_profile
    context['property_types'] = PROPERTY_CHOICES
    context['timelines'] = TIMELINE_CHOICES
    context['lead_status'] = LEAD_CHOICES


    lead_flow = lead.lead_flow_json

    parsed_lead_flow = {}
    for key, value in lead_flow.items():
        parsed_lead_flow[key] = {
            'percentage': abs(value),
            'is_positive': True if value >= 0 else False  # True for positive, False for negative
        }
    context['lead_flow'] = parsed_lead_flow
    
    template = "leads/lead_report_re.html"

    if lead.lead_type == "realestate":

        template = "leads/lead_report_re.html"

    elif lead.lead_type == "roofing":
        template = "leads/lead_report_roofing.html"
    

    if request.method == "POST":

        data = request.POST
        

        total_percentage = data.get('hidden_total_percentage')


        lead = Lead.objects.get(lead_id=lead_id)


        if lead.status == "pending":


            
            

            camp_id = data.get('campaign')
            dialer_list = data.get('dialer_list')
            lead.campaign = Campaign.objects.get(id=camp_id)
            lead.seller_name = data.get('owner_name')
            lead.property_type = data.get('property_type')
            #lead.property_address = data.get('address')
            lead.asking_price = data.get('asking_price')
            lead.market_value = data.get('market_value')
            lead.reason = data.get('reason')
            lead.timeline = data.get('timeline')
            lead.property_url = data.get('zillow_url')
            lead.callback = data.get('callback_time')
            lead.general_info = data.get('general_info')
            lead.extra_notes = data.get('extra_info')





            lead.roof_age = data.get('roof_age')
            lead.appointment_time = data.get('appointment_time')
            lead.known_issues = data.get('known_issues')

            lead.quality_notes = data.get('quality_notes')
            lead.save()
        
        redirect_link = '/my-leads/'+str(current_month)+'-'+str(current_year)
        return redirect(redirect_link)


        
    return render(request, template, context)




@login_required
def leads_quality(request, month, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile


    negative_threshold = settings.negative_percentage
    neutral_threshold = settings.neutral_percentage

    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    leads = Lead.objects.filter(agent_profile=profile,
                    pushed__year=year,
                    pushed__month=month).exclude(status="pending").order_by('-pushed')
    
    context['contacts'] = leads[:10]
    lead_flows = list(leads.values_list('lead_flow', flat=True))
    total_count = len(lead_flows)

    negative_count = sum(1 for flow in lead_flows if flow < negative_threshold)
    neutral_count = sum(1 for flow in lead_flows if negative_threshold <= flow < neutral_threshold)
    positive_count = sum(1 for flow in lead_flows if flow >= neutral_threshold)

    
    negative_percentage = round((negative_count / total_count * 100),2) if total_count > 0 else 0
    neutral_percentage = round((neutral_count / total_count * 100),2) if total_count > 0 else 0
    positive_percentage = round((positive_count / total_count * 100),2) if total_count > 0 else 0

    context.update({
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'positive_count': positive_count,
        'negative_percentage': negative_percentage,
        'neutral_percentage': neutral_percentage,
        'positive_percentage': positive_percentage,
    })
    
    return render(request,'leads/leads_quality.html',context)



@permission_required('lead_scoring')
@login_required
def lead_scoring(request, month, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    # Get the first and last days of the month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    # Get ISO week numbers for the first and last days of the month
    first_week = first_day.isocalendar()[1]
    last_week = last_day.isocalendar()[1]

    # Initialize a dictionary to store total points per week
    weekly_points_count = defaultdict(int)

    # Get leads for the current month and year
    leads = Lead.objects.filter(
        agent_profile=profile,
        status="qualified",
        pushed__year=year,
        pushed__month=month
    )
    
    context['leads'] = leads.order_by("-pushed")
    # Calculate lead points per campaign
    leads_per_campaign = leads.values('campaign').annotate(lead_count=Count('lead_id')).order_by('campaign')
    campaign_leads_count = {
        Campaign.objects.get(pk=item['campaign']).lead_points: item['lead_count']
        for item in leads_per_campaign
    }

    # Sum points for each week
    for lead in leads:
        week_number = lead.pushed.isocalendar()[1]  # Get ISO week number
        lead_points = Campaign.objects.get(pk=lead.campaign_id).lead_points
        weekly_points_count[week_number] += lead_points

    # Ensure that all weeks from first to last are represented
    weeks_in_month = range(first_week, last_week + 1)

    # Prepare list with total points for each week
    weekly_total_points_list = [weekly_points_count.get(week, 0) for week in weeks_in_month]

    # Convert week numbers to "Week 1", "Week 2", etc.
    week_labels = [f"Week {i + 1}" for i in range(len(weeks_in_month))]

    # Update context with week labels and total points per week
    context['week_numbers'] = week_labels
    context['weekly_total_points'] = weekly_total_points_list

    




    return render(request, 'leads/lead_scoring.html', context)



@permission_required('leaderboard')
@login_required
def leads_leaderboard(request, month, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    # Get the first and last days of the month
    callers_list = ['callers', 'sales']
    callers_teams = Team.objects.filter(team_type__in=callers_list)
    
    active_coldcallers = Profile.objects.filter(team__in=callers_teams, active=True)

    # Initialize leaderboard
    leaderboard = []

    # Check for date range query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        # Parse the start and end date
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

   
        
        for agent in active_coldcallers:
            # Fetch qualified leads for the agent within the date range
            if start_date == end_date:
                 qualified_leads_count = Lead.objects.filter(
                    agent_profile=agent,
                    pushed__date=start_date,
                    status="qualified"
                ).count()

            else:
                qualified_leads_count = Lead.objects.filter(
                    agent_profile=agent,
                    pushed__range=[start_date, end_date],
                    status="qualified"
                ).count()

            # Add agent and their total qualified leads to the leaderboard
            leaderboard.append({'agent': agent, 'qualified_leads': qualified_leads_count})
    else:
        # Default to filtering by month and year (original behavior)
        for agent in active_coldcallers:
            # Fetch qualified leads for the agent for the specified month and year
            qualified_leads_count = Lead.objects.filter(
                agent_profile=agent,
                pushed__year=year,
                pushed__month=month,
                status="qualified"
            ).count()

            # Add agent and their total qualified leads to the leaderboard
            leaderboard.append({'agent': agent, 'qualified_leads': qualified_leads_count})

    leaderboard = sorted(leaderboard, key=lambda x: x['qualified_leads'], reverse=True)
    context['leaderboard'] = leaderboard
    context['start_date'] = start_date.date() if start_date else None
    context['end_date'] = end_date.date() if end_date else None


    return render(request, 'leads/leaderboard.html', context)




@permission_required('qa_pending')
@login_required
def quality_pending(request):

    context = {}

    now = tz.now()
    current_year = now.year
    current_month = now.month
    current_month_name = _date(now, "F")
    
    context['year'] = current_year
    context['month_name'] =current_month_name

    


    context['profile'] = Profile.objects.get(user=request.user)
    context['pending_leads'] = Lead.objects.filter(status="pending", active=True).order_by('-pushed')[:10]

    context['qualified'] = Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        status="qualified",
        active=True,
        handled_by=request.user,
        ).count()

    context['disqualified'] = Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        status__in = ["disqualified", "duplicate"],
        active=True,
        handled_by=request.user,
        ).count()

    pending_leads = Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        status="pending",
        active=True
        )
    
    context['pending'] = pending_leads.count()

    context['callback'] = Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        status="callback",
        active=True,
        handled_by=request.user,
        ).count()


    context['total_handled_month'] =  Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        status__in=['qualified','disqualified','duplicated','callback'],
        handled_by=request.user,
        active=True,
        ).count()
    
    context['total_month_all'] =  Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        status__in=['qualified','disqualified','duplicated','callback'],
        active=True,
        ).count()
    
    if context['total_month_all'] == 0:
        context['total_handled_month_perc'] = 0  # or some other default value
    else:
        context['total_handled_month_perc'] = round((context['total_handled_month'] / context['total_month_all']) * 100, 2)


    context['total'] =  Lead.objects.filter(
        pushed__month=current_month,
        pushed__year=current_year,
        active=True,
        handled_by=request.user,
        ).count()
    
    context['total_year'] =  Lead.objects.filter(
        pushed__year=current_year,
        active=True,
        status__in=['qualified','disqualified','duplicated','callback'],
        handled_by=request.user,
        ).count()
    

    def calculate_percentage(part, whole):
        if whole == 0:
            return 0
        return (part / whole) * 100

    qualified_percentage = calculate_percentage(context['qualified'], context['total'])
    disqualified_percentage = calculate_percentage(context['disqualified'], context['total'])
    #pending_percentage = calculate_percentage(context['pending'], context['total'])
    callback_percentage = calculate_percentage(context['callback'], context['total'])

    # Format percentages
    def format_percentage(value):
        return '{:.2f}'.format(value).rstrip('0').rstrip('.')

    context['qualified_perc'] = format_percentage(qualified_percentage)
    context['disqualified_perc'] = format_percentage(disqualified_percentage)
    #context['pending_perc'] = format_percentage(pending_percentage)
    context['callback_perc'] = format_percentage(callback_percentage)

    char_data = []
    for month in range(1, 13):
        total_count = Lead.objects.filter(
            pushed__month=month,
            pushed__year=current_year,
            handled_by=request.user,
            status__in=['qualified','disqualified','duplicated','callback'],
            active=True
        ).count()
        char_data.append(total_count)
    context['char_data'] = char_data


    context['pending_leads'] =  Lead.objects.filter(
        status="pending",
        active=True
        )



    return render(request, "quality/pending_leads.html",context)




@permission_required('qa_lead_reports')
@login_required
def quality_lead_reports(request, month, year):

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


    
    

    context['profile'] = Profile.objects.get(user=request.user)

    context['qualified'] = Lead.objects.filter(
        pushed__year=current_year,
         status="qualified",
        active=True
        ).count()

    context['disqualified'] = Lead.objects.filter(
        pushed__year=current_year,
         status__in=["disqualified","callback"],
        active=True
        ).count()

    
    
    context['duplicated'] = Lead.objects.filter(
        pushed__year=current_year,
         status="duplicated",
        active=True
        ).count()

    
    

    context['total'] =  Lead.objects.filter(
        pushed__year=current_year,
         active=True
        ).count()
    

    

    char_data_qualified = []
    for month in range(1, 13):
        total_count = Lead.objects.filter(
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

    # Adjust for the case where the last day belongs to Week 1 of the next year
    if last_week == 1:
        last_week = 52  # Set last_week to Week 52, avoiding an extra week from the next year



    # Initialize a dictionary to store total leads per week
    weekly_leads_count = defaultdict(int)

    # Get leads for the current month and year
    leads = Lead.objects.filter(
        pushed__year=current_year,
        pushed__month=current_month,
        active=True
    )

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
    


    context['all_leads'] = Lead.objects.filter(active=True        
                                               ,pushed__year=current_year,
                                                pushed__month=current_month).order_by('-pushed')
    
    
    



    return render(request, "quality/lead_reports.html",context)


@permission_required('agents_table')
@login_required
def agent_lead_reports(request, agent_id,month , year ):

    context = {}

    now = tz.now()
    current_year = year
    current_month = month
    current_month_name = _date(now, "F")
    
    context['year'] = current_year
    context['month_name'] =current_month_name
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    


    context['profile'] = Profile.objects.get(user=request.user)

    agent_profile = Profile.objects.get(id=agent_id)
    context['agent_profile'] = agent_profile

    context['agentid'] = agent_profile.id

    context['qualified'] = Lead.objects.filter(
        pushed__year=current_year,
        agent_profile=agent_profile,
        status="qualified",
        active=True
        ).count()

    context['disqualified'] = Lead.objects.filter(
        pushed__year=current_year,
        agent_profile=agent_profile,
        status__in=["disqualified","callback"],
        active=True
        ).count()

    
    
    context['duplicated'] = Lead.objects.filter(
        pushed__year=current_year,
        agent_profile=agent_profile,
        status="duplicated",
        active=True
        ).count()

    
    

    context['total'] =  Lead.objects.filter(
        pushed__year=current_year,
        agent_profile=agent_profile,
        active=True
        ).count()
    

    

    char_data_qualified = []
    for month in range(1, 13):
        total_count = Lead.objects.filter(
            agent_profile=agent_profile,
          
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
            agent_profile=agent_profile,
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
        agent_profile=agent_profile,
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
        agent_profile=agent_profile,
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
    


    context['all_leads'] = Lead.objects.filter(agent_profile=agent_profile,active=True,
                                               pushed__month=current_month,
                                               pushed__year=current_year).order_by('-pushed')
    
    
    



    return render(request, "quality/lead_reports_agent.html",context)



@permission_required('qa_lead_reports')
@login_required
@require_http_methods(["POST"])
def fire_lead(request, lead_id):
    try:
        lead = Lead.objects.get(lead_id=lead_id)
        lead.fireback = True
        lead.save()
        return JsonResponse({'message': 'Lead Fired successfully.'}, status=200)
    except lead.DoesNotExist:
        return JsonResponse({'message': 'Lead not found.'}, status=404)







def get_lead_status(request, lead_id):
    try:
        lead = Lead.objects.get(lead_id=lead_id)
        user_profile = Profile.objects.get(user=request.user)

        if lead.assigned:
            if lead.assigned == user_profile:
                return JsonResponse({'assigned_to_user': True})
            else:
                return JsonResponse({'assigned': True})
        
        if request.method == 'POST':
            lead.assigned = user_profile
            lead.assigned_time = tz.now()
            lead.save()
            return JsonResponse({'assigned': True})

        return JsonResponse({'assigned': False})
    except Lead.DoesNotExist:
        return JsonResponse({'error': 'Lead not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def unassign_lead(request, lead_id):
    try:
        # Fetch the lead and user profile
        lead = get_object_or_404(Lead, lead_id=lead_id)
        user_profile = Profile.objects.get(user=request.user)
        access = user_profile.role.qa_unassign_lead

        # Check if the lead is already assigned to the user
        if access:
            if request.method == 'POST':
                # If confirmed (POST), unassign the lead
                lead.assigned = None
                lead.assigned_time = None
                lead.save()
                return JsonResponse({'message': 'Lead successfully unassigned', 'access': access}, status=200)
            else:
                # If not POST, return a confirmation prompt for unassigning
                return JsonResponse({'message': 'Do you want to unassign this lead?', 'access': access}, status=200)
        else:
            # If the lead is not assigned to the current user
            return JsonResponse({'message': 'You are not allowed to unassign leads', 'access': access}, status=400)

    except Lead.DoesNotExist:
        return JsonResponse({'error': 'Lead not found'}, status=404)
    except Profile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@permission_required('qa_lead_handling')
@login_required
def lead_handling(request, lead_id):

    context = {}

    context['profile'] = Profile.objects.get(user=request.user)
    lead = Lead.objects.get(lead_id=lead_id,active=True)

    if not lead.assigned:
        return HttpResponseForbidden("You do not have permission to access this resource.")

    context['campaigns'] = Campaign.objects.filter(status="active")
    context['contactlists'] = ContactList.objects.filter(active=True)

    context['lead'] = lead

    context['agent_profile'] = lead.agent_profile 
    context['property_types'] = PROPERTY_CHOICES 
    context['timelines'] = TIMELINE_CHOICES
    context['lead_status'] = LEAD_CHOICES

    try:
        lead_flow_slots = LeadHandlingSettings.objects.get(active=True, campaign=lead.campaign)
        context['lead_flow_slots'] = lead_flow_slots.get_active_slots()
    except:
        context['lead_flow_slots'] = None



    lead_flow = lead.lead_flow_json

    parsed_lead_flow = {}
    for key, value in lead_flow.items():
        parsed_lead_flow[key] = {
            'percentage': abs(value),
            'is_positive': True if value >= 0 else False  # True for positive, False for negative
        }
    context['lead_flow'] = parsed_lead_flow
    

    template = "quality/lead_handling_re.html"

    if lead.lead_type == "realestate":
        template = "quality/lead_handling_re.html"
    elif lead.lead_type == "roofing":
        template = "quality/lead_handling_roofing.html"

    if request.method == "POST":
        data = request.POST
        """slot_json = {}
        lead_flow_slots =lead_flow_slots.get_active_slots()
        for i in range(1, len(lead_flow_slots) + 1):
            slot_name = request.POST.get(f'slot{i}_name')
            slot_percentage = request.POST.get(f'slot{i}_percentage')
            # Ensure that slot_name is not empty and slot_percentage is not None
            if slot_name:
                # Access slot names directly from the dictionary
                slot_json[lead_flow_slots[i-1]['name']] = slot_percentage
        # Print or use the slot_dict as needed"""


        slot_json = {}
        lead_flow_slots = lead_flow_slots.get_active_slots()

        for i in range(1, len(lead_flow_slots) + 1):
            slot_name = request.POST.get(f'slot{i}_name')
            slot_percentage = request.POST.get(f'slot{i}_percentage')
            
            # Ensure that slot_name is not empty and slot_percentage is not None
            if slot_name and slot_percentage is not None:
                # Convert slot_percentage to float and make it negative if slot_name is '0'
                percentage_value = float(slot_percentage)
                if slot_name == '0':
                    percentage_value = -percentage_value
                
                # Access slot names directly from the dictionary
                slot_json[lead_flow_slots[i-1]['name']] = percentage_value

        # Print or use the slot_json as needed


        total_percentage = data.get('hidden_total_percentage')


        lead = Lead.objects.get(lead_id=lead_id)


        insurance = data.get('insurance')
        contractor = data.get('contractor')
        deductible = data.get('deductible')
        
        if str(insurance) == "yes":
            insurance = True
        elif str(insurance) == "no":
            insurance = False
        else:
            insurance = False

        if str(contractor) == "yes":
            contractor = True
        elif str(contractor) == "no":
            contractor = False
        else:
            contractor = False

        if str(deductible) == "yes":
            deductible = True
        elif str(deductible) == "no":
            deductible = False
        else:
            deductible = False
        
        dialer_list = data.get('dialer_list')

        lead.seller_name = data.get('owner_name')
        lead.seller_phone = data.get('phone_number')
        lead.seller_email = data.get('email')
        lead.property_type = data.get('property_type')
        #lead.property_address = data.get('address')
        lead.asking_price = data.get('asking_price')
        lead.market_value = data.get('market_value')
        lead.reason = data.get('reason')
        lead.timeline = data.get('timeline')
        lead.property_url = data.get('zillow_url')
        lead.callback = data.get('callback_time')
        lead.general_info = data.get('general_info')
        lead.extra_notes = data.get('extra_info')

        lead.insurance = insurance
        lead.contractor = contractor
        lead.deductible = deductible
        lead.roof_age = data.get('roof_age')
        lead.appointment_time = data.get('appointment_time')
        lead.known_issues = data.get('known_issues')


        lead.quality_notes = data.get('quality_notes')
        lead.lead_flow = float(total_percentage)
        lead.status = data.get('lead_status')
        lead.handled_by = request.user
        lead.lead_flow_json = slot_json
        lead.handled = tz.now()
        if not lead.handling_time:
            handling_time = tz.now() - lead.assigned_time
            lead.handling_time = handling_time
        lead.save()

        return redirect('/quality-pending')


        
    return render(request, template, context)


@permission_required('qa_auditing')
@login_required
def feedbacks_table(request):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['feedbacks'] = Feedback.objects.filter(active=True).order_by('-created')


    return render(request,'quality/feedbacks.html',context)

@permission_required('agents_table')
@login_required
def feedbacks_agent(request, agent_id):

    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    agent_profile = Profile.objects.get(id=agent_id)
    context['agent_profile'] = agent_profile
    context['feedbacks'] = Feedback.objects.filter(agent_profile=agent_profile, active=True).order_by('-created')


    return render(request,'quality/feedbacks.html',context)


@permission_required('qa_auditing')
@login_required
def feedback_single(request):


    context = {}
    profile = Profile.objects.get(user=request.user)


    context['profile'] = profile
    context['campaigns'] = Campaign.objects.filter(active=True)
    context['agent_profiles'] = Profile.objects.filter(active=True)



    if request.method == "POST":
        data = request.POST

        agent_id = data.get('agent')
        feedback_type = data.get('feedback_type')
        feedback_text = data.get('feedback_text')
        selected_camp_ids = data.getlist('campaigns')

        if int(feedback_type) == 1:
            feedback_type = "positive"
        elif int(feedback_type) == 2:
            feedback_type = "negative"
        
        elif int(feedback_type) == 3:
            feedback_type = "neutral"

        agent_profile = Profile.objects.get(id=agent_id)
        camps = Campaign.objects.filter(id__in=selected_camp_ids)

        feedback = Feedback.objects.create(agent=agent_profile.user,
                                agent_profile=agent_profile,
                                auditor=profile.user,
                                auditor_profile=profile,
                                feedback_type=feedback_type,
                                type="single",
                                feedback_text = feedback_text,

                                )
        feedback.campaign.add(*camps)

        return redirect('/feedbacks')

            
    
    return render(request,'quality/feedback_multiple.html',context)


@permission_required('qa_auditing')
@login_required
def feedback_monthly(request):


    context = {}
    profile = Profile.objects.get(user=request.user)


    context['profile'] = profile
    context['campaigns'] = Campaign.objects.filter(active=True)
    context['agent_profiles'] = Profile.objects.filter(active=True)



    if request.method == "POST":
        data = request.POST

        agent_id = data.get('agent')
        feedback_type = data.get('feedback_type')
        feedback_text = data.get('feedback_text')
        selected_camp_ids = data.getlist('campaigns')

        if int(feedback_type) == 1:
            feedback_type = "positive"
        elif int(feedback_type) == 2:
            feedback_type = "negative"
        
        elif int(feedback_type) == 3:
            feedback_type = "neutral"

        agent_profile = Profile.objects.get(id=agent_id)
        camps = Campaign.objects.filter(id__in=selected_camp_ids)

        feedback = Feedback.objects.create(agent=agent_profile.user,
                                agent_profile=agent_profile,
                                auditor=profile.user,
                                auditor_profile=profile,
                                feedback_type=feedback_type,
                                type="single",
                                feedback_text = feedback_text,

                                )
        feedback.campaign.add(*camps)
    

        return redirect('/feedbacks')

            
    
    return render(request,'quality/feedback_multiple.html',context)



@permission_required('qa_auditing_handling')
@login_required
def feedback_report(request, id):


    context = {}
    profile = Profile.objects.get(user=request.user)


    context['profile'] = profile
    context['agent_profiles'] = Profile.objects.filter(active=True)
    context['feedback'] = Feedback.objects.get(id=id)
    context['feedback_status_choices'] = FEEDBACK_STATUS_CHOICES

    if request.method == "POST":
        data = request.POST
        feedback_id = data.get('feedback_id')
        feedback_status = data.get('feedback_status')
        trainer_text = data.get('trainer_text')

        
        feedback = Feedback.objects.get(id=id)
        feedback.status = feedback_status
        feedback.trainer_text = trainer_text
        feedback.save()
        return redirect('/feedbacks')

            
    
    return render(request,'quality/feedback_report.html',context)


@permission_required('qa_agents_table')
@login_required
def quality_agents(request, month, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile





    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    # Get the first and last days of the month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    # Get ISO week numbers for the first and last days of the month
    first_week = first_day.isocalendar()[1]
    last_week = last_day.isocalendar()[1]

    # Adjust for the case where the last day belongs to Week 1 of the next year
    if last_week < first_week:  # Week rollover
        last_week = 52  # Cap it to the last valid ISO week for the year

    # Initialize a dictionary to store the count of qualified leads per week
    weekly_leads_count = defaultdict(int)

    # Get leads for the current month and year
    leads = Lead.objects.filter(
        status="qualified",
        pushed__year=year,
        pushed__month=month
    )

    # Count leads per week
    for lead in leads:
        week_number = lead.pushed.isocalendar()[1]  # Get ISO week number
        weekly_leads_count[week_number] += 1

    # Ensure that all weeks from first to last are represented
    weeks_in_month = range(first_week, last_week + 1)


    # Prepare list with total leads count for each week
    weekly_total_leads_list = [weekly_leads_count.get(week, 0) for week in weeks_in_month]

    # Convert week numbers to "Week 1", "Week 2", etc.
    week_labels = [f"Week {i + 1}" for i in range(len(weeks_in_month))]

    # Update context with week labels and total leads per week
    context['week_numbers'] = week_labels
    context['weekly_total_leads'] = weekly_total_leads_list


    quality_teams = Team.objects.filter(team_type="quality")

    qa_reports = {}

    qa_agents = Profile.objects.filter(team__in=quality_teams)

    # Loop through each QA agent
    for qa_agent in qa_agents:
        # Aggregate leads data for the current QA agent
        aggregated_data = Lead.objects.filter(
            handled_by=qa_agent.user,
            pushed__year=year,
            pushed__month=month
        ).aggregate(
            qualified_count=Count('lead_id', filter=Q(status='qualified')),
            disqualified_count=Count('lead_id', filter=Q(status='disqualified')),
            handling_time_avg=Avg('handling_time'),
            total_leads_count=Count('lead_id'),
            fireback_count=Count('lead_id', filter=Q(fireback=True))
        )
        
        # Format the average handling time
        formatted_handling_time_avg = format_timedelta(aggregated_data['handling_time_avg'])
        
        # Store the results in the dictionary
        qa_reports[qa_agent] = {
            'qualified_count': aggregated_data['qualified_count'],
            'disqualified_count': aggregated_data['disqualified_count'],
            'handling_time_avg': formatted_handling_time_avg,
            'total_leads_count': aggregated_data['total_leads_count'],
            'fireback_count': aggregated_data['fireback_count']
        }

    context['qa_reports'] = qa_reports






    return render(request, 'quality/quality_agents.html', context)




def application_form(request):

    context = {}
    try:
        context['profile'] = Profile.objects.get(user=request.user)
    except:
        pass

    context['discovery_options'] = APPLICATION_DISCOVERY

    return render(request, 'applications/application_form.html', context)

@csrf_exempt
def handle_audio_upload(request):
    if request.method == 'POST': #and request.FILES.get('audio_data'):

        try:
            audio_file = request.FILES['audio_data']
        except:
            audio_file = None
        
        
        

        try:
            # Example code to save file to media root

            phone = request.POST.get('full_phone_number')

            
            
            new_application = Application(phone=phone)
            #new_application.app_uuid = submitted_uuid  # Store the UUID
            new_application.full_name = request.POST.get('full_name')
            new_application.audio_file = audio_file
            new_application.position = request.POST.get('position')
            new_application.phone = request.POST.get('phone_number')
            new_application.email = request.POST.get('email')
            new_application.education = request.POST.get('education')
            new_application.start_date = request.POST.get('start_date')
            new_application.shift = request.POST.get('shift')
            new_application.experience = request.POST.get('previous_experience')
            new_application.app_discovery = request.POST.get('discovery')
            new_application.recording_link = request.POST.get('recording_external')

            # Save the dynamic field value (recruiter name or "other" source)
            discovery_method = request.POST.get('discovery')
            if discovery_method in ['recruiter', 'other']:
                new_application.discovery_details = request.POST.get('dynamic_field')

            new_application.save()

            app = new_application

            utc_now = datetime.utcnow()

            # Get the timezone object for 'America/New_York'
            est_timezone = pytz.timezone('America/New_York')

            # Convert UTC time to Eastern timezone
            est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

            # Format the time as HH:MM:SS string
            est = est_time.strftime('%I:%M:%S %p')

            # Construct the content of the embed with quote formatting
            request_ip = request.META.get('REMOTE_ADDR')

            content = f'\n**APPLICATION**\n\n\n**Applicant:** {app.full_name}\n\n**Position:** {app.get_position_display()}\n\n**Can Start on:** {app.start_date}\n\n**Shift:** {app.get_shift_display()}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}  '
            
            try:
                send_discord_message_application(content,app.id)
            except:
                pass
            
            return redirect('/application-success')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'No audio file found.'}, status=400)




@csrf_exempt
def check_duplicate_application(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if phone_number:
            existing_app = Application.objects.filter(phone=phone_number).order_by('-submission_date').first()
            if existing_app:

                # Make sure datetime.now() is timezone-aware
                now = tz.now()

                # Subtracting timezone-aware datetime objects
                time_difference = now - existing_app.submission_date
                minutes_ago = int(time_difference.total_seconds() // 60)
                hours_ago = minutes_ago // 60
                days_ago = hours_ago // 24

                time_message = (
                    f"{days_ago} days ago" if days_ago > 0 else
                    f"{hours_ago} hours ago" if hours_ago > 0 else
                    f"{minutes_ago} minutes ago"
                )
                return JsonResponse({
                    'exists': True,
                    'time_message': time_message
                })

        return JsonResponse({'exists': False})
    return JsonResponse({'error': 'Invalid request method'}, status=400)




def application_success(request):

    return render(request, 'statuses/application_200.html')

@login_required
def upload_profile(request):
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            # Check if the uploaded file is an image
            if file.content_type.startswith('image'):
                # Example: Save the file to a Profile model instance
                profile = Profile.objects.get(user=request.user)  # Adjust based on your profile retrieval logic
                profile.picture = file
                profile.save()
                return JsonResponse({'message': 'Image uploaded successfully.'})
            else:
                return JsonResponse({'error': 'File is not an image.'}, status=400)
        else:
            return JsonResponse({'error': 'File not provided.'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@login_required
def account_settings(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile


    return render(request,'users/settings.html', context)


@require_POST
def update_theme(request):
    data = json.loads(request.body)
    theme = data.get('theme')

    if theme == "dark":
        profile = Profile.objects.get(user=request.user)
        profile.settings_theme = "dark"
        profile.save()
    elif theme == "white":
        profile = Profile.objects.get(user=request.user)
        profile.settings_theme = "white"
        profile.save()

    return JsonResponse({'message': f'Theme updated to {theme}'})


@require_POST
def maps_theme(request):
    data = json.loads(request.body)
    theme = data.get('theme')

    if theme == "dark":
        profile = Profile.objects.get(user=request.user)
        profile.maps_theme = "dark"
        profile.save()
    elif theme == "white":
        profile = Profile.objects.get(user=request.user)
        profile.maps_theme = "white"
        profile.save()

    return JsonResponse({'message': f'Theme updated to {theme}'})


def payment_info(request):
    if request.method == 'POST':
        data = request.POST
        payoneer_account = data.get('payoneer_account')
        instapay_account = data.get('instapay_account')
        payoneer_choice = data.get('payoneer_choice')
        instapay_choice = data.get('instapay_choice')

        profile = Profile.objects.get(user=request.user)
        if profile.payoneer != payoneer_account:
            profile.payoneer = payoneer_account
        if profile.instapay != instapay_account:
            profile.instapay = instapay_account
        if payoneer_choice == "on":
            profile.payment_method = "payoneer"
        elif instapay_choice == "on":
            profile.payment_method = "instapay"
        else:
            return redirect('/')
        profile.save()
    return redirect('/settings')




def address_autocomplete(request):

    if 'term' in request.GET:
        term = request.GET.get('term')
        HERE_API = django_settings.HERE_API
        url = f'https://autocomplete.geocoder.ls.hereapi.com/6.2/suggest.json?query={term}&apiKey={HERE_API}&country=USA'
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            suggestions = [item['label'] for item in data.get('suggestions', [])]
            return JsonResponse(suggestions, safe=False)
        else:
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)



ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'dot': 'application/msword',  # Older Word templates
    'dotx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template',  # Word template
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
    'avi': 'video/x-msvideo',
    'zip': 'application/zip',
    'rar': 'application/vnd.rar',
    # Add more video extensions if needed
}


MAX_FILE_SIZE_MB = 7

def validate_file(file):
    # Check file size
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"File size exceeds {MAX_FILE_SIZE_MB} MB limit.")
    
    # Check file extension
    extension = file.name.split('.')[-1].lower()
    content_type = file.content_type
    
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("Unsupported file type.")
    
    # Check content type
    if content_type != ALLOWED_EXTENSIONS.get(extension):
        raise ValidationError("File type does not match its extension.")
   



@permission_required('leave_request')
@csrf_exempt
@login_required
def leave_request(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['leave_types'] = LEAVE_CHOICES

    if request.method == "POST":
        data = request.POST
        file = None
        agent_profile = Profile.objects.get(user=request.user)
        leave_type = data.get('leave_type')
        requested_date = data.get('requested_date')
        reason = data.get('reason')
 
        

        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                validate_file(file)
                
            except ValidationError as e:
                file= None

        # Create Leave instance with or without the file
        leave = Leave.objects.create(
            agent_user=request.user,
            agent_profile=agent_profile,
            agent_name=agent_profile.full_name,
            team=agent_profile.team,
            leave_type=leave_type,
            requested_date=requested_date,
            reason=reason,
            file=file if file else None  # Assign file only if it exists
        )


        request_ip = request.META.get('REMOTE_ADDR')

        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')

        content = f'**Agent:** {profile.full_name}\n\n**Action:** Requested a Leave on **[{leave.requested_date}]**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}  '
        try:
            send_discord_message_requests(content,leave.id,'leave')
        except:
            pass

    
        

        return redirect('/leave-requests')
    return render(request,'requests/leave.html', context)


@permission_required('leave_request')
@login_required
def leave_request_list(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['leaves'] = Leave.objects.filter(active=True, agent_user=request.user).order_by('-submission_date')
    context['profile'] = profile

    return render(request,'requests/leaves_list.html', context)

@require_http_methods(["DELETE"])
def delete_leave(request, leave_id):
    try:
        leave = Leave.objects.get(id=leave_id)
        if leave.status == "pending":

            leave.delete()
            return JsonResponse({'message': 'Leave deleted successfully.'}, status=200)
        else:
            return JsonResponse({'message': 'You Can not Delete a Handled Request.'}, status=403)

    except Leave.DoesNotExist:
        return JsonResponse({'message': 'Leave not found.'}, status=404)





@permission_required('leave_handling')
@login_required
def leave_handling_list(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['leaves'] = Leave.objects.filter(active=True).order_by('-submission_date')
    context['profile'] = profile

    return render(request,'requests/leaves_list_handling.html', context)


@permission_required('leave_handling')
@login_required
def leave_report(request, leave_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['leave_types'] = LEAVE_CHOICES
    context['leave_status'] = REQUESTS_STATUS_CHOICES
    context['leave'] = Leave.objects.get(id=leave_id)
    context['teams'] = Team.objects.filter(active=True)

    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        leave_type = data.get('leave_type')
        requested_date = data.get('requested_date')
        reason = data.get('reason')
        status = data.get('leave_status')
 
        
        leave = Leave.objects.get(id=leave_id)

        
        leave.leave_type=leave_type
        leave.requested_date=requested_date
        leave.reason=reason
        leave.status=status
        leave.handled_by=request.user
        leave.save()
        if status == "approved":
            absence = Absence.objects.create(
                team = agent_profile.team,
                reporter = request.user,
                reporter_profile = agent_profile,
                agent = leave.agent_user,
                agent_profile=leave.agent_profile,

                absence_date = requested_date,
                absence_type = leave_type,
                notes = reason,
            )
            
        

        return redirect('/leave-handling')
    return render(request,'requests/leave_report.html', context)






@permission_required('action_request')
@csrf_exempt
@login_required
def action_request(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['action_types'] = ACTION_CHOICES

    if request.method == "POST":
        data = request.POST
        file = None
        userid = int(data.get('agentid'))
        agent_profile = Profile.objects.get(id=userid)
        action_type = data.get('action_type')
        incident_date = data.get('incident_date')
        deduction_amount = data.get('amount')
        reason = data.get('reason')
 
        

        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                validate_file(file)
                # Process file (save to database, etc.)
                # Example: save the file
                # YourModel.objects.create(file=file)
                pass
            except ValidationError as e:
                file = None

        # Create Leave instance with or without the file
        action = Action.objects.create(
            accuser=request.user,
            accuser_profile= Profile.objects.get(user=request.user),
            agent= agent_profile.user,
            agent_profile = agent_profile,
            action_type=action_type,
            incident_date=incident_date,
            deduction_amount=deduction_amount,
            reason=reason,
            file=file if file else None  # Assign file only if it exists
        )

        request_ip = request.META.get('REMOTE_ADDR')
        
        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')
 
        content = f'**Agent:** {profile.full_name}\n\n**Action:** Requested an Action  on **{action.agent_profile.full_name}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '
        try:
            send_discord_message_requests(content,action.id,'action')
        except:
            pass

        return redirect('/action-requests')
    return render(request,'requests/action.html', context)


@permission_required('action_request')
@login_required
def action_request_list(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['actions'] = Action.objects.filter(active=True, accuser=request.user).order_by('-submission_date')
    context['profile'] = profile

    return render(request,'requests/actions_list.html', context)



@require_http_methods(["DELETE"])
def delete_action(request, action_id):
    try:
        action = Action.objects.get(id=action_id)
        if action.status == "pending":

            action.delete()
            return JsonResponse({'message': 'Action deleted successfully.'}, status=200)
        else:
            return JsonResponse({'message': 'You Can not Delete a Handled Request.'}, status=403)
    except Action.DoesNotExist:
        return JsonResponse({'message': 'Action not found.'}, status=404)





@permission_required('action_handling')
@login_required
def action_handling_list(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['actions'] = Action.objects.filter(active=True).order_by('-submission_date')
    context['profile'] = profile

    return render(request,'requests/action_list_handling.html', context)


@permission_required('action_handling')
@login_required
def action_report(request, action_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['action_types'] = ACTION_CHOICES
    context['action_status'] = REQUESTS_STATUS_CHOICES
    context['action'] = Action.objects.get(id=action_id)

    
    if request.method == "POST":
        data = request.POST
        action = Action.objects.get(id=action_id)
        userid = (action.agent_profile).id
        agent_profile = Profile.objects.get(id=userid)
        action_type = data.get('action_type')
        incident_date = data.get('incident_date')
        deduction_amount = data.get('amount')
        status = data.get('action_status')
        reason = data.get('reason')
 
        
        action = Action.objects.get(id=action_id)

        action.agent_user=request.user
        action.agent_profile=agent_profile
        action.agent_name=agent_profile.full_name
        action.team=agent_profile.team
        action.action_type=action_type
        action.incident_date=incident_date
        action.deduction_amount = deduction_amount
        action.reason=reason
        action.status=status
        action.handled_by=request.user
        action.save()
        

        return redirect('/action-handling')
    return render(request,'requests/action_report.html', context)






@permission_required('prepayment_request')
@login_required
def prepayment_request(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        timeframe = data.get('timeframe')
        amount = data.get('amount')
        payment_account = data.get('payment_account')
        reason = data.get('reason')

        

        

        # Create Leave instance with or without the file
        prepayment = Prepayment.objects.create(
            agent=request.user,
            agent_profile=agent_profile,
            timeframe=timeframe,
            amount=amount,
            payment_account=payment_account,
        )

        request_ip = request.META.get('REMOTE_ADDR')
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        utc_now = datetime.utcnow()
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')
        mention4 = f'<@979421026976927785>'

        requestid = prepayment.id
        content = f'**Agent:** {profile.full_name}\n\n**Action:** Requested a prepayment\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '
        try:
            send_discord_message_prepayment(content,requestid) 
        except:
            pass

    
        

        return redirect('/prepayment-requests')
    return render(request,'requests/prepayment.html', context)


@permission_required('prepayment_request')
@login_required
def prepayment_request_list(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['prepayments'] = Prepayment.objects.filter(active=True, agent=request.user).order_by('-submission_date')
    context['profile'] = profile

    return render(request,'requests/prepayments_list.html', context)

@require_http_methods(["DELETE"])
def delete_prepayment(request, prepayment_id):
    try:
        prepayment = Prepayment.objects.get(id=prepayment_id)
        if prepayment.status == "pending":

            prepayment.delete()
            return JsonResponse({'message': 'Prepayment deleted successfully.'}, status=200)
        else:
            return JsonResponse({'message': 'You Can not Delete a Handled Request.'}, status=403)
    except Prepayment.DoesNotExist:
        return JsonResponse({'message': 'Prepayment not found.'}, status=404)





@permission_required('prepayment_handling')
@login_required
def prepayment_handling_list(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['prepayments'] = Prepayment.objects.filter(active=True).order_by('-submission_date')
    context['profile'] = profile

    return render(request,'requests/prepayments_list_handling.html', context)


@permission_required('prepayment_handling')
@login_required
def prepayment_report(request, prepayment_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['prepayment_status'] = REQUESTS_STATUS_CHOICES
    context['prepayment'] = Prepayment.objects.get(id=prepayment_id)

    if request.method == "POST":
        data = request.POST
        amount = data.get('amount')
        status = data.get('prepayment_status')
 
        
        prepayment = Prepayment.objects.get(id=prepayment_id)


        prepayment.amount=amount
        prepayment.status=status
        prepayment.handled_by=request.user
        prepayment.save()
       
            
        

        return redirect('/prepayments-handling')
    return render(request,'requests/prepayment_report.html', context)












@permission_required('dialer_reports')
@login_required
def dialer_report(request, camp_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    campaign = Campaign.objects.get(id=camp_id)

    context['campaign'] = campaign
    context['camp_id'] = campaign.id

    today_date = tz.now().date()

    context['today_date'] = today_date  
    context['month'] = tz.now().month
    context['year'] = tz.now().year
    api_key = campaign.dialer_api_key
    dialer_type = campaign.dialer_type
    dialer_type_display = campaign.get_dialer_type_display()

    date= (tz.localtime(tz.now())).date()


    start_date = request.GET.get('start', str(today_date))  # Default to today if not provided
    end_date = request.GET.get('end', str(today_date))  # Default to today if not provided

    context['start_date'] = start_date
    context['end_date'] = end_date

    if dialer_type == "batchdialer":


        payload = {
            "daterange": {
                "from": start_date+"T06:00:00-05:00",  # Start time 11 AM Eastern Time
                "to": end_date+"T23:59:00-05:00"    # End time 11:59 PM Eastern Time
            }
        }

        headers = {
            'X-ApiKey': api_key, 
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        url = "https://app.batchdialer.com/api/report/public/agents"

        totals = {
            'answered': 0,
            'callsduration': 0,
            'totaltime': 0,
            'presences': {
                'After Call': 0,
                'Auto Pause': 0,
                'Available': 0,
                'Break': 0,
                'In Meeting': 0,
                'In training': 0,
                'Lunch': 0,
                'On Call': 0,
                'Out of desk': 0,
                'PrepWork': 0,
                'Wrap Up Time': 0
            },
            'appointments': 0,
            'leads': 0,
            'answering_machine': 0,
            'abandoned': 0,
            'callstotal': 0
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            api_unsorted = response.json()
            api_response = sorted(api_unsorted, key=lambda x: x['presences']['Available'], reverse=True)
            for agent in api_response:
                totals['answered'] += agent.get('answered', 0)
                totals['callsduration'] += agent.get('callsduration', 0)
                totals['totaltime'] += agent.get('totaltime', 0)
                totals['appointments'] += agent.get('appointments', 0)
                totals['leads'] += agent.get('leads', 0)
                totals['answering_machine'] += agent.get('answering_machine', 0)
                totals['abandoned'] += agent.get('abandoned', 0)
                totals['callstotal'] += agent.get('callstotal', 0)

                for key, value in agent.get('presences', {}).items():
                    totals['presences'][key] += value
            context['totals'] = totals
            context['response'] = api_response
        else:
            api_response = "ERROR"

        return render(request,'dialer_reports/dialer_report_batch.html', context)
    
    elif "calltools" in  dialer_type:


        url = f'https://{dialer_type_display}/api/agentperformance/?startDate={start_date}&endDate={end_date}'

        token = campaign.dialer_api_key
        
        # Set the headers with the API key included
        headers = {
            'accept': 'application/json',
            'Authorization': f'Token {token}',  # 6534a0b1d0f324d09f15fd8a18a3a8dbcd15d734 with the actual key
        }



        # Make the GET request
        response = requests.get(url, headers=headers)


        # Check if the request was successful
        api_response = []
        totals = {
                'calls_duration': 0,
                'available': 0,
                'on_call': 0,
                'post_call': 0,
                'meeting': 0,
                'not_available': 0,
                'break': 0,
                'lunch': 0,
            }
        if response.status_code == 200:
            # Parse and print the JSON response
            data = response.json()



            for record in data['records']:
                agent_info = {
                    'full_name': record['Full Name'],
                    'calls_duration': safe_get(record, 'Call Duration'),
                    'available':safe_get(record, 'Agent Status:Available'),
                    'on_call':safe_get(record, 'Agent Status:On A Call'),
                    'post_call':safe_get(record, 'Agent Status:Post Call'),
                    'meeting':safe_get(record, 'Agent Status:Meeting'),
                    'not_available':safe_get(record, 'Agent Status:Not Available'),
                    'break':safe_get(record, 'Agent Status:Break'),
                    'lunch':safe_get(record, 'Agent Status:Lunch'),




                }
                api_response.append(agent_info)

                totals['calls_duration'] += agent_info['calls_duration']
                totals['available'] += agent_info['available']
                totals['on_call'] += agent_info['on_call']
                totals['post_call'] += agent_info['post_call']
                totals['meeting'] += agent_info['meeting']
                totals['not_available'] += agent_info['not_available']
                totals['break'] += agent_info['break']
                totals['lunch'] += agent_info['lunch']



                """
                dispo_info = {}

                full_name = ""  # Initialize full_name variable

                # Iterate through each key-value pair in the record
                for key, value in record.items():

                    if key == "Full Name":
                        # Save the full name
                        full_name = value
                        dispo_info["full_name"] = full_name

                    if key.startswith("Call Dispo:") and "/Hr" not in key:
                        # Save the Call Dispo variable with its key
                        new_key = key.replace("Call Dispo:", "").strip()  # Remove prefix and strip spaces
                        dispo_info[new_key] = value

                        # Calculate totals
                        

                # Append full_name to the dispo_info dictionary
                    

                # Append the populated dispo_info to the response list
                api_response2.append(dispo_info)

                """

        else:
            api_response = "ERROR"

        context['response'] = api_response
        context['totals'] = totals





        return render(request,'dialer_reports/dialer_report_ct.html', context)





def safe_get(record, key):
    try:
        return record[key]
    except KeyError:
        return 0



def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"







@csrf_exempt
@login_required
def heartbeat_view(request):
    user = request.user
    # Trigger the user_heartbeat_signal to update last seen timestamp
    user_heartbeat_signal.send(sender=None, user=user, request=request)
    return JsonResponse({'status': 'ok'})




@permission_required('work_status')
@login_required
def update_status(request):
    new_status = request.POST.get('status')
    user = request.user
    today = (tz.localtime(tz.now())).date()
    
    profile = Profile.objects.get(user=user)

    if new_status in dict(WorkStatus.STATUS_CHOICES).keys():
        duration = None
        try:
            work_status, created = WorkStatus.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'current_status': new_status,
                    'last_status_change': tz.now()
                }
            )
            previous_status = work_status.current_status
            duration = work_status.get_current_duration()

            work_status.update_status(new_status)


            """
            if new_status == 'offline':
                    try:
                        seat = profile.assigned_credentials
                        
                        if seat:
                            # Update the SeatAssignmentLog to end the session
                            SeatAssignmentLog.objects.filter(
                                agent_profile=profile,
                                dialer_credentials=seat,
                                end_time__isnull=True
                            ).update(end_time=timezone.now())

                            # Clear the seat assignment for both the agent and the seat
                            
                    except DialerCredentials.DoesNotExist:
                        pass  # Handle the case where the agent does not have an assigned seat
            else:
                
                try:
                    seat = profile.assigned_credentials

                    SeatAssignmentLog.objects.filter(
                                agent_profile=profile,
                                dialer_credentials=seat,
                                end_time__isnull=True
                            ).update(end_time=timezone.now())
                    

                    SeatAssignmentLog.objects.create(
                        agent_profile=profile,
                        dialer_credentials=seat,
                        start_time=timezone.now()
                    )
                except DialerCredentials.DoesNotExist:
                    pass
            """


            # Calculate updated total times in seconds
            ready_time_seconds = work_status.ready_time.total_seconds()
            meeting_time_seconds = work_status.meeting_time.total_seconds()
            break_time_seconds = work_status.break_time.total_seconds()
            offline_time_seconds = work_status.offline_time.total_seconds()
            login_time = str((work_status.get_login_time_in_timezone()).strftime('%I:%M %p'))
            # Format times


            

            utc_now = datetime.utcnow()

            # Get the timezone object for 'America/New_York'
            est_timezone = pytz.timezone('America/New_York')

            # Convert UTC time to Eastern timezone
            est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

            # Format the time as HH:MM:SS string
            est = est_time.strftime('%I:%M:%S %p')

            # Construct the content of the embed with quote formatting
            request_ip = request.META.get('REMOTE_ADDR')
            
            """if started_shift == "offline":
                content = f'**Agent:** {profile.full_name}\n\n**Action:** Started Shift **{new_status.upper()}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'

            else:"""
            content = f'**Agent:** {profile.full_name}\n\n**Action:** Changed Working Status  **{previous_status.upper()}** > **{new_status.upper()}**\n\n**Duration:** {str(duration).upper()}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'

            try:
                send_discord_message_activity(content,new_status)
            except:
                pass


            def format_duration(seconds):
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            


            

            # Prepare response
            response_data = {
                'success': True,
                'new_status': new_status,
                'login_time':login_time,
                'ready_time': format_duration(ready_time_seconds),
                'meeting_time': format_duration(meeting_time_seconds),
                'break_time': format_duration(break_time_seconds),
                'offline_time': format_duration(offline_time_seconds),
                'last_status_change': work_status.last_status_change.isoformat()
            }
            return JsonResponse(response_data)
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid status.'})







@login_required
def work_status_data(request):
    today = (tz.localtime(tz.now())).date()
    user = request.user
    
    try:
        work_status = WorkStatus.objects.get(user=user, date=today)
    except WorkStatus.DoesNotExist:
        try:
            work_status = WorkStatus.objects.create(user=user, date=today, current_status='offline')
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)

    # Calculate total times in seconds
    ready_time_seconds = work_status.ready_time.total_seconds()
    meeting_time_seconds = work_status.meeting_time.total_seconds()
    break_time_seconds = work_status.break_time.total_seconds()
    try:
        login_time = str((work_status.get_login_time_in_timezone()).strftime('%I:%M %p'))
    except:
        login_time = "00:00:00"

    data = {
        'login_time':login_time,
        'current_status': work_status.current_status,
        'ready_time': ready_time_seconds,
        'meeting_time': meeting_time_seconds,
        'break_time': break_time_seconds,
        'last_status_change': work_status.last_status_change.isoformat(),
    }
    return JsonResponse(data)