from django.dispatch import Signal, receiver
from django.utils import timezone
import threading
from django.contrib.auth import logout

import time
from .models import Profile, WorkStatus  # Import your Profile and WorkStatus models
import pytz
from datetime import datetime
# from discord_app.bot import queue_message as discord_private
# from discord_app.views import discord_crm_timeout, send_discord_message_activity

from .models import DialerCredentials,SeatAssignmentLog

# Signals for user heartbeat and timeout
user_heartbeat_signal = Signal()
user_timeout_signal = Signal()

# Store user last heartbeat timestamps and request data
user_last_seen = {}
user_requests = {}

# Timeout duration (5 minutes = 300 seconds)
TIMEOUT_DURATION = 300  # 300 - 5 minutes

def check_user_timeouts():
    while True:
        now = timezone.now()
        for user, last_seen in list(user_last_seen.items()):

            if (now - last_seen).total_seconds() > TIMEOUT_DURATION:
                # Send a timeout signal if the user has been inactive for too long
                user_timeout_signal.send(sender=None, user=user, request=user_requests.get(user))
                # Remove user from the tracking list
                del user_last_seen[user]
                if user in user_requests:
                    del user_requests[user]
        time.sleep(TIMEOUT_DURATION / 2)

# Start the timeout checking thread
thread = threading.Thread(target=check_user_timeouts)
thread.daemon = True
thread.start()

# Signal receiver to update user activity on heartbeat
@receiver(user_heartbeat_signal)
def update_user_last_seen(sender, user, request, **kwargs):
    user_last_seen[user] = timezone.now()
    user_requests[user] = request  # Store the request object

# Signal receiver to handle user timeout
@receiver(user_timeout_signal)
def handle_user_timeout(sender, user, request, **kwargs):
    profile = Profile.objects.get(user=user)
    today = (timezone.localtime(timezone.now())).date()

    work_status = WorkStatus.objects.filter(user=user, date=today).last()

    last_status = work_status.current_status
    if last_status != "offline":
        try:
            work_status = WorkStatus.objects.get(user=user, date=today)
            previous_status = work_status.current_status
            duration = work_status.get_current_duration()
            work_status.update_status("offline")
        except WorkStatus.DoesNotExist:
            # Handle the case where WorkStatus doesn't exist, create a new one, or log an error
            pass
        
        """try:
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
            pass  # Handle the case where the agent does not have an assigned seat"""



        try:
            message = "Your Connection Timed out from the CRM! Please Login back and re-set your working status."
            # discord_private(int(profile.discord),message)
        except Exception as e:
            print(e)

        # try:
        #     # discord_crm_timeout(profile.full_name,request)
        # except Exception as e:
        #     print(e)

        
        utc_now = datetime.utcnow()

            # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')

        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')

        content = f'**Agent:** {profile.full_name}\n\n**Action:** Timed Out **{previous_status.upper()}** > **OFFLINE**\n\n**Duration:** {str(duration).upper()}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip}'

        # try:
        #     send_discord_message_activity(content,"offline")
        # except:
        #     pass
        logout(request)

    

                


