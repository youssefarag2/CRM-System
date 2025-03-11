from django.shortcuts import render, redirect
from core.models import *
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone as tz

from django.utils.timezone import make_aware

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
from django.db import transaction, DatabaseError
from core.decorators import *
from discord_app.views import *




try:
    settings = ServerSetting.objects.first()
except:
    settings = None


@permission_required('seats')
@login_required
def seats(request):
    context = {"settings":settings,}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    campaigns = Campaign.objects.filter(campaign_type="calling", active=True,status="active")
    context['campaigns'] = campaigns

    now = tz.now()
    current_year = now.year
    current_month = now.month
    context['month'] = current_month
    context['year'] = current_year
    
    callers_list = ['callers','sales']
    callers_teams = Team.objects.filter(team_type__in=callers_list)

    agents = Profile.objects.filter(team__in=callers_teams, active=True)
    #agents = 0 # CHECK CALLERS 
    context['agent_profiles'] = agents


    
    return render(request,'operations/seats.html', context)



@permission_required('seats')
@login_required
def seat_breakdown(request, seat_id, month, year):
    context = {"settings":settings,}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]    

    

    context['seat_logs'] = get_seat_breakdown(seat_id, month , year)

    context['seat'] = DialerCredentials.objects.get(id=seat_id)

    
    return render(request,'operations/seat_breakdown.html', context)


@permission_required('seats')
@login_required
def agent_seat_breakdown(request, agent_id, month ,year ):
    context = {"settings":settings,}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    
    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]    

    context['seat_logs'] = get_agent_breakdown(agent_id, month, year)

    context['agent_profile'] = Profile.objects.get(id=agent_id)
    
    return render(request,'operations/agent_seat_breakdown.html', context)



def get_agent_breakdown(agent_profile_id, month, year):
    """Get a breakdown of all seat assignments for a specific agent."""
    seat_logs = SeatAssignmentLog.objects.filter(created_time__month=month, created_time__year=year,
                                                 agent_profile_id=agent_profile_id)
    breakdown = []
    
    for log in seat_logs:
        breakdown.append({
            'id':log.id,
            'seat_id': log.dialer_credentials.id,
            'seat_username':log.dialer_credentials.username,
            'campaign':log.dialer_credentials.campaign,
            'created_time':log.created_time,
            'start_time': log.start_time,
            'end_time': log.end_time,
            'duration_formatted': log.duration_formatted(),
        })
    
    return breakdown
def get_seat_breakdown(dialer_credentials_id, month, year ):
    """Get a breakdown of all agent assignments for a specific seat."""
    seat_logs = SeatAssignmentLog.objects.filter(created_time__month=month, created_time__year=year,
                                                 dialer_credentials_id=dialer_credentials_id)
    breakdown = []
    
    for log in seat_logs:
        breakdown.append({
            'agent_id': log.agent_profile.id,
            'agent_name':log.agent_profile.full_name,
            'start_time': log.start_time,
            'end_time': log.end_time,
            'created_time':log.created_time,
            'duration_formatted': log.duration_formatted(),
        })
    
    return breakdown

def list_all_agent_breakdowns():
    """List breakdowns for all agents."""
    all_breakdowns = []
    agents = Profile.objects.all()
    
    for agent in agents:
        breakdown = get_agent_breakdown(agent.id)
        all_breakdowns.append({
            'agent_id': agent.id,
            'breakdown': breakdown,
        })
    
    return all_breakdowns

def list_all_seat_breakdowns():
    """List breakdowns for all seats."""
    all_breakdowns = []
    seats = DialerCredentials.objects.all()
    
    for seat in seats:
        breakdown = get_seat_breakdown(seat.id)
        all_breakdowns.append({
            'seat_id': seat.id,
            'breakdown': breakdown,
        })
    
    return all_breakdowns





def log_end_of_session(agent_profile, seat):
    seat = SeatAssignmentLog.objects.filter(
        agent_profile=agent_profile,
        dialer_credentials=seat,
        end_time__isnull=True
    ).update(end_time=timezone.now())



@transaction.atomic
def update_seat_agent_profile(request, seat_id):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                agent_id = int(request.POST.get('agent_id'))
                seat = get_object_or_404(DialerCredentials, id=seat_id)

                if agent_id == 0:
                    # Unassign current agent from seat
                    agent_profile = seat.agent_profile
                    if agent_profile:
                        log_end_of_session(agent_profile, seat)
                        agent_profile.assigned_credentials = None
                        agent_profile.save()

                    seat.agent_profile = None
                    seat.save()
                
                else:
                    # Assign new agent to seat
                    agent_profile = get_object_or_404(Profile, id=agent_id)
                    try:
                        old_seat = DialerCredentials.objects.get(agent_profile=agent_profile)


                        
                        log_end_of_session(agent_profile, old_seat)
                        old_seat.agent_profile = None
                        old_seat.save()

                    except DialerCredentials.DoesNotExist as error:
                        old_seat = None

                    if seat.agent_profile:
                        old_agent_seated = seat.agent_profile
                        log_end_of_session(old_agent_seated, seat)
                        seat.agent_profile = None
                        seat.save()
                        old_agent_seated.assigned_credentials = None
                        old_agent_seated.save()

                    seat.agent_profile = agent_profile
                    seat.save()

                    agent_profile.assigned_credentials = seat
                    agent_profile.save()

                    
                    SeatAssignmentLog.objects.create(
                        agent_profile=agent_profile,
                        dialer_credentials=seat,
                        start_time=timezone.now()
                    )

                return JsonResponse({'success': True, 'message': 'Seat agent profile updated successfully.'})

            except DatabaseError as e:
                return JsonResponse({'success': False, 'message': 'Database error occurred'}, status=500)
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


@require_POST
def unseat_agent(request, agent_id):
    try:
        
        agent_profile = Profile.objects.get(id=agent_id)
        seat = agent_profile.assigned_credentials
        if agent_profile:
            # Log the end of the current session
            SeatAssignmentLog.objects.filter(
                agent_profile=agent_profile,
                dialer_credentials=seat,
                end_time__isnull=True
            ).update(end_time=timezone.now())

            # Update agent and seat profiles
            agent_profile.assigned_credentials = None
            agent_profile.save()

        # Clear the seat's agent profile assignment
        seat.agent_profile = None
        seat.save()

        return JsonResponse({'message': 'Agent unseated successfully.'}, status=200)

    except DialerCredentials.DoesNotExist:
        return JsonResponse({'message': 'Seat not found.'}, status=404)


@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteSeatLogView(View):
    def post(self, request, log_id):
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
            target_camp = get_object_or_404(SeatAssignmentLog, id=log_id)
            target_camp.delete()
            return JsonResponse({'message': 'Account deleted successfully.'}, status=200)
        
        else:
            return JsonResponse({'error': 'Invalid password.'}, status=401)



@login_required
def update_status_admin(request):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        user_id = request.POST.get('user_id')
        
        # Get the agent's profile
        profile = Profile.objects.get(id=user_id)
        profile_user = profile.user
        today = (tz.localtime(tz.now())).date()

        if new_status in dict(WorkStatus.STATUS_CHOICES).keys():
            try:
                # Get or create today's WorkStatus object for the user
                work_status, created = WorkStatus.objects.get_or_create(
                    user=profile_user,
                    date=today,
                    defaults={
                        'current_status': new_status,
                        'last_status_change': tz.now()
                    }
                )

                

                # If it's not newly created, update the status
                if not created:
                    work_status.update_status(new_status)

                # If the new status is 'offline', update the SeatAssignmentLog
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
                response_data = {
                    'success': True,
                    'new_status': new_status,
                }
                return JsonResponse(response_data)

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': False, 'error': 'Invalid status.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def update_seat_admin(request):
    if request.method == 'POST':
        seat_id = request.POST.get('seat_id')  # Get the new seat ID from the request
        agent_id = request.POST.get('agent_id')  # Get the agent ID from the request


        try:
            # Get the agent profile based on agent_id
            agent_profile = Profile.objects.get(id=agent_id)
            # Find the new seat object based on seat_id

            if int(seat_id) == 0:
                seat = agent_profile.assigned_credentials
                # Log the end of the current session
                SeatAssignmentLog.objects.filter(
                    agent_profile=agent_profile,
                    dialer_credentials=seat,
                    end_time__isnull=True
                ).update(end_time=timezone.now())

                # Update agent and seat profiles
                agent_profile.assigned_credentials = None
                agent_profile.save()

                # Clear the seat's agent profile assignment
                seat.agent_profile = None
                seat.save()

            else:

                seat = DialerCredentials.objects.get(id=seat_id)
                try:
                    print("is agent already seated before?")
                    old_seat = DialerCredentials.objects.get(agent_profile=agent_profile)

                    print(old_seat)
                    
                    log_end_of_session(agent_profile, old_seat)
                    old_seat.agent_profile = None
                    old_seat.save()

                except DialerCredentials.DoesNotExist as error:
                    old_seat = None

                if seat.agent_profile:
                    print('is another agent seated')
                    old_agent_seated = seat.agent_profile

                    print('old :', old_agent_seated)
                    log_end_of_session(old_agent_seated, seat)
                    seat.agent_profile = None
                    seat.save()
                    old_agent_seated.assigned_credentials = None
                    old_agent_seated.save()

                seat.agent_profile = agent_profile
                seat.save()

                agent_profile.assigned_credentials = seat
                agent_profile.save()

                SeatAssignmentLog.objects.create(
                    agent_profile=agent_profile,
                    dialer_credentials=seat,
                    start_time=timezone.now()
                )


            # Return success response
            response_data = {
                'success': True,
                'new_seat': seat.id,
            }
            return JsonResponse(response_data)

        except Profile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Agent not found.'})
        except DialerCredentials.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Seat not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@permission_required('agents_table')
@login_required
def agents_list_company(request):

    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month

    today_date = now.date() 

    
    context['month'] = current_month
    context['year'] = current_year
   
    
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    callers_list = ['callers', 'sales']
    callers_teams = Team.objects.filter(team_type__in=callers_list)

    agents = Profile.objects.filter(team__in=callers_teams, active=True)

    for agent in agents:
        work_status = WorkStatus.objects.filter(user=agent.user, date=today_date).first()
        agent.login_time2 = work_status.login_time if work_status else None

         # Attach the WorkStatus instance to the agent object
        agent.work_status = work_status

        if work_status and work_status.lateness:
            lateness = work_status.lateness
            lateness_status = work_status.lateness_status
            minutes_difference = lateness.total_seconds() / 60

            if lateness_status == "late":
                if minutes_difference <= 5:
                    agent.lateness_class = 'bg-gradient-warning'

                else:
                    agent.lateness_class = 'bg-gradient-danger'

                agent.lateness_status = f"{int(minutes_difference)} minutes late"

            elif lateness_status == "early":
                agent.lateness_class = 'bg-gradient-success'  # Class for early or on time
                agent.lateness_status = f"{abs(int(minutes_difference))} minutes early"

            else:
                agent.lateness_class = 'bg-gradient-success'  # Class for on time
                agent.lateness_status = "On time"
        else:
            agent.lateness_class = ''  # No class if no lateness data
            agent.lateness_status = "No data"

                # Count the number of pushed leads for the agent today
        pushed_leads_count = Lead.objects.filter(
            agent_user=agent.user,  # Assuming agent_user is the ForeignKey to User
            pushed__date=today_date  # Filter by the current date
        ).count()
        agent.pushed_leads_count = pushed_leads_count

    context['agents'] = agents

    context['team_name'] = "company"

    seats = DialerCredentials.objects.all()
    context['seats'] = seats


    
    # Fetch all teams and add them to the context
    teams = Team.objects.all()
    context['teams'] = teams


        # Fetch all campaigns and add them to the context
    campaigns = Campaign.objects.all()  # Assuming Campaign is the model for campaigns
    context['campaigns'] = campaigns





  

    return render(request,'operations/agents/agents_list.html',context)



@permission_required('agents_table') # Use the same permission
@login_required 
def fetch_agents(request):
    team_id = request.GET.get('team_id')
    if not team_id:
        return JsonResponse({'error': 'team_id is required'}, status=400)

    agents = Profile.objects.filter(team_id=team_id, active=True).values('id', 'full_name')
    return JsonResponse({'agents': list(agents)})





@permission_required('agents_table')
@login_required
def agents_list_team(request, team_id):

    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    

    today_date = now.date() 

    context['month'] = current_month
    context['year'] = current_year
   
    
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    team = Team.objects.get(id=team_id)

    context['team_name'] = team.team_name

    agents = Profile.objects.filter(team=team, active=True)

    for agent in agents:
        work_status = WorkStatus.objects.filter(user=agent.user, date=today_date).first()
        agent.login_time2 = work_status.login_time if work_status else None


        if work_status and work_status.lateness:
            lateness = work_status.lateness
            lateness_status = work_status.lateness_status
            minutes_difference = lateness.total_seconds() / 60

            if lateness_status == "late":
                if minutes_difference <= 5:
                    agent.lateness_class = 'bg-gradient-warning'

                else:
                    agent.lateness_class = 'bg-gradient-danger'

                agent.lateness_status = f"{int(minutes_difference)} minutes late"

            elif lateness_status == "early":
                agent.lateness_class = 'bg-gradient-success'  # Class for early or on time
                agent.lateness_status = f"{abs(int(minutes_difference))} minutes early"

            else:
                agent.lateness_class = 'bg-gradient-success'  # Class for on time
                agent.lateness_status = "On time"
        else:
            agent.lateness_class = ''  # No class if no lateness data
            agent.lateness_status = "No data"



    context['agents'] = agents

    seats = DialerCredentials.objects.all()
    context['seats'] = seats


    teams = Team.objects.all()
    context['teams'] = teams

 
    # Fetch all campaigns and add them to the context
    campaigns = Campaign.objects.all()  # Assuming Campaign is the model for campaigns
    context['campaigns'] = campaigns    



    return render(request,'operations/agents/agents_list.html',context)








@permission_required('working_hours')
@login_required
def working_hours_company(request, month,year):

    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['month_name'] = month_name
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    # Fetch all teams and add them to the context
    teams = Team.objects.all()
    context['teams'] = teams

    callers_list = ['callers', 'sales']
    callers_teams = Team.objects.filter(team_type__in=callers_list)
    
    agents = Profile.objects.filter(team__in=callers_teams, active=True)
    context['agents'] = agents

        
    # Define status field mapping
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    # Calculate total time for each status per agent
    status_totals = {}
    for agent in agents:
        agent_totals = {}
        for status in ['ready', 'meeting', 'break', 'offline']:
            total_time = WorkStatus.objects.filter(
                user=agent.user,
                date__month=month,
                date__year=year
            ).aggregate(total_time=Sum(status_field_mapping[status]))

            # Convert timedelta to formatted string
            total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            agent_totals[status] = formatted_time

        # Calculate total worked time
        total_worked_time_seconds = sum([
            (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
                total_ready_time=Sum('ready_time'),
                total_meeting_time=Sum('meeting_time'),
                total_break_time=Sum('break_time')
            )[field] or timedelta()).total_seconds()
            for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
        ])
        agent_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"

        # Calculate total payable time
        try:
            settings = ServerSetting.objects.first()
            break_paid = settings.break_paid
        except:
            break_paid = False
        total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_ready_time=Sum('ready_time')
        )['total_ready_time'] or timedelta()).total_seconds()
        total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_meeting_time=Sum('meeting_time')
        )['total_meeting_time'] or timedelta()).total_seconds()
        total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_break_time=Sum('break_time')
        )['total_break_time'] or timedelta()).total_seconds()

        total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)
        agent_totals['total_payable'] = f"{int(total_payable_time_seconds // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

        status_totals[agent] = agent_totals

    context['status_totals'] = status_totals


    return render(request,'operations/working_hours_company.html',context)


@permission_required('working_hours')
@login_required
def working_hours_team(request, team_id, month, year):
    context = {}
    now = tz.now()

    month_name = now.strftime('%B')
    context['month_name'] = month_name
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]

    # Fetch all teams and add them to the context
    teams = Team.objects.all()
    context['teams'] = teams

    # Fetch the relevant team and agents
    team = Team.objects.get(id=team_id)
    agents = Profile.objects.filter(team=team, active=True)
    context['agents'] = agents
    context['team_id'] = team.id
    context['team_name'] = team.team_name

    # Define status field mapping
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    # Calculate total time for each status per agent
    status_totals = {}
    for agent in agents:
        agent_totals = {}
        for status in ['ready', 'meeting', 'break', 'offline']:
            total_time = WorkStatus.objects.filter(
                user=agent.user,
                date__month=month,
                date__year=year
            ).aggregate(total_time=Sum(status_field_mapping[status]))

            # Convert timedelta to formatted string
            total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            agent_totals[status] = formatted_time

        # Calculate total worked time
        total_worked_time_seconds = sum([
            (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
                total_ready_time=Sum('ready_time'),
                total_meeting_time=Sum('meeting_time'),
                total_break_time=Sum('break_time')
            )[field] or timedelta()).total_seconds()
            for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
        ])
        agent_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"

        # Calculate total payable time
        try:
            settings = ServerSetting.objects.first()
            break_paid = settings.break_paid
        except:
            break_paid = False
        total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_ready_time=Sum('ready_time')
        )['total_ready_time'] or timedelta()).total_seconds()
        total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_meeting_time=Sum('meeting_time')
        )['total_meeting_time'] or timedelta()).total_seconds()
        total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_break_time=Sum('break_time')
        )['total_break_time'] or timedelta()).total_seconds()

        total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)
        agent_totals['total_payable'] = f"{int(total_payable_time_seconds // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

        status_totals[agent] = agent_totals

    context['status_totals'] = status_totals


    return render(request, 'operations/working_hours_team.html', context)


# @permission_required('agents_table')
# @login_required
# def agent_hours(request, agent_id,month,year):

#     context = {}

#     profile = Profile.objects.get(user=request.user)
#     context['profile'] = profile

#     agent_profile = Profile.objects.get(id=agent_id)
#     agent_user = agent_profile.user
#     context['agent'] = agent_profile
#     now = tz.now()
#     month_name = now.strftime('%B')
#     context['month_name'] = month_name
#     profile = Profile.objects.get(user=request.user)
#     context['profile'] = profile
#     month_date = datetime(year, month, 1)
#     month_name = month_date.strftime('%b')
#     context['year'] = year
#     context['month'] = month
#     context['month_name'] = month_name
#     context['full_month_name'] = calendar.month_name[month]


#     context['breakdown_data'] = WorkStatus.objects.filter(date__month=month, date__year=year,
#                                                         login_time__isnull=False, user=agent_user)
    
                                                   


#     return render(request,'operations/agent_breakdown.html',context)



@permission_required('agents_table')
@login_required
def agent_hours(request, agent_id, month, year):
    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    agent_profile = Profile.objects.get(id=agent_id)
    team = agent_profile.team
    agent_user = agent_profile.user
    context['agent'] = agent_profile
    context['team'] = team
    context['selected_team_id'] = team.id
    context['selected_agent_id'] = agent_profile.id

    now = tz.now()
    month_name = now.strftime('%B')
    context['month_name'] = month_name
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]

    # Check for date range query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        # Parse the start and end date
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        # Filter based on the date range
        breakdown_data = WorkStatus.objects.filter(
            date__range=[start_date, end_date],
            login_time__isnull=False, 
            user=agent_user
        )
    else:
        # Default to filtering by month and year
        breakdown_data = WorkStatus.objects.filter(
            date__month=month, 
            date__year=year,
            login_time__isnull=False, 
            user=agent_user
        )

    context['breakdown_data'] = breakdown_data
    teams = Team.objects.all()
    context['teams'] = teams

    return render(request, 'operations/agent_breakdown.html', context)








@permission_required('adjusting_hours')
@login_required
def adjusting_hours(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['adjusted_hours'] = ManualHours.objects.filter(active=True).order_by('-created')
    
   
    
    return render(request,'salaries/adjusting_hours.html', context)

@permission_required('adjusting_hours')
@login_required
def adjusting_hours_form(request):


    context = {}
    profile = Profile.objects.get(user=request.user)


    context['profile'] = profile
    context['agent_profiles'] = Profile.objects.filter(active=True)



    if request.method == "POST":
        data = request.POST

        agent_id = data.get('agent')
        operation = data.get('operation')
        amount = data.get('amount')
        reason = data.get('reason')
 
        if int(operation) == 1:
            positive = True
        else:
            positive = False

        agent_profile = Profile.objects.get(id=agent_id)
 
        feedback = ManualHours.objects.create(agent_user=agent_profile.user,
                                agent_profile=agent_profile,
                                admin_user=profile.user,
                                admin_profile=profile,
                                positive=positive,
                                hours=amount,
                                reason=reason,
 
                                )
 
        return redirect('/adjusting-hours')

            
    
    return render(request,'salaries/adjusting_hours_form.html',context)


@permission_required('salaries_table')
@login_required
def salary_company(request, month,year):

    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['month_name'] = month_name
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    callers_list = ['callers', 'sales']
    callers_teams = Team.objects.filter(team_type__in=callers_list)
    
    agents = Profile.objects.filter(team__in=callers_teams, active=True)
    context['agents'] = agents

        
    # Define status field mapping
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    # Calculate total time for each status per agent
    status_totals = {}
    for agent in agents:
        agent_totals = {}
        for status in ['ready', 'meeting', 'break', 'offline']:
            total_time = WorkStatus.objects.filter(
                user=agent.user,
                date__month=month,
                date__year=year
            ).aggregate(total_time=Sum(status_field_mapping[status]))

            total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            agent_totals[status] = formatted_time

        total_worked_time_seconds = sum([
            (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
                total_ready_time=Sum('ready_time'),
                total_meeting_time=Sum('meeting_time'),
                total_break_time=Sum('break_time')
            )[field] or timedelta()).total_seconds()
            for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
        ])
        agent_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"

        try:
            settings = ServerSetting.objects.first()
            break_paid = settings.break_paid
        except:
            break_paid = False

        total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_ready_time=Sum('ready_time')
        )['total_ready_time'] or timedelta()).total_seconds()
        total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_meeting_time=Sum('meeting_time')
        )['total_meeting_time'] or timedelta()).total_seconds()
        total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_break_time=Sum('break_time')
        )['total_break_time'] or timedelta()).total_seconds()

        total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)

        # Fetch added and removed manual hours
        added_minutes = ManualHours.objects.filter(created__month=month, created__year=year, agent_profile=agent, positive=True, active=True).aggregate(total_added=Sum('hours'))['total_added'] or 0
        removed_minutes = ManualHours.objects.filter(created__month=month, created__year=year, agent_profile=agent, positive=False, active=True).aggregate(total_removed=Sum('hours'))['total_removed'] or 0
        deductions = Action.objects.filter(
            agent=agent.user,
            action_type="deduction",
            status="approved",
            active=True,
            submission_date__month=month,
            submission_date__year=year
        )

        ded_total = deductions.aggregate(total_deductions=Sum('deduction_amount'))['total_deductions'] or 0
        payments = Prepayment.objects.filter(
            agent=agent.user,
            status="approved",
            active=True,
            submission_date__month=month,
            submission_date__year=year
        )

        prepayment_total = payments.aggregate(total_prepayments=Sum('amount'))['total_prepayments'] or 0
        
        # Convert manual hours to seconds (assuming manual hours are in hours)
        added_seconds = added_minutes * 60
        removed_seconds = removed_minutes * 60
        deduction_seconds = ded_total * 3600

        total_seconds = int(added_seconds)
        hours = total_seconds // 3600  # Get the total hours
        minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
        seconds = total_seconds % 60  # Get the remaining seconds

        # Format the time in HH:MM:SS
        formatted_added_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"
        

        total_seconds = int(removed_seconds) 
        hours = total_seconds // 3600  # Get the total hours
        minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
        seconds = total_seconds % 60  # Get the remaining seconds

        # Format the time in HH:MM:SS
        formatted_removed_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"

        # Adjust total payable time with manual hours


        total_seconds = int(deduction_seconds)
        hours = total_seconds // 3600  # Get the total hours
        minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
        seconds = total_seconds % 60  # Get the remaining seconds

        # Format the time in HH:MM:SS
        formatted_deduction_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"

        # Adjust total payable time with manual hours
        total_payable_time_seconds += added_seconds - removed_seconds - deduction_seconds

        agent_totals['added_minutes'] = str(formatted_added_seconds)
        agent_totals['removed_minutes'] = str(formatted_removed_seconds)
        agent_totals['deductions'] = str(formatted_deduction_seconds)
        agent_totals['prepayments'] = str(prepayment_total)

        agent_totals['total_payable'] = f"{int(total_payable_time_seconds // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

        status_totals[agent] = agent_totals

        salary = agent.hourly_rate * (total_payable_time_seconds/3600)

        salary_final = salary - int(prepayment_total)

        agent_totals['salary'] = round(salary_final,2)
    context['status_totals'] = status_totals


    return render(request, 'salaries/salaries_company.html', context)



@permission_required('salaries_table')
@login_required
def salary_team(request, team_id, month,year):

    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['month_name'] = month_name
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    team = Team.objects.get(id=team_id)

    context['teamid'] = team_id

    context['team_name'] = team.team_name
    
    agents = Profile.objects.filter(team=team, active=True)
    context['agents'] = agents

        
    # Define status field mapping
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    # Calculate total time for each status per agent
    status_totals = {}
    for agent in agents:
        agent_totals = {}
        for status in ['ready', 'meeting', 'break', 'offline']:
            total_time = WorkStatus.objects.filter(
                user=agent.user,
                date__month=month,
                date__year=year
            ).aggregate(total_time=Sum(status_field_mapping[status]))

            total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            agent_totals[status] = formatted_time

        total_worked_time_seconds = sum([
            (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
                total_ready_time=Sum('ready_time'),
                total_meeting_time=Sum('meeting_time'),
                total_break_time=Sum('break_time')
            )[field] or timedelta()).total_seconds()
            for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
        ])
        agent_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"

        try:
            settings = ServerSetting.objects.first()
            break_paid = settings.break_paid
        except:
            break_paid = False

        total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_ready_time=Sum('ready_time')
        )['total_ready_time'] or timedelta()).total_seconds()
        total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_meeting_time=Sum('meeting_time')
        )['total_meeting_time'] or timedelta()).total_seconds()
        total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_break_time=Sum('break_time')
        )['total_break_time'] or timedelta()).total_seconds()

        total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)

        # Fetch added and removed manual hours
        added_minutes = ManualHours.objects.filter(created__month=month, created__year=year, agent_profile=agent, positive=True, active=True).aggregate(total_added=Sum('hours'))['total_added'] or 0
        removed_minutes = ManualHours.objects.filter(created__month=month, created__year=year, agent_profile=agent, positive=False, active=True).aggregate(total_removed=Sum('hours'))['total_removed'] or 0
        deductions = Action.objects.filter(
            agent=agent.user,
            action_type="deduction",
            status="approved",
            active=True,
            submission_date__month=month,
            submission_date__year=year
        )

        ded_total = deductions.aggregate(total_deductions=Sum('deduction_amount'))['total_deductions'] or 0
        payments = Prepayment.objects.filter(
            agent=agent.user,
            status="approved",
            active=True,
            submission_date__month=month,
            submission_date__year=year
        )

        prepayment_total = payments.aggregate(total_prepayments=Sum('amount'))['total_prepayments'] or 0
        
        # Convert manual hours to seconds (assuming manual hours are in hours)
        added_seconds = added_minutes * 60
        removed_seconds = removed_minutes * 60
        deduction_seconds = ded_total * 3600

        total_seconds = int(added_seconds)
        hours = total_seconds // 3600  # Get the total hours
        minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
        seconds = total_seconds % 60  # Get the remaining seconds

        # Format the time in HH:MM:SS
        formatted_added_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"
        

        total_seconds = int(removed_seconds)
        hours = total_seconds // 3600  # Get the total hours
        minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
        seconds = total_seconds % 60  # Get the remaining seconds

        # Format the time in HH:MM:SS
        formatted_removed_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"

        total_seconds = int(deduction_seconds)
        hours = total_seconds // 3600  # Get the total hours
        minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
        seconds = total_seconds % 60  # Get the remaining seconds

        # Format the time in HH:MM:SS
        formatted_deduction_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"

        # Adjust total payable time with manual hours
        total_payable_time_seconds += added_seconds - removed_seconds - deduction_seconds

        agent_totals['added_minutes'] = str(formatted_added_seconds)
        agent_totals['removed_minutes'] = str(formatted_removed_seconds)
        agent_totals['deductions'] = str(formatted_deduction_seconds)
        agent_totals['prepayments'] = str(prepayment_total)

        agent_totals['total_payable'] = f"{int(total_payable_time_seconds // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

        status_totals[agent] = agent_totals

        salary = agent.hourly_rate * (total_payable_time_seconds/3600)

        salary_final = salary - int(prepayment_total)

        agent_totals['salary'] = round(salary_final,2)
    context['status_totals'] = status_totals

    return render(request, 'salaries/salaries_team.html', context)

@login_required
def invoice(request, agent_id,month, year):
    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = int(month)
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['month_name'] = month_name    
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    agent_profile = Profile.objects.get(id=agent_id)
    context['agent_profile'] = agent_profile

    if profile != agent_profile:
        if not profile.role.agents_table:
            return redirect('/')



    formatted_date = f"{month:02d}/01/{year}"

    context ['formatted_date'] = formatted_date


    next_month = (month % 12) + 1
    next_year = year + (month // 12)
    formatted_date = f"{next_month:02d}/01/{next_year}"

    context ['due_date'] = formatted_date


    agent = Profile.objects.get(id=agent_id)

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
            date__month=month,
            date__year=year
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
        (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_ready_time=Sum('ready_time'),
            total_meeting_time=Sum('meeting_time'),
            total_break_time=Sum('break_time')
        )[field] or timedelta()).total_seconds()
        for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
    ])
    status_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"



    total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
        total_ready_time=Sum('ready_time')
    )['total_ready_time'] or timedelta()).total_seconds()
    total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
        total_meeting_time=Sum('meeting_time')
    )['total_meeting_time'] or timedelta()).total_seconds()
    total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
        total_break_time=Sum('break_time')
    )['total_break_time'] or timedelta()).total_seconds()

    total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)

    # Fetch added and removed manual hours
    added_minutes = ManualHours.objects.filter(created__month=month, created__year=year, agent_profile=agent, positive=True, active=True).aggregate(total_added=Sum('hours'))['total_added'] or 0
    removed_minutes = ManualHours.objects.filter(created__month=month, created__year=year, agent_profile=agent, positive=False, active=True).aggregate(total_removed=Sum('hours'))['total_removed'] or 0
    deductions = Action.objects.filter(
        agent=agent.user,
        action_type="deduction",
        status="approved",
        active=True,
        submission_date__month=month,
        submission_date__year=year
    )

    ded_total = deductions.aggregate(total_deductions=Sum('deduction_amount'))['total_deductions'] or 0
    payments = Prepayment.objects.filter(
        agent=agent.user,
        status="approved",
        active=True,
        submission_date__month=month,
        submission_date__year=year
    )

    prepayment_total = payments.aggregate(total_prepayments=Sum('amount'))['total_prepayments'] or 0

    # Convert manual hours to seconds (assuming manual hours are in hours)
    added_seconds = added_minutes * 60
    removed_seconds = removed_minutes * 60
    deduction_seconds = ded_total * 3600

    added_hours = added_minutes / 60

    removed_hours = removed_minutes / 60

    # Adjust total payable time with manual hours
    total_positive = total_payable_time_seconds + added_seconds
    total_payable =  total_positive - removed_seconds - deduction_seconds


        # Convert manual hours to seconds (assuming manual hours are in hours)
    added_seconds = added_minutes * 60
    removed_seconds = removed_minutes * 60
    deduction_seconds = ded_total * 3600

    total_seconds = int(added_seconds)
    hours = total_seconds // 3600  # Get the total hours
    minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
    seconds = total_seconds % 60  # Get the remaining seconds

    # Format the time in HH:MM:SS
    formatted_added_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"
    

    total_seconds = int(removed_seconds)
    hours = total_seconds // 3600  # Get the total hours
    minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
    seconds = total_seconds % 60  # Get the remaining seconds

    # Format the time in HH:MM:SS
    formatted_removed_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"

    total_seconds = int(deduction_seconds)
    hours = total_seconds // 3600  # Get the total hours
    minutes = (total_seconds % 3600) // 60  # Get the remaining minutes
    seconds = total_seconds % 60  # Get the remaining seconds

    # Format the time in HH:MM:SS
    formatted_deduction_seconds = f"{hours:02}:{minutes:02}:{seconds:02}"

    status_totals['added_hours'] = str(formatted_added_seconds)
    status_totals['added_hours_total'] = round(added_hours * agent.hourly_rate, 2)
    status_totals['removed_hours'] = str(formatted_removed_seconds)
    status_totals['removed_hours_total'] = round(removed_hours * agent.hourly_rate, 2)

    status_totals['deductions'] = str(formatted_deduction_seconds)
    status_totals['deductions_total'] = round(ded_total * agent.hourly_rate, 2)

    status_totals['prepayments'] = str(prepayment_total)
    status_totals['prepayment_total'] = round(prepayment_total * agent.hourly_rate, 2)
    status_totals['total_positive'] = round((total_positive/3600) * agent.hourly_rate, 2)
    status_totals['total_payable'] = f"{int(total_payable // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

    salary = agent.hourly_rate * (total_payable / 3600)

    salary_final = salary - int(prepayment_total)

    status_totals['salary'] = round(salary_final, 2)
    
    context['agentid'] = agent.id

    context['invoice'] = status_totals

    
    return render(request,'salaries/invoice.html', context)




@permission_required('attendance_monitor')
@login_required
def attendance_company(request, month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date

    # Fetch all teams and add them to the context
    teams = Team.objects.all()
    context['teams'] = teams

    context['absences'] = Absence.objects.filter(absence_date__year=year, active=True)

    absence_counts = Absence.objects.filter(
        active=True,
        absence_date__month=month,
        absence_date__year=year,
    ).values('absence_type').annotate(count=Count('id'))

    # Initialize all counts to zero
    context['annuals'] = 0
    context['upls'] = 0
    context['sicks'] = 0
    context['casuals'] = 0
    context['nsncs'] = 0

    # Map the counts to the context dictionary
    for absence in absence_counts:
        if absence['absence_type'] == 'annual':
            context['annuals'] = absence['count']
        elif absence['absence_type'] == 'upl':
            context['upls'] = absence['count']
        elif absence['absence_type'] == 'sick':
            context['sicks'] = absence['count']
        elif absence['absence_type'] == 'casual':
            context['casuals'] = absence['count']
        elif absence['absence_type'] == 'nsnc':
            context['nsncs'] = absence['count']


    return render(request,'operations/attendance_company.html',context)


@permission_required('attendance_monitor')
@login_required
def attendance_team(request, team_id, month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date
    team = Team.objects.get(id=team_id)

    context['team'] = team
    context['absences'] = Absence.objects.filter(team = team, absence_date__year=year,active=True)

    # Fetch all teams and add them to the context
    teams = Team.objects.all()
    context['teams'] = teams


    absence_counts = Absence.objects.filter(
        team = team,
        active=True,
        absence_date__month=month,
        absence_date__year=year,
    ).values('absence_type').annotate(count=Count('id'))

    # Initialize all counts to zero
    context['annuals'] = 0
    context['upls'] = 0
    context['sicks'] = 0
    context['casuals'] = 0
    context['nsncs'] = 0

    # Map the counts to the context dictionary
    for absence in absence_counts:
        if absence['absence_type'] == 'annual':
            context['annuals'] = absence['count']
        elif absence['absence_type'] == 'upl':
            context['upls'] = absence['count']
        elif absence['absence_type'] == 'sick':
            context['sicks'] = absence['count']
        elif absence['absence_type'] == 'casual':
            context['casuals'] = absence['count']
        elif absence['absence_type'] == 'nsnc':
            context['nsncs'] = absence['count']



    return render(request,'operations/attendance_team.html',context)


@permission_required('attendance_monitor')
@login_required
def attendance_agent(request, agent_id, month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date

    # Fetch all teams and add them to the context
    teams = Team.objects.all()
    context['teams'] = teams

  

    agent_profile = Profile.objects.get(id=agent_id)
    context['absences'] = Absence.objects.filter(agent_profile = agent_profile, absence_date__year=year,active=True)

    context['agent_profile'] = agent_profile

    team = agent_profile.team
    context['team'] = team
    context['selected_team_id'] = team.id
    context['selected_agent_id'] = agent_profile.id

    absence_counts = Absence.objects.filter(
        agent_profile = agent_profile,
        active=True,
        absence_date__month=month,
        absence_date__year=year,
    ).values('absence_type').annotate(count=Count('id'))

    # Initialize all counts to zero
    context['annuals'] = 0
    context['upls'] = 0
    context['sicks'] = 0
    context['casuals'] = 0
    context['nsncs'] = 0

    # Map the counts to the context dictionary
    for absence in absence_counts:
        if absence['absence_type'] == 'annual':
            context['annuals'] = absence['count']
        elif absence['absence_type'] == 'upl':
            context['upls'] = absence['count']
        elif absence['absence_type'] == 'sick':
            context['sicks'] = absence['count']
        elif absence['absence_type'] == 'casual':
            context['casuals'] = absence['count']
        elif absence['absence_type'] == 'nsnc':
            context['nsncs'] = absence['count']


    work_status_objects = WorkStatus.get_workstatus_with_login_time(agent_profile, month, year)
    attendance_count = work_status_objects.count()

    context['attendance'] = work_status_objects
    context['attendance_count'] = attendance_count

    return render(request,'operations/attendance_agent.html',context)


@permission_required('attendance_monitor')
@login_required
def report_absence(request):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_name = now.strftime('%B')
    context['month_name'] = month_name
    context['today_date'] = now.date()

    context['agents'] = Profile.objects.filter(active=True)

    context['absence_types'] = ABSENCE_CHOICES

    if request.method == "POST":
        data = request.POST
        next_url = request.GET.get('next', '/')  # Default URL if `next` is not provided

        agent_id = data.get('agent_id') 
        absence_type = data.get('absence_type')
        date = data.get('date')
        notes = data.get('notes')

        agent_profile = Profile.objects.get(id=agent_id)
        reporter_profile = Profile.objects.get(user=request.user)

        absence = Absence.objects.create(
            team = agent_profile.team,
            reporter = request.user,
            reporter_profile = reporter_profile,
            agent = agent_profile.user,
            agent_profile = agent_profile,
            absence_date = date,
            absence_type = absence_type,
            notes = notes,
        )
        return redirect(next_url)


    return render(request,'operations/report_absence.html',context)




@permission_required('lateness_monitor')
@login_required
def lateness_company(request, month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date
    
    callers_list = ['callers', 'sales']
    callers_teams = Team.objects.filter(team_type__in=callers_list)
    agents = Profile.objects.filter(team__in=callers_teams, active=True)
    
    # Create a list of all days in the month
    days_in_month = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day) for day in range(1, days_in_month + 1)]

    absences = []
    late_less_than_5 = 0
    early_or_on_time = 0
    late_5_or_more = 0

    for agent in agents:
        for day in dates:
            work_status = WorkStatus.objects.filter(
                user=agent.user,
                date=day.date(),
                login_time__isnull=False
            ).first()

            if work_status and work_status.lateness:
            
                lateness = work_status.lateness
                lateness_status = work_status.lateness_status

                
                minutes_difference = lateness.total_seconds() / 60

                if lateness_status == "late":
                    
                    if minutes_difference <= 5:
                        status_class = 'bg-gradient-warning'
                        late_less_than_5 += 1
                    else:
                        status_class = 'bg-gradient-danger'
                        late_5_or_more += 1
                    status = f"{int(minutes_difference)} minutes late"
                elif lateness_status == "early":
                    status_class = 'bg-gradient-success'
                    early_or_on_time += 1
                    status = f"{abs(int(minutes_difference))} minutes early"
                else:
                    status_class = 'bg-gradient-success'
                    early_or_on_time += 1
                    status = "On time"
                
                
                absences.append({
                    'agent_profile': f"{agent.full_name}",
                    'status':status,
                    'absence_date': day.date(),
                    'absence_type': status_class,
                })


    context['absences'] = absences
    context['late_less_than_5'] = late_less_than_5
    context['early_or_on_time'] = early_or_on_time
    context['late_5_or_more'] = late_5_or_more



    return render(request, 'operations/lateness_company.html', context)

@permission_required('lateness_monitor')
@login_required
def lateness_team(request, team_id,month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date
    
    team = Team.objects.get(id=team_id)
    agents = Profile.objects.filter(team=team, active=True)
    context['team'] = team

    # Create a list of all days in the month
    days_in_month = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day) for day in range(1, days_in_month + 1)]

    absences = []

    late_less_than_5 = 0
    early_or_on_time = 0
    late_5_or_more = 0

    for agent in agents:
        for day in dates:
            work_status = WorkStatus.objects.filter(
                user=agent.user,
                date=day.date(),
                login_time__isnull=False
            ).first()

            if work_status and work_status.lateness:
            
                lateness = work_status.lateness
                lateness_status = work_status.lateness_status

                
                minutes_difference = lateness.total_seconds() / 60

                if lateness_status == "late":
                    
                    if minutes_difference <= 5:
                        status_class = 'bg-gradient-warning'
                        late_less_than_5 += 1
                    else:
                        status_class = 'bg-gradient-danger'
                        late_5_or_more += 1
                    status = f"{int(minutes_difference)} minutes late"
                elif lateness_status == "early":
                    status_class = 'bg-gradient-success'
                    early_or_on_time += 1
                    status = f"{abs(int(minutes_difference))} minutes early"
                else:
                    status_class = 'bg-gradient-success'
                    early_or_on_time += 1
                    status = "On time"
                
                absences.append({
                    'agent_profile': f"{agent.full_name}",
                    'status':status,
                    'absence_date': day.date(),
                    'absence_type': status_class,
                })


    context['absences'] = absences
    context['late_less_than_5'] = late_less_than_5
    context['early_or_on_time'] = early_or_on_time
    context['late_5_or_more'] = late_5_or_more

    return render(request, 'operations/lateness_team.html', context)


@permission_required('lateness_monitor')
@login_required
def lateness_agent(request, agent_id,month, year):

    context = {}

    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['today_date'] = month_date
    
    agent_profile = Profile.objects.get(id=agent_id, active=True)

    context['agent_profile'] = agent_profile
    context['agent_id'] = agent_id

    # Create a list of all days in the month
    days_in_month = calendar.monthrange(year, month)[1]
    dates = [datetime(year, month, day) for day in range(1, days_in_month + 1)]

    absences = []

    late_less_than_5 = 0
    early_or_on_time = 0
    late_5_or_more = 0

    total_late_minutes = 0  # Initialize total late minutes

    for day in dates:
        work_status = WorkStatus.objects.filter(
            user=agent_profile.user,
            date=day.date(),
            login_time__isnull=False
        ).first()

        if work_status and work_status.lateness:
            
            lateness = work_status.lateness
            lateness_status = work_status.lateness_status

            
            minutes_difference = lateness.total_seconds() / 60

            if lateness_status == "late":
                total_late_minutes += minutes_difference  # Add to total late minutes
                
                if minutes_difference <= 5:
                    status_class = 'bg-gradient-warning'
                    late_less_than_5 += 1
                else:
                    status_class = 'bg-gradient-danger'
                    late_5_or_more += 1
                status = f"{int(minutes_difference)} minutes late"
            elif lateness_status == "early":
                status_class = 'bg-gradient-success'
                early_or_on_time += 1
                status = f"{abs(int(minutes_difference))} minutes early"
            else:
                status_class = 'bg-gradient-success'
                early_or_on_time += 1
                status = "On time"
            
            # Append the result
            absences.append({
                'agent_profile': f"{status}",
                'absence_date': day.date(),
                'absence_type': status_class,
            })

    total_late_seconds = round(total_late_minutes * 60)  # Convert minutes to seconds and round
    hours, remainder = divmod(total_late_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_late_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    context['total_lateness'] = formatted_late_time
    context['absences'] = absences
    context['late_less_than_5'] = late_less_than_5
    context['early_or_on_time'] = early_or_on_time
    context['late_5_or_more'] = late_5_or_more

    return render(request, 'operations/lateness_agent.html', context)





@permission_required('agents_table')
@login_required
def agents_moderation(request, month, year):

    context = {}
    now = tz.now()
    current_year = now.year
    current_month = now.month
    month_date = datetime(year, month, 1)  
    month_name = month_date.strftime('%b') 
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    context['month_name'] = month_name
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    callers_list = ['callers']
    callers_teams = Team.objects.filter(team_type__in=callers_list)
    
    agents = Profile.objects.filter(team__in=callers_teams, active=True)
    context['agents'] = agents

        
    # Define status field mapping
    status_field_mapping = {
        'ready': 'ready_time',
        'meeting': 'meeting_time',
        'break': 'break_time',
        'offline': 'offline_time'
    }

    # Calculate total time for each status per agent
    status_totals = {}
    for agent in agents:
        agent_totals = {}
        for status in ['ready', 'meeting', 'break', 'offline']:
            total_time = WorkStatus.objects.filter(
                user=agent.user,
                date__month=month,
                date__year=year
            ).aggregate(total_time=Sum(status_field_mapping[status]))

            # Convert timedelta to formatted string
            total_seconds = total_time['total_time'].total_seconds() if total_time['total_time'] else 0
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            agent_totals[status] = formatted_time

        # Calculate total worked time
        total_worked_time_seconds = sum([
            (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
                total_ready_time=Sum('ready_time'),
                total_meeting_time=Sum('meeting_time'),
                total_break_time=Sum('break_time')
            )[field] or timedelta()).total_seconds()
            for field in ['total_ready_time', 'total_meeting_time', 'total_break_time']
        ])
        agent_totals['total_worked'] = f"{int(total_worked_time_seconds // 3600):02}:{int((total_worked_time_seconds % 3600) // 60):02}:{int(total_worked_time_seconds % 60):02}"

        # Calculate total payable time
        try:
            settings = ServerSetting.objects.first()
            break_paid = settings.break_paid
        except:
            break_paid = False
        total_ready_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_ready_time=Sum('ready_time')
        )['total_ready_time'] or timedelta()).total_seconds()
        total_meeting_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_meeting_time=Sum('meeting_time')
        )['total_meeting_time'] or timedelta()).total_seconds()
        total_break_time_seconds = (WorkStatus.objects.filter(user=agent.user, date__month=month, date__year=year).aggregate(
            total_break_time=Sum('break_time')
        )['total_break_time'] or timedelta()).total_seconds()

        total_payable_time_seconds = total_ready_time_seconds + total_meeting_time_seconds + (total_break_time_seconds if break_paid else 0)
        agent_totals['total_payable'] = f"{int(total_payable_time_seconds // 3600):02}:{int((total_payable_time_seconds % 3600) // 60):02}:{int(total_payable_time_seconds % 60):02}"

        leads_count = len(Lead.objects.filter(agent_profile=agent, pushed__month=month, pushed__year=year))
        qualified_count = len(Lead.objects.filter(agent_profile=agent,pushed__month=month,pushed__year=year, status='qualified'))
        qa_dq_count = len(Lead.objects.filter(agent_profile=agent,pushed__month=month,pushed__year=year, status__in=['qualified','disqualified']))
        agent_totals['hours_per_lead'] = (total_payable_time_seconds/3600) / leads_count if leads_count != 0 else 0
        salary = agent.hourly_rate * (total_payable_time_seconds/3600)

        agent_totals['leads_count'] = leads_count
        agent_totals['usd_per_lead'] = salary / leads_count if leads_count != 0 else salary
        agent_totals['qa_dq_ratio'] = (qualified_count/qa_dq_count)*100 if qa_dq_count != 0 else 0
        agent_totals['usd_per_qa'] = salary / qualified_count if qualified_count != 0 else salary




        days_in_month = calendar.monthrange(year, month)[1]
        dates = [datetime(year, month, day) for day in range(1, days_in_month + 1)]


        

        total_late_minutes = 0  # Initialize total late minutes

        for day in dates:
            work_status = WorkStatus.objects.filter(
                user=agent.user,
                date=day.date(),
                login_time__isnull=False
            ).first()

            if work_status and work_status.lateness:
                
                lateness = work_status.lateness
                lateness_status = work_status.lateness_status

                
                minutes_difference = lateness.total_seconds() / 60

                if lateness_status == "late":
                    total_late_minutes += minutes_difference  # Add to total late minutes
                    
                    

        total_late_seconds = round(total_late_minutes * 60)  # Convert minutes to seconds and round
        hours, remainder = divmod(total_late_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_late_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        agent_totals['total_lateness'] = formatted_late_time

        
        agent_totals['positive_feedbacks'] = len(Feedback.objects.filter(agent_profile=agent, created__month=month, created__year=year,feedback_type="positive"))

        agent_totals['negative_feedbacks'] = len(Feedback.objects.filter(agent_profile=agent, created__month=month, created__year=year,feedback_type="negative"))

        agent_totals['neutral_feedbacks'] = len(Feedback.objects.filter(agent_profile=agent, created__month=month, created__year=year,feedback_type="neutral"))

        status_totals[agent] = agent_totals


        

    context['status_totals'] = status_totals

  




        



    return render(request,'operations/agents_moderation.html',context)



def calculate_working_days(month, year):
    # Get the total number of days in the given month and year
    total_days = calendar.monthrange(year, month)[1]
    
    working_days = 0
    
    for day in range(1, total_days + 1):
        date = datetime(year, month, day)
        # Check if the day is a weekday (Monday=0, ..., Sunday=6)
        if date.weekday() < 5:  # 0-4 corresponds to Monday-Friday
            working_days += 1
            
    return working_days

def calculate_working_days_in_year(year):
    """
    Calculate the number of working days (Monday through Friday) in the given year.
    """
    working_days = 0
    for month in range(1, 13):
        month_start_date = datetime(year, month, 1)
        if month == 12:
            month_end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            month_end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        for single_date in (month_start_date + timedelta(n) for n in range((month_end_date - month_start_date).days + 1)):
            if single_date.weekday() < 5:  # Monday to Friday
                working_days += 1

    return working_days


def calculate_working_days_in_month(start_date, end_date):
    """
    Calculate the number of working days (Monday through Friday) in the given month.
    """
    working_days = 0
    for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
        if single_date.weekday() < 5:  # Monday to Friday
            working_days += 1

    return working_days




def format_hours_minutes(decimal_hours):
    """
    Convert decimal hours to HH:MM format.
    """
    hours = int(decimal_hours)
    minutes = int(round((decimal_hours - hours) * 60))
    return f"{hours:02}:{minutes:02}"



@permission_required('camp_hours')
@login_required
def camp_hours_daily(request, camp_id, month, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    # Create a datetime object for the given month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]

    campaign = Campaign.objects.get(id=camp_id)
    context['campaign'] = campaign

    working_days_in_month = calculate_working_days(month, year)
    target_hours_daily = campaign.weekly_hours / 5
    target_hours_monthly = target_hours_daily * working_days_in_month

    context['target_hours_daily'] = int(target_hours_daily)

    start_date = make_aware(datetime(year, month, 1))  # First day of the month
    if month == 12:
        end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of December
    else:
        end_date = make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)  # Last second of the month

    # Initialize lists to hold days and durations
    days_list = []
    durations_list = []

    # Calculate daily accumulated durations
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        # Get accumulated durations for the current day
        accumulated_duration_seconds = campaign.get_accumulated_durations(current_date, next_date)
        
        
        # Convert accumulated seconds to decimal hours
        accumulated_hours_total = accumulated_duration_seconds / 3600  # Convert seconds to hours
        
        # Append day and duration to lists
        days_list.append(f"{current_date.day}")
        durations_list.append(f"{accumulated_hours_total:.2f}")  # Format as decimal hours
        
        # Move to the next day
        current_date = next_date

    # Calculate the total accumulated hours and achievement percentage
    total_accumulated_seconds = sum(
        campaign.get_accumulated_durations(datetime(year, month, int(day)), 
                                            datetime(year, month, int(day)) + timedelta(days=1))
        for day in days_list
    )

    accumulated_hours_total = total_accumulated_seconds / 3600  # Convert seconds to hours

    # Calculate achievement percentage
    achievement_percentage = (accumulated_hours_total / target_hours_monthly) * 100
    remaining_hours = target_hours_monthly - accumulated_hours_total

    # Format remaining hours in decimal hours
    remaining_hours = round(remaining_hours, 2)

    remaining_hours_percentage = (remaining_hours / target_hours_monthly) * 100

    # Format achieved hours in decimal hours
    achieved_hours_total = round(accumulated_hours_total, 2)
 
    formatted_remaining_hours = format_hours_minutes(remaining_hours)
    formatted_achieved_hours_total = format_hours_minutes(achieved_hours_total)

    # Add the formatted hours to the context
    context['remaining_hours_formatted'] = formatted_remaining_hours
    context['achieved_hours_formatted'] = formatted_achieved_hours_total

    # Add the new calculations to the context
    context['achievement_percentage'] = round(achievement_percentage, 2)
    context['remaining_hours_percentage'] = round(remaining_hours_percentage, 2)
    context['remaining_hours'] = remaining_hours
    context['achieved_hours'] = achieved_hours_total
    context['days_list'] = days_list
    context['durations_list'] = durations_list

    return render(request, 'campaign_hours/daily_reports.html', context)


@permission_required('camp_hours')
@login_required
def camp_hours_monthly(request, camp_id, month, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    campaign = Campaign.objects.get(id=camp_id)
    context['campaign'] = campaign

    working_days_in_month = calculate_working_days(month, year)

    target_hours_daily = campaign.weekly_hours / 5
    target_hours_monthly = target_hours_daily * working_days_in_month

    context['target_hours_monthly'] = int(target_hours_monthly)

    start_date = make_aware(datetime(year, month, 1))  # First day of the month
    if month == 12:
        end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of December
    else:
        end_date = make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)  # Last second of the month

    # Get the accumulated duration for the specified month
    accumulated_duration_seconds = campaign.get_accumulated_durations(start_date, end_date)

    # Convert accumulated seconds to hours and minutes
    hours_accumulated, remainder = divmod(int(accumulated_duration_seconds), 3600)
    minutes_accumulated, _ = divmod(remainder, 60)

    # Format the accumulated time as HH:MM
    accumulated_duration_formatted = f"{hours_accumulated:02}:{minutes_accumulated:02}"

    # Calculate the percentage of target hours achieved
    accumulated_hours_total = accumulated_duration_seconds / 3600  # Convert seconds to hours
    achievement_percentage = (accumulated_hours_total / target_hours_monthly) * 100

    # Calculate remaining hours for the month
    remaining_hours = target_hours_monthly - accumulated_hours_total

    # Format remaining hours in HH:MM format
    remaining_hours_int = int(remaining_hours)
    remaining_minutes = int((remaining_hours - remaining_hours_int) * 60)
    remaining_hours_formatted = f"{remaining_hours_int:02}:{remaining_minutes:02}"

    remaining_hours_percentage = (remaining_hours / target_hours_monthly) * 100

    # Format achieved hours in HH:MM format
    achieved_hours_int = int(accumulated_hours_total)
    achieved_minutes = int((accumulated_hours_total - achieved_hours_int) * 60)
    achieved_hours_formatted = f"{achieved_hours_int:02}:{achieved_minutes:02}"

    # Add the new calculations to the context
    context['achievement_percentage'] = round(achievement_percentage, 2)
    context['remaining_hours_percentage'] = round(remaining_hours_percentage, 2)
    context['remaining_hours'] = round(remaining_hours, 2)  # This will give the remaining hours as a decimal
    context['remaining_hours_formatted'] = remaining_hours_formatted
    context['achieved_hours_formatted'] = achieved_hours_formatted

    # Initialize list to hold weekly hours
    weekly_hours = []
    weekly_hours_formatted = []  # Formatted weekly hours
    week_labels = []
    
    # Calculate weekly hours
    current_start_date = start_date
    while current_start_date <= end_date:
        current_end_date = current_start_date + timedelta(days=6)
        if current_end_date > end_date:
            current_end_date = end_date

        # Get the accumulated duration for the current week
        weekly_duration_seconds = campaign.get_accumulated_durations(current_start_date, current_end_date)
        weekly_hours_total = weekly_duration_seconds / 3600  # Convert seconds to hours

        # Convert weekly hours to HH:MM format
        hours, minutes = divmod(weekly_hours_total * 3600, 3600)
        formatted_hours = f"{int(hours):02}:{int(minutes / 60):02}"

        # Append numeric and formatted hours to lists
        weekly_hours.append(weekly_hours_total)
        weekly_hours_formatted.append(formatted_hours)

        # Label for the week
        week_labels.append(f"Week {len(week_labels) + 1}")

        # Move to the next week
        current_start_date = current_end_date + timedelta(days=1)

    # Add weekly hours and labels to the context
    context['week_labels'] = week_labels
    context['weekly_hours'] = weekly_hours
    context['weekly_hours_formatted'] = weekly_hours_formatted

    # Get total hours for each account
    account_data = campaign.get_total_hours_per_account(start_date, end_date)
    
    # Convert the account_data dictionary to a list of tuples
    account_hours_list = [(seat, data['formatted_time'], data['unique_agents_count']) 
                          for seat, data in account_data.items()]

    # Add account hours list to context
    context['account_hours_list'] = account_hours_list


    return render(request, 'campaign_hours/monthly_reports.html', context)




@csrf_exempt  # Use this decorator if you're not passing a CSRF token in your AJAX request
def update_agent_campaign(request, agent_id):
    if request.method == 'POST':
        campaign_id = request.POST.get('campaign_id')
        
        try:
            agent = Profile.objects.get(id=agent_id)
            campaign = Campaign.objects.get(id=campaign_id)
            agent.current_campaign = campaign
            agent.save()
            return JsonResponse({'status': 'success', 'message': 'Campaign updated successfully'})
        except Profile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Agent not found'}, status=404)
        except Campaign.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Campaign not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
@require_POST
def update_agent_login_time(request):
    try:
        # Parse the JSON body of the request
        data = json.loads(request.body)
        agent_id = data.get('agent_id')
        login_time = data.get('login_time')

        # Get the Profile object for the agent
        profile = Profile.objects.get(id=agent_id)

        # Update the login_time and save the profile
        profile.login_time = login_time
        profile.save()

        # Return a success response
        return JsonResponse({'success': True, 'message': 'Login time updated successfully.'})
    except Profile.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Agent not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)    



@permission_required('camp_hours')
@login_required
def camp_hours_yearly(request, camp_id, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['year'] = year

    # Create a datetime object for January 1st of the given year
    year_start_date = make_aware(datetime(year, 1, 1))  # First day of the year
    year_end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of the year

    # Get the campaign for the given ID
    campaign = Campaign.objects.get(id=camp_id)
    context['campaign'] = campaign

    # Calculate total working days in the year (Monday to Friday)
    working_days_in_year = calculate_working_days_in_year(year)

    # Calculate target hours
    target_hours_daily = campaign.weekly_hours / 5  # Daily target hours (assuming 5 working days a week)
    target_hours_yearly = target_hours_daily * working_days_in_year

    context['target_hours_yearly'] = int(target_hours_yearly)

    # Get the accumulated duration for the specified year
    accumulated_duration_seconds = campaign.get_accumulated_durations(year_start_date, year_end_date)

    # Convert accumulated seconds to hours and minutes
    hours_accumulated, remainder = divmod(int(accumulated_duration_seconds), 3600)
    minutes_accumulated, _ = divmod(remainder, 60)

    # Format the accumulated time as HH:MM
    accumulated_duration_formatted = f"{hours_accumulated:02}:{minutes_accumulated:02}"

    # Calculate the percentage of target hours achieved
    accumulated_hours_total = accumulated_duration_seconds / 3600  # Convert seconds to hours
    achievement_percentage = (accumulated_hours_total / target_hours_yearly) * 100

    # Calculate remaining hours for the year
    remaining_hours = target_hours_yearly - accumulated_hours_total

    # Format remaining hours in HH:MM format
    remaining_hours_int = int(remaining_hours)
    remaining_minutes = int((remaining_hours - remaining_hours_int) * 60)
    remaining_hours_formatted = f"{remaining_hours_int:02}:{remaining_minutes:02}"

    remaining_hours_percentage = (remaining_hours / target_hours_yearly) * 100

    # Format achieved hours in HH:MM format
    achieved_hours_int = int(accumulated_hours_total)
    achieved_minutes = int((accumulated_hours_total - achieved_hours_int) * 60)
    achieved_hours_formatted = f"{achieved_hours_int:02}:{achieved_minutes:02}"

    # Add the new calculations to the context
    context['achievement_percentage'] = round(achievement_percentage, 2)
    context['remaining_hours_percentage'] = round(remaining_hours_percentage, 2)
    context['remaining_hours'] = round(remaining_hours, 2)  # This will give the remaining hours as a decimal
    context['remaining_hours_formatted'] = remaining_hours_formatted
    context['achieved_hours_formatted'] = achieved_hours_formatted

    # Initialize lists to hold monthly hours
    monthly_hours = []
    monthly_hours_formatted = []  # Formatted monthly hours
    month_labels = []
    missed_hours = []  # List to hold missed hours each month
    missed_hours_formatted = []  # Formatted missed hours each month

    # Calculate monthly hours and missed hours
    for month in range(1, 13):  # Loop through each month
        current_start_date = make_aware(datetime(year, month, 1))
        if month == 12:
            current_end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)
        else:
            current_end_date = make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)

        # Get the accumulated duration for the current month
        monthly_duration_seconds = campaign.get_accumulated_durations(current_start_date, current_end_date)
        monthly_hours_total = monthly_duration_seconds / 3600  # Convert seconds to hours

        # Calculate the number of working days in the current month
        working_days_in_month = calculate_working_days_in_month(current_start_date, current_end_date)
        
        # Calculate the target hours for the current month
        target_hours_monthly = target_hours_daily * working_days_in_month

        # Calculate missed hours for the current month
        missed_hours_total = target_hours_monthly - monthly_hours_total

        # Convert monthly hours and missed hours to HH:MM format
        hours, minutes = divmod(monthly_hours_total * 3600, 3600)
        formatted_hours = f"{int(hours):02}:{int(minutes / 60):02}"
        missed_hours_int = int(missed_hours_total)
        missed_minutes = int((missed_hours_total - missed_hours_int) * 60)
        formatted_missed_hours = f"{missed_hours_int:02}:{missed_minutes:02}"

        # Append numeric and formatted hours to lists
        monthly_hours.append(monthly_hours_total)
        monthly_hours_formatted.append(formatted_hours)
        missed_hours.append(missed_hours_total)
        missed_hours_formatted.append(formatted_missed_hours)

        # Label for the month
        month_labels.append(calendar.month_name[month])

    # Add monthly hours, missed hours, and labels to the context
    context['month_labels'] = month_labels
    context['monthly_hours'] = monthly_hours
    context['monthly_hours_formatted'] = monthly_hours_formatted
    context['missed_hours'] = missed_hours
    context['missed_hours_formatted'] = missed_hours_formatted

    # Get total hours for each account
    account_data = campaign.get_total_hours_per_account(year_start_date, year_end_date)
    
    # Convert the account_data dictionary to a list of tuples
    account_hours_list = [(seat, data['formatted_time'], data['unique_agents_count']) 
                          for seat, data in account_data.items()]

    # Add account hours list to context
    context['account_hours_list'] = account_hours_list

    return render(request, 'campaign_hours/yearly_reports.html', context)


@permission_required('camp_leads')
@login_required
def all_campaigns_performance(request, month, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]
    
    # Create date range for the month
    start_date = tz.make_aware(datetime(year, month, 1))  # First day of the month
    if month == 12:
        end_date = tz.make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of December
    else:
        end_date = tz.make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)  # Last second of the month

    # Calculate the total number of working days in the month
    total_working_days = calculate_working_days_in_month(start_date, end_date)

    # Initialize dictionary for campaign performance
    campaign_performance = {}

    # Loop through each campaign
    all_campaigns = Campaign.objects.filter(campaign_type="calling")

    context['campaigns_count'] = len(all_campaigns)

    total_targets = 0
    total_achieved = 0 
    
    for campaign in all_campaigns:
        weekly_target = campaign.weekly_leads
        daily_target = weekly_target / 5  # 5 working days per week
        # Calculate the target leads for the month based on working days
        total_target_leads = daily_target * total_working_days

        # Query the leads for the current month in the campaign
        monthly_leads = Lead.objects.filter(
            campaign=campaign,
            pushed__range=[start_date, end_date]
        )


        # Filter by lead statuses
        qualified_leads = monthly_leads.filter(status='qualified').count()

        # Calculate achievement percentage
        achievement_percentage = (qualified_leads / total_target_leads) * 100 if total_target_leads > 0 else 0
        total_targets +=total_target_leads
        total_achieved +=qualified_leads

        # Add campaign performance to the dictionary
        campaign_performance[campaign.id] = {
            'campaign_name': campaign.name,  # Assuming 'name' is a field in your Campaign model
            'achieved_leads': qualified_leads,
            'target_leads': int(total_target_leads),
            'achievement_percentage': round(achievement_percentage, 2)
        }
    
    total_remaining = total_targets-total_achieved

    achieved_percentage = (total_achieved / total_targets) * 100 if total_targets > 0 else 0

    remaining_percentage = 100-achieved_percentage

    context['total_targets'] = int(total_targets)
    context['total_achieved'] = total_achieved
    context['total_remaining'] = int(total_remaining)
    context['achieved_percentage'] = round(achieved_percentage,2)
    context['remaining_percentage'] = round(remaining_percentage,2)

    # Sort campaigns by achievement percentage from least to most achieved
    sorted_campaign_performance = dict(sorted(campaign_performance.items(), key=lambda item: item[1]['achievement_percentage']))

    # Prepare data for JavaScript
    campaign_names = [v['campaign_name'] for v in sorted_campaign_performance.values()] 
    achieved_leads = [v['achieved_leads'] for v in sorted_campaign_performance.values()]
    target_leads = [v['target_leads'] for v in sorted_campaign_performance.values()] 

    context['campaign_names'] = json.dumps(campaign_names)
    context['achieved_leads'] = json.dumps(achieved_leads)
    context['target_leads'] = json.dumps(target_leads)



    return render(request, 'campaign_leads/overall_performance.html', context)


@permission_required('camp_leads')
@login_required
def camp_leads_daily(request, camp_id, month, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    # Get the campaign
    campaign = Campaign.objects.get(id=camp_id)
    context['campaign'] = campaign

    weekly_target = campaign.weekly_leads
    daily_target = weekly_target / 5  # 5 working days per week

    # Create a datetime object for the given month
    month_date = datetime(year, month, 1)
    month_name = month_date.strftime('%b')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]

    # Create date range for the month
    start_date = make_aware(datetime(year, month, 1))  # First day of the month
    if month == 12:
        end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of December
    else:
        end_date = make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)  # Last second of the month

    # Initialize lists for each lead status
    daily_qualified = []
    daily_disqualified = []
    daily_duplicated = []
    daily_callback = []
    day_labels = []

    # Initialize variables for total leads
    total_qualified = 0
    total_disqualified = 0
    total_duplicated = 0
    total_callback = 0

    # Loop through each day in the month
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        # Query the leads for the current day in the campaign
        daily_leads = Lead.objects.filter(
            campaign=campaign,
            pushed__date=current_date.date()
        )
        
        # Filter by lead statuses
        qualified_leads = daily_leads.filter(status='qualified').count()
        disqualified_leads = daily_leads.filter(status='disqualified').count()
        duplicated_leads = daily_leads.filter(status='duplicated').count()
        callback_leads = daily_leads.filter(status="callback").count()

        # Append counts to the respective lists
        daily_qualified.append(qualified_leads)
        daily_disqualified.append(disqualified_leads)
        daily_duplicated.append(duplicated_leads)
        daily_callback.append(callback_leads)

        # Update total counts
        total_qualified += qualified_leads
        total_disqualified += disqualified_leads
        total_duplicated += duplicated_leads
        total_callback += callback_leads

        # Append day label
        day_labels.append(f"{current_date.day}")
        
        # Move to the next day
        current_date = next_date

    # Calculate the total number of working days in the month
    total_working_days = calculate_working_days_in_month(start_date, end_date)

    # Calculate the target leads for the month based on working days
    total_target_leads = daily_target * total_working_days

    # Add data to context
    context['day_labels'] = json.dumps(day_labels)
    context['daily_qualified'] = json.dumps(daily_qualified)
    context['daily_disqualified'] = json.dumps(daily_disqualified)
    context['daily_duplicated'] = json.dumps(daily_duplicated)
    context['daily_callback'] = json.dumps(daily_callback)

    # Calculate achievement percentage
    achievement_percentage = (total_qualified / total_target_leads) * 100 if total_target_leads > 0 else 0

    # Calculate remaining leads
    remaining_leads = total_target_leads - total_qualified

    # Calculate remaining percentage
    remaining_percentage = (remaining_leads / total_target_leads) * 100 if total_target_leads > 0 else 0

    # Format results
    context['daily_target'] = int(daily_target)
    context['achievement_percentage'] = round(achievement_percentage, 2)
    context['remaining_leads'] =  int(remaining_leads)
    context['achieved_leads'] = total_qualified
    context['remaining_percentage'] = round(remaining_percentage, 2)


    return render(request, 'campaign_leads/daily_reports.html', context)

@permission_required('camp_leads')
@login_required
def camp_leads_monthly(request, camp_id, month, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    # Get the campaign
    campaign = Campaign.objects.get(id=camp_id)
    context['campaign'] = campaign

    weekly_target = campaign.weekly_leads
    daily_target = weekly_target / 5  # 5 working days per week

    
    month_date = datetime(year, month, 1)  # Create a datetime object for the given month
    month_name = month_date.strftime('%b')  # Get the abbreviated month name (e.g., 'Sep')
    context['year'] = year
    context['month'] = month
    context['month_name'] = month_name
    context['full_month_name'] = calendar.month_name[month]


    # Create date range for the month
    start_date = make_aware(datetime(year, month, 1))  # First day of the month
    if month == 12:
        end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of December
    else:
        end_date = make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)  # Last second of the month

    # Calculate the total number of working days in the month
    total_working_days = calculate_working_days_in_month(start_date, end_date)
    
    # Calculate the target leads for the month based on working days
    total_target_leads = daily_target * total_working_days

    # Initialize lists for each lead status
    weekly_qualified = []
    weekly_disqualified = []
    weekly_duplicated = []
    weekly_callback = []
    week_labels = []

    # Initialize variables for total leads
    total_qualified = 0
    total_disqualified = 0
    total_duplicated = 0
    total_callback = 0

    # Loop through each week in the month
    current_start_date = start_date
    week_number = 1  # For labeling weeks
    while current_start_date <= end_date:
        current_end_date = current_start_date + timedelta(days=6)
        if current_end_date > end_date:
            current_end_date = end_date

        # Query the leads for the current week in the campaign
        weekly_leads = Lead.objects.filter(
            campaign=campaign,
            pushed__range=[current_start_date, current_end_date]
        )

        

        # Filter by lead statuses
        qualified_leads = weekly_leads.filter(status='qualified').count()
        disqualified_leads = weekly_leads.filter(status='disqualified').count()
        duplicated_leads = weekly_leads.filter(status='duplicated').count()
        callback_leads = weekly_leads.filter(status="callback").count()

        # Append counts to the respective lists
        weekly_qualified.append(qualified_leads)
        weekly_disqualified.append(disqualified_leads)
        weekly_duplicated.append(duplicated_leads)
        weekly_callback.append(callback_leads)

        # Update total counts
        total_qualified += qualified_leads
        total_disqualified += disqualified_leads
        total_duplicated += duplicated_leads
        total_callback += callback_leads

        # Append week label
        week_labels.append(f"Week {week_number}")
        week_number += 1

        # Move to the next week
        current_start_date = current_end_date + timedelta(days=1)

    # Add data to context
    context['week_labels'] = json.dumps(week_labels)
    context['weekly_qualified'] = json.dumps(weekly_qualified)
    context['weekly_disqualified'] = json.dumps(weekly_disqualified)
    context['weekly_duplicated'] = json.dumps(weekly_duplicated)
    context['weekly_callback'] = json.dumps(weekly_callback)

    # Calculate achievement percentage
    achievement_percentage = (total_qualified / total_target_leads) * 100 if total_target_leads > 0 else 0

    # Calculate remaining leads
    remaining_leads = total_target_leads - total_qualified

    # Calculate remaining percentage
    remaining_percentage = (remaining_leads / total_target_leads) * 100 if total_target_leads > 0 else 0

    # Format results
    context['total_target_leads'] = int(total_target_leads)
    context['achievement_percentage'] = round(achievement_percentage, 2)
    context['remaining_leads'] =  int(remaining_leads)
    context['achieved_leads'] = total_qualified
    context['remaining_percentage'] = round(remaining_percentage, 2)

    return render(request, 'campaign_leads/monthly_reports.html', context)



@permission_required('camp_leads')
@login_required
def camp_leads_yearly(request, camp_id, year):
    context = {"settings": settings}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile
    context['year'] = year

    # Get the campaign for the given ID
    campaign = Campaign.objects.get(id=camp_id)
    context['campaign'] = campaign

    # Get the total number of working days in the year
    working_days_in_year = calculate_working_days_in_year(year)

    # Calculate weekly target leads
    weekly_target = campaign.weekly_leads
    daily_target = weekly_target / 5  # 5 working days per week
    total_target_leads_yearly = daily_target * working_days_in_year

    # Initialize lists for each month's data
    monthly_qualified = []
    monthly_disqualified = []
    monthly_duplicated = []
    monthly_callback = []
    month_labels = []
    
    total_qualified = 0
    total_disqualified = 0
    total_duplicated = 0
    total_callback = 0

    # Loop through each month in the year
    for month in range(1, 13):  # From January to December
        month_date = datetime(year, month, 1)
        month_name = month_date.strftime('%b')  # Abbreviated month name (e.g., 'Jan')
        month_labels.append(calendar.month_name[month])

        # Define the start and end dates for the current month
        start_date = make_aware(datetime(year, month, 1))  # First day of the month
        if month == 12:
            end_date = make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)  # Last second of December
        else:
            end_date = make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)  # Last second of the month

        # Query the leads for the current month
        monthly_leads = Lead.objects.filter(
            campaign=campaign,
            pushed__range=[start_date, end_date]
        )

        # Filter by lead statuses
        qualified_leads = monthly_leads.filter(status='qualified').count()
        disqualified_leads = monthly_leads.filter(status='disqualified').count()
        duplicated_leads = monthly_leads.filter(status='duplicated').count()
        callback_leads = monthly_leads.filter(status="callback").count()

        # Append counts to the respective lists
        monthly_qualified.append(qualified_leads)
        monthly_disqualified.append(disqualified_leads)
        monthly_duplicated.append(duplicated_leads)
        monthly_callback.append(callback_leads)

        # Update total counts
        total_qualified += qualified_leads
        total_disqualified += disqualified_leads
        total_duplicated += duplicated_leads
        total_callback += callback_leads

    # Calculate annual statistics
    achievement_percentage = (total_qualified / total_target_leads_yearly) * 100 if total_target_leads_yearly > 0 else 0
    remaining_leads = total_target_leads_yearly - total_qualified
    remaining_percentage = (remaining_leads / total_target_leads_yearly) * 100 if total_target_leads_yearly > 0 else 0

    # Add data to context
    context['month_labels'] = month_labels
    context['monthly_qualified'] = json.dumps(monthly_qualified)
    context['monthly_disqualified'] = json.dumps(monthly_disqualified)
    context['monthly_duplicated'] = json.dumps(monthly_duplicated)
    context['monthly_callback'] = json.dumps(monthly_callback)
    
    context['total_target_leads_yearly'] = int(total_target_leads_yearly)
    context['total_qualified'] = total_qualified
    context['achievement_percentage'] = round(achievement_percentage, 2)
    context['remaining_leads'] = int(remaining_leads)
    context['remaining_percentage'] = round(remaining_percentage, 2)


    return render(request, 'campaign_leads/yearly_reports.html', context)






@permission_required('operations')
@login_required
def company_tasks(request, year):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    context['year'] = year

    tasks = Task.objects.filter(active=True, created__year=year)

    # Create a dictionary to hold lists of sales leads for each status choice
    tasks_grouped = {choice[0]: [] for choice in TASK_DEPARTMENTS}  # Initialize with empty lists

    # Iterate over each sales lead and group by status
    for task in tasks:
        tasks_grouped[task.assigned_department].append(task)

    # Prepare the context with grouped sales leads
    context['tasks'] = tasks_grouped

    # Include the names of the statuses in your context as well
    context['task_departments'] = dict(TASK_DEPARTMENTS)



   

    return render(request, 'operations/company_tasks.html', context)




@permission_required('company_tasks')
@login_required
def task_creation(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    now = tz.now()
    current_year = now.year

   


    # Include the names of the statuses in your context as well
    context['task_departments'] = dict(TASK_DEPARTMENTS)

    if request.method == "POST":
        data = request.POST

        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        priority = int(data.get('priority'))
        department = data.get('department')
        task_notes = data.get('task_notes')

        

        task = Task.objects.create(agent_user=request.user,
                                   agent_profile=profile,
                                    title=title,
                                   description=description,
                                   due = due_date,
                                   priority=priority,
                                   assigned_department=department,
                                   notes=task_notes)

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

           
            task_id = task.id

            department = task.get_assigned_department_display()

            task_title = task.title

            task_due = task.due

            action_type= "create"

            content = f'**Agent:** {profile.full_name}\n\n**Action:** Task Creation \n\n**Department:** {str(department).upper()}\n\n**Title:** {task_title}\n\n**Due Date:** {task_due}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

            send_discord_message_task(content,task_id,action_type)
            
        except:
            pass
        


        
        return redirect(f'/company-tasks-{current_year}')




   

    return render(request, 'operations/task_create.html', context)




@permission_required('company_tasks')
@login_required
def task_info(request, task_id):
    context = {}
    profile = Profile.objects.get(user=request.user)
    context['profile'] = profile

    now = tz.now()
    current_year = now.year


    task = Task.objects.get(id=task_id)

    context['task'] = task

   


    # Include the names of the statuses in your context as well
    context['task_departments'] = dict(TASK_DEPARTMENTS)
    context['task_statuses'] = dict(TASK_RESULT_CHOICES)

    if request.method == "POST":
        data = request.POST

        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        priority = int(data.get('priority'))
        department = data.get('department')
        task_notes = data.get('task_notes')
        task_status = data.get('task_status')

        
        task = Task.objects.get(id=task_id)

        old_task_dep = task.get_assigned_department_display()

        old_status = task.get_status_display()

        
        task.title=title
        task.description=description
        task.due = due_date
        task.priority=priority
        task.assigned_department=department
        task.notes=task_notes
        task.status = task_status

        task.save()

        new_task_dep = task.get_assigned_department_display()

        new_status = task.get_status_display()

        utc_now = datetime.utcnow()

        # Get the timezone object for 'America/New_York'
        est_timezone = pytz.timezone('America/New_York')

        # Convert UTC time to Eastern timezone
        est_time = utc_now.replace(tzinfo=pytz.utc).astimezone(est_timezone)

        # Format the time as HH:MM:SS string
        est = est_time.strftime('%I:%M:%S %p')


        # Construct the content of the embed with quote formatting
        request_ip = request.META.get('REMOTE_ADDR')

           
        task_id = task.id

        department = task.get_assigned_department_display()

        task_title = task.title

        task_due = task.due

        action_type= "reassign"

            

        if new_task_dep != old_task_dep:

            try:


                content = f'**Agent:** {profile.full_name}\n\n**Action:** Task Reassignment \n\n**Departments:** \n{str(old_task_dep).upper()} > {str(new_task_dep).upper()}\n\n**Title:** {task_title}\n\n**Due Date:** {task_due}\n\n**Status:** {new_status}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

                send_discord_message_task(content,task_id,action_type)

            except:
                pass

        elif old_status != new_status:
            try:


                content = f'**Agent:** {profile.full_name}\n\n**Action:** Task Status Update \n\n**Department: **  {str(new_task_dep).upper()}\n\n**Title:** {task_title}\n\n**Due Date:** {task_due}\n\n**Status:** {old_status} > {new_status}\n\n**Eastern:** {est}\n\n**IP Address:** {request_ip} '

                send_discord_message_task(content,task_id,action_type)

            except:
                pass

        


    

        
        
        return redirect(f'/company-tasks-{current_year}')




   

    return render(request, 'operations/task_info.html', context)