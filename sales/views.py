from django.shortcuts import render, redirect
from core.models import *
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone as tz
from django.db.models import Count
from django.views.decorators.http import require_POST
from datetime import datetime,timedelta
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views import View
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
import calendar
import json
from collections import defaultdict
from core.decorators import *

import pytz

from discord_app.views import send_discord_message_sales_lead

# Create your views here.



@permission_required('sales_dashboard')
@login_required
def sales_dashboard(request, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['year'] = year

    sales_leads = SalesLead.objects.filter(active=True, pushed__year=year)

    # Create a dictionary to hold lists of sales leads for each status choice
    sales_lead_grouped = {choice[0]: [] for choice in SALES_LEAD_CHOICES}  # Initialize with empty lists

    # Iterate over each sales lead and group by status
    for lead in sales_leads:
        sales_lead_grouped[lead.status].append(lead)

    # Prepare the context with grouped sales leads
    context['sales_leads'] = sales_lead_grouped

    # Include the names of the statuses in your context as well
    context['sales_lead_choices'] = dict(SALES_LEAD_CHOICES)



   

    return render(request, 'sales/dashboard.html', context)



@permission_required('sales_lookerstudio')
@login_required
def sales_lookerstudio(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['lookerstudio'] = ServerSetting.objects.first().sales_lookerstudio

    return render(request, 'sales/lookerstudio.html', context)




@permission_required('sales_performance')
@login_required
def sales_calendar(request, month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()

    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date

    statuses = ['follow_up', 'scheduled_meeting','follow_up_landing' , 'send_contract', 'longterm_follow_up']
    context['sales_leads'] = SalesLead.objects.filter(status__in=statuses,followup_date__year=year, active=True)

    leads_count = SalesLead.objects.filter(
        active=True,
        followup_date__month=month,
        followup_date__year=year,status__in=statuses,
    ).values('status').annotate(count=Count('lead_id'))

    # Initialize all counts to zero
    context['followup'] = 0
    context['scheduled_meeting'] = 0
    context['followup_landing'] = 0
    context['send_contract'] = 0
    context['longterm_followup'] = 0

    # Map the counts to the context dictionary
    for status_count in leads_count:
        if status_count['status'] == 'follow_up':
            context['followup'] = status_count['count']
        elif status_count['status'] == 'scheduled_meeting':
            context['scheduled_meeting'] = status_count['count']
        elif status_count['status'] == 'follow_up_landing':
            context['followup_landing'] = status_count['count']
        elif status_count['status'] == 'send_contract':
            context['send_contract'] = status_count['count']
        elif status_count['status'] == 'longterm_follow_up':
            context['longterm_followup'] = status_count['count']


    return render(request,'sales/calendar.html',context)




@permission_required('sales_dashboard')
@login_required
def sales_lead_create(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    now = tz.now()
    current_year = now.year

   


    # Include the names of the statuses in your context as well
    context['sales_statuses'] = dict(SALES_LEAD_CHOICES)

    if request.method == "POST":
        data = request.POST

        contact = data.get('contact')
        contact_phone = data.get('phone')
        contact_email = data.get('email')
        interest = int(data.get('interest'))
        followup_date = data.get('followup_date')
        followup_time = data.get('followup_time')
        notes = data.get('notes')
        status = data.get('status')

        

        lead = SalesLead.objects.create(agent_user=request.user,
                                   agent_profile=profile,
                                    contact=contact,
                                   contact_phone=contact_phone,
                                   contact_email = contact_email,
                                   interest_rating=interest,
                                   followup_date=followup_date,
                                   followup_time=followup_time,
                                   status=status,
                                   notes=notes,
                                   
                                   
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

            status = lead.get_status_display()

            contact = lead.contact

            followup_date = lead.followup_date

            followup_time = lead.followup_time

            action_type= "create"

            content = f'**Agent:** {profile.full_name}\n\n**Action:** Contact Creation \n\n**Status:** {str(status).upper()}\n\n**Contact:** {contact}\n\n**Follow up:** {followup_date} - {followup_time}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

            send_discord_message_sales_lead(content,lead_id,action_type)
            
        except:
            pass
        


        
        return redirect(f'/sales-dashboard-{current_year}')




   

    return render(request, 'sales/sales_lead_create.html', context)




@permission_required('sales_dashboard')
@login_required
def sales_lead_info(request, lead_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    now = tz.now()
    current_year = now.year

   
    lead = SalesLead.objects.get(lead_id=lead_id)
    context['lead'] = lead

    # Include the names of the statuses in your context as well
    sales_statuses = dict(SALES_LEAD_CHOICES)
    context['sales_statuses'] = sales_statuses

    if request.method == "POST":
        data = request.POST

        contact = data.get('contact')
        contact_phone = data.get('phone')
        contact_email = data.get('email')
        interest = int(data.get('interest'))
        followup_date = data.get('followup_date')
        followup_time = data.get('followup_time')
        notes = data.get('notes')
        status = data.get('status')

        lead = SalesLead.objects.get(lead_id=lead_id)

        old_status = lead.status

        
        lead.contact=contact
        lead.contact_phone=contact_phone
        lead.contact_email = contact_email
        lead.interest_rating=interest
        lead.followup_date=followup_date
        lead.followup_time=followup_time
        lead.status=status
        lead.notes=notes

        lead.save()
        
                                   
                                 
        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')


        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')
        if status != old_status:

            try:
                
            
                lead_id = lead.lead_id

                status = lead.get_status_display()

                contact = lead.contact

                followup_date = lead.followup_date

                followup_time = lead.followup_time


                action_type= "updates"

                content = f'**Agent:** {profile.full_name}\n\n**Action:** Contact Update \n\n**Status Change:** {sales_statuses[old_status].upper()} > {str(status).upper()}\n\n**Contact:** {contact}\n\n**Follow up:** {followup_date} - {followup_time}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

                send_discord_message_sales_lead(content,lead_id,action_type)

                
            except:
                pass
        


        
        return redirect(f'/sales-dashboard-{current_year}')




   

    return render(request, 'sales/sales_lead_info.html', context)



@permission_required('sales_dashboard')
@login_required
def sales_clients_list(request, year):

    context = {}
    context['year'] = year
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    
    sales_leads = SalesLead.objects.filter(active=True, pushed__year=year)

    context['sales_leads'] = sales_leads

    return render(request,'sales/clients_list.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class SalesLeadSubmitView(View):
    def post(self, request, *args, **kwargs):
        # Parse the JSON data from the request
        data = json.loads(request.body)


        agent_user = request.user
        agent_profile = Profile.objects.get(user=request.user)
        # Create a new SalesLead object
        lead = SalesLead.objects.create(
            agent_user=agent_user,
            agent_profile=agent_profile,
            contact=data['contact'],
            contact_phone=data['phone'],
            contact_email=data['email'],
            interest_rating=data['interest'],
            followup_date=data['date'],
            followup_time=data['time'],
            notes=data['notes']
        )

        
        return JsonResponse({'status': 'success', 'id': lead.lead_id})
    



@csrf_exempt  # Only use if you're not using CSRF tokens; otherwise, use the correct CSRF handling
def update_sales_lead(request):
    
    if request.method == 'POST':
        data = json.loads(request.body)
        lead_id = data.get('id')


        try:
            # Retrieve the SalesLead object and update it
            sales_lead = SalesLead.objects.get(lead_id=lead_id)
            sales_lead.contact = data.get('contact')
            sales_lead.contact_phone = data.get('phone')
            sales_lead.contact_email = data.get('email')
            sales_lead.interest_rating = data.get('interest_rate')
            sales_lead.followup_date = data.get('followup_date')
            sales_lead.followup_time = data.get('followup_time')
            sales_lead.notes = data.get('notes')
            sales_lead.save()

            return JsonResponse({'status': 'success', 'message': 'Lead updated successfully!'})
        except SalesLead.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Lead not found.'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)









class UpdateLeadStatusView(View):
    @csrf_exempt  # You can remove this if using CSRF tokens properly
    def post(self, request):
        data = json.loads(request.body)
        lead_id = data.get('id')
        new_status = data.get('status')

        try:
            lead = SalesLead.objects.get(lead_id=lead_id)
            lead.status = new_status
            lead.save()

            print(lead,lead.status)
            return JsonResponse({'status': 'success', 'message': 'Lead status updated'})
        except Lead.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Lead not found'}, status=404)




@login_required
def sales_leads_data(request):
    # Fetch active sales leads from the database
    sales_leads = SalesLead.objects.filter(active=True)

    # Create a dictionary to hold lists of sales leads for each status choice
    sales_lead_grouped = {choice[0]: [] for choice in SALES_LEAD_CHOICES}

    # Iterate over each sales lead and group by status
    for lead in sales_leads:
        sales_lead_grouped[lead.status].append(lead)

    # Prepare data structure for the JSON response
    data = []
    for status, leads in sales_lead_grouped.items():
        data.append({
            'status': status,
            'title': f"{dict(SALES_LEAD_CHOICES).get(status)} - {len(leads)}",
            'leads': [
                {
                    'lead_id': lead.lead_id,
                    'contact': lead.contact,
                    'contact_phone': lead.contact_phone,
                    'contact_email': lead.contact_email,
                    'interest_rating': lead.interest_rating,
                    'followup_date': lead.followup_date,
                    'followup_time': lead.followup_time,
                    'notes': lead.notes,
                }
                for lead in leads
            ]
        })

    return JsonResponse(data, safe=False)