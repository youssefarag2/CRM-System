from django.shortcuts import render
from core.models import ServerSetting
import requests

from pytz import timezone
from datetime import datetime

import pytz

# Create your views here.


def get_ip_info(ip_address):
    data = {}
    try:
        if ip_address == "127.0.0.1":

            data['location'] = "Ezzat's Home"
            data['isp'] = 'Local Development Server'
        else:
            url = f'http://ipwhois.app/json/{ip_address}'
            response = (requests.get(url)).json()
            data['location'] = response['country']+", "+response['continent']
            data['isp'] = response['isp']
    except:
            data['location'] = "Error Fetching Location"
            data['isp'] = "Error Fetching ISP"
        
    return data



def send_discord_message_application(content,application_id):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None

    url = settings.applications_webhook
    headers = {'Content-Type': 'application/json'}

    color = 65280

    
    application_link =  f"https://{settings.crm_domain}/application-form/"+ str(application_id)

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



def send_discord_message_requests(content,request,request_type):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None

    url = settings.requests_webhook

    headers = {'Content-Type': 'application/json'}

    if request_type == "leave":
        color = 65280

        request_link = f"https://{settings.crm_domain}/leave-report/"+ str(request)
    
    elif request_type == "action":
        request_link = f"https://{settings.crm_domain}/action-report/"+ str(request)
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



def send_discord_message_lead(content,lead):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None

    url = settings.leads_webhook

    headers = {'Content-Type': 'application/json'}


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


def send_discord_message_prepayment(content,request):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    url = settings.prepayments_webhook
    headers = {'Content-Type': 'application/json'}



    request_link = f"https://{settings.crm_domain}/prepayment-report/"+ str(request)
    color = 65280  # Green color in Discord embed (decimal)

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




def send_discord_message_activity(content, status):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    url = settings.activity_webhook

    headers = {'Content-Type': 'application/json'}


    color = 65280

    green_color = 65280

    red_color = 16711680  

    orange_color = 16747520   

    if status == "break":
        color = orange_color

    elif status == "offline":
        color = red_color
        
    else:
        color = green_color



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



def discord_crm_login(agent_name, logged,request):

    if logged:
        action_text = "LOGGED IN"
        color = 65280  # Green color in Discord embed (decimal)
    else:
        action_text = "LOGGED OUT"
        color = 16747520  # Orange color in Discord embed (decimal)
    
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    url = settings.logins_webhook

    
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
    data = get_ip_info(request_ip)
    location = data['location']
    isp = data['isp']

    content = f'**Agent:** {agent_name}\n\n**Action:** {action_text}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}\n\n**Location:** {location}\n\n**Service Provider:** {isp}'

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


    action_text = "TIMED OUT"
    color = 16711680  # Red color in Discord embed (decimal)
    
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    url = settings.logins_webhook

    
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
    data = get_ip_info(request_ip)
    location = data['location']
    isp = data['isp']

    content = f'**Agent:** {agent_name}\n\n**Action:** {action_text}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}\n\n**Location:** {location}\n\n**Service Provider:** {isp}'

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




def send_discord_message_task(content,task_id, action_type):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    url = settings.tasks_webhook
    headers = {'Content-Type': 'application/json'}



    request_link = f"https://{settings.crm_domain}/task-info/"+ str(task_id)


    color = 65280

    

    green_color = 65280

    red_color = 16711680  

    orange_color = 16747520   


    if action_type == "create":
        color = green_color
    
    elif action_type == "reassign":
        color = orange_color

    elif action_type == "status":
        color = red_color




    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
                'title':'Task Link Click here to view',
                'url': request_link,
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')






def send_discord_message_sales_lead(content,lead_id, action_type):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None
    url = settings.sales_webhook
    headers = {'Content-Type': 'application/json'}



    request_link = f"https://{settings.crm_domain}/sales-lead-info/"+ str(lead_id)


    color = 65280

    

    green_color = 65280

    red_color = 16711680  

    orange_color = 16747520   


    if action_type == "create":
        color = green_color
    
    elif action_type == "updates":
        color = orange_color

    elif action_type == "status":
        color = red_color




    payload = {
        'embeds': [
            {
                'description': f' {content}',  # Using '>' for quote formatting
                'color': color,  # Setting the color based on 'logged' status
                'title':'Contact Link Click here to view',
                'url': request_link,
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print('Message sent successfully')
    else:
        print(f'Failed to send message: {response.status_code}')







def send_discord_message_contract(content, action_type):
    try:
        settings = ServerSetting.objects.first()
    except:
        settings = None

    url = settings.clients_webhook

    headers = {'Content-Type': 'application/json'}

    color = 65280


    green_color = 65280

    red_color = 16711680  

    orange_color = 16747520   


    if action_type == "filled":
        color = green_color
    
    elif action_type == "created":
        color = orange_color

    elif action_type == "visit":
        color = red_color

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

