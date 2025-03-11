from django.db import models
from django.contrib.auth.models import User
from nedialo.constants import US_STATES_CHOICES,COUNTRIES_CHOICES
from django.template.defaultfilters import slugify  # new
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware

from datetime import timedelta, datetime
import os,uuid,secrets
from django.db.models import Sum, F, ExpressionWrapper, DurationField

import uuid


STATUS_CHOICES = (
    ('active','Active'),
    ('upl', 'UPL'),
    ('annual','Annual'),
    ('casual','Casual'),
    ('sick','Sick'),
    ('hold','Hold'),
    ('dropped','Dropped'),
    ('blacklisted','Blacklisted'),
)

THEME_CHOICES = (
    ("white","White"),
    ("dark","Dark"),
)

PAYMENT_CHOICES = (
    ("payoneer","Payoneer"),
    ("instapay","InstaPay"),
)


TEAM_TYPES = (
    ('callers', 'Cold Callers'),
    ('sales', 'Sales'),
    ('dispo', 'Dispositions'),
    ('acq', 'Acquisitions'),
    ('data', 'Data Management'),
    ('quality', 'Quality'),
    ('team_leaders', 'Team Leaders'),
)

CONTRACT_FIELD_TYPES = (
    ('roofing', 'Roofing'),
    ('realestate', 'Real Estate'),
)


CONTRACT_PREF_PROPERTY_TYPE = (
    ('residential','Residential'),
    ('commercial','Commercial'),
    ('both','Residential & Commercial')
)

CONTRACT_PREF_PROPERTY_TYPE_RE = (
    ('residential','Residential'),
    ('commercial','Commercial'),
    ('lands','Vacant Lands'),
    ('parks','Parks'),

)

CONTRACT_PREF_OWNER_TYPE = (
    ('individual','Individual'),
    ('corporate','Corporate'),
    ('any','Any')

)




CONTRACT_PREF_RE_RESD_TYPES = (
    ('sfh','Single Family'),
    ('mfh','Multi Family'),
    ('condo','Condos/Townhoueses'),
    ('mobile','Mobile Homes'),

)


CONTRACT_PREF_PRICE_RANGES = (
    ("less_200","$50k-$200k"),
    ('less_500', "$200k-$500k"),
    ('less_800','$500k-$800k'),
    ('less_1000','$800k-$1M'),
    ('less_5000','$1M-$5M'),
    ('more_5000','$5M+'),

)

APPLICATION_POS_CHOICES = (
    ("cold_caller", "Cold Caller"),
    ("acq_manager", "Acquisition Manager"),
    ("dispo_manager","Disposition Manager"),
    ("data_manager","Data Manager"),
    ('sales', "Sales")

)

APPLICATION_LANG_CHOICES = (
    ('basic', "Basic"),
    ('conversational', 'Conversational'),
    ('fluent', 'Fluent'),
    ('native', 'Native'),

)
APPLICATION_SKILLS_CHOICES = (
    ('bi_lingual',"Bilingual"),
    ('cold_caller', 'Cold Caller'),
    ('lead_manager', 'Lead Manager'),
    ('dispositions_manager', 'Dispositions Manager'),
    ('acqusitions_manager', 'Acquisitions Manager'),
    ('data_manager', 'Data Manager'),
    ('b2c_sales','B2C Sales'),
    ('b2b_sales','B2B Sales'),
    ('csr', 'Customer Service Rep'),
    ('quality', 'QA Specialist'),
    ('team_leader','Team Leader'),
    ('account_manager','Account Manager'),
    ('opm','Operations Manager'),
    ('none', 'None'),
    ('real_estate','Real Estate'),
    ('roofing','Roofing'),
    ('solar','Solar'),
    ('data_entry','Data Entry'),
    ('hr','Human Resources'),
    ('social_media','Social Media Moderator'),
    ('assistant_manager','Assistant Manager'),
    ('technical_support','Technical Support'),
    ('appointment_setter','Appointment Setter'),
    
)

APPLICATION_EDU_CHOICES = (
    ("highschool", "High School"),
    ("undergraduate", "Undergradute"),
    ("bachelors","Bachelors"),
    ("mba","MBA"),

)

APPLICATION_SHIFT_CHOICES = (
    ("part_time", "Part Time"),
    ("full_time","Full Time"),

)


APPLICATION_STATUS_CHOICES = (
    
    ('pending', 'Pending'),
    ('panel_1', "Proficent English"),
    ('panel_2', "Waiting Interview"),
    ('panel_3', 'Standby'),
    ('rejected', 'Rejected'),
    ('accepted','Hired'),
)

APPLICATION_PANEL_CHOICES = (
    
    ('pending', 'Pending'),
    ('panel_1', "Proficent English"),
    ('panel_2', "Waiting Interview"),
    ('panel_3', 'Standby'),
    ('rejected', 'Rejected'),
    ('accepted','Hired'),
)



LEAD_CHOICES = (
    ('pending','Pending'),
    ('qualified', 'Qualified'),
    ('disqualified','Disqualified'),
    ('callback', 'Callback'),
    ('duplicated', 'Duplicated'),
   
)


LEAD_TYPE_CHOICES = (

    ('realestate', 'Real Estate'),
    ('roofing', 'Roofing'),
)




SALES_LEAD_CHOICES = (
    ("follow_up","Follow Up" ),
    ("scheduled_meeting","Scheduled Meeting"),
    ('no_show','No Show'),
    ('send_contract',"To-Send Contract"),
    ('follow_up_landing', "Follow Up-Landing"),
    ('landed','Landed'),
    ('longterm_follow_up', 'Long Term Follow Up'),
    ('unresponsive', 'Unresponsive'),
    ('not_interested', 'Not Interested'),
    ('archive', 'Archive')

    )


TASK_DEPARTMENTS = (
    ('executive_dep','Executive Management'),
    ('ops_dep', 'Operations Management'),
    ('data_dep', 'Data Management'),
    ('workforce_dep','Workforce'),
    ('quality_dep','Quality'),
    ('dev_dep','Development'),
    ('sales_dep', 'Sales'),
    ('hr_dep','Human Resources'),
    ('accounting_dep','Accounting'),
    ('archive','Archive')
)

TASK_RESULT_CHOICES = (
    ('in_progress', 'In Progress'),
    ('on_hold', 'On Hold'),
    ('blocked','Blocked'),
    ('cancelled','Cancelled'),
    ('completed', 'Completed'),


)

PROPERTY_CHOICES = (
    ('house','House'),
    ('vacant_land','Vacant Land'),
    ('business', 'Business'),
    ('apartment', 'Apartment'),
    ('condo', 'Condo'),
    ('mobile_home','Mobile Home'),
)

TIMELINE_CHOICES = (
    ('two_weeks', "2 Weeks"),
    ('one_month', "1 Month"),
    ('two_months', "2 Months"),
    ('three_months', "3 Months"),
    ('four_months', "4 Months"),
    ('five_months', "5 Months"),
    ('six_months', "6 Months"),
    ('more_than_six_months', "+6 Months"),



)


CAMP_ACTIVITY = (
    ('active', 'Active'),
    ('hold', 'Hold'),
    ('pending','Pending'),
    ('inactive', 'Inactive'),
)

SALARY_TYPE = (
    ('monthly','Monthly'),
    ('hourly', 'Hourly'),
)

DISCOVERY_TYPE = (

    ("affiliate", "Affiliate"),
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("batchservice", "Batchservice"),
    ("linkedin", "Linkedin"),
    ("upwork", "Upwork or other freelancing sites"),
    ("google_search", "Google Search"),
    ("google_ads", "Google Ads"),
    ("twitter", "Twitter"),
    ("youtube", "YouTube"),
    ("tiktok", "TikTok"),
    ("pinterest", "Pinterest"),
    ("referral", "Referral from a Friend"),
    ("email_newsletter", "Email Newsletter"),
    ("outreach_call", "Outreach Representative Calls")
)

APPLICATION_DISCOVERY = (
    ("facebook",'Facebook'),
    ("instagram",'Instagram'),
    ('linkedin', 'Linkedin'),
    ('referral','Referral'),
    ('company_website','Company Website'),
    ('job_portal','Job Portal'),
    ('direct_messages','Direct Messages'),
    ('recruiter', 'Recruiter'),
    ('other','Other'),
)

SERVICE_TYPES = (
    ('calling','Calling Service'),
    ('texting', 'Texting Service'),
    ('email', 'Email Service'),
    ('admin', 'Admin Service'),
    ('marketing', 'Marketing Service'),
    ('sales', 'Sales Service'),
)

DIALER_TYPES = (
    ('calling','Calling'),
    ('texting','Texting'),

)

DIALERS = (
    ('batchdialer', 'BatchDialer'),
    ('east1_calltools', 'east-1.calltools.io'),
    ('east2_calltools', 'east-2.calltools.io'),
    ('west2_calltools', 'west-2.calltools.io'),
    ('west3_calltools', 'west-3.calltools.io'),
    ('west4_calltools', 'west-4.calltools.io'),
    ('app_calltools', 'app.calltools.io'),
    ('staging_calltools', 'staging.calltools.io'),




)


DATASOURCE_TYPES = (
    ('pulling',"List Pulling"),
    ('skip_tracing', "Skip Tracing"),
    ('skip_pull', 'List Pulling & Skip Tracing'),
    ('data_management','Data Management'),
    ('crm', 'CRM'),

)


DIALER_ACCOUNT_TYPE = (
    ('agent','Agent'),
    ('supervisor', 'Supervisor'),
    ('admin', 'Admin'),
)

SOURCE_ACCOUNT_TYPE = (
    ('full_access','Full Access'),
    ('limited_access','Limited Access'),
)

LIST_STATUS_CHOICES = (
    ('pulled', 'Pulled'),
    ('being_dialed', 'Being Dialed'),
    ('paused','Paused'),
    ('dialed','Dialed'),
)

LEAVE_CHOICES = (
    ('upl', 'UPL'),
    ('annual','Annual'),
    ('casual','Casual'),
    ('sick','Sick'),
)

ABSENCE_CHOICES = (
    ('annual','Annual'),
    ('casual','Casual'),
    ('sick','Sick'),
    ('upl', 'UPL'),
    ('nsnc', 'No Show No Call')
)


ACTION_CHOICES = (
    ('warning','Written Warning'),
    ('deduction','Deduction'),
    ('termination','Termination'),
)


REQUESTS_STATUS_CHOICES = (
    ('pending','Pending'),
    ('approved','Approved'),
    ('rejected','Rejected'),
)

FEEDBACK_CHOICES = (
    ('single','Single'),
    ('monthly','Monthly'),
)



FEEDBACK_STATUS_CHOICES = (
    ('pending','Pending'),
    ('approved','Approved'),
    ('rejected','Rejected'),
)

FEEDBACK_TYPE_CHOICES = (
    ('positive', 'Positive'),
    ('negative', 'Negative'),
    ('neutral', 'Neutral'),
)

class ServerSetting(models.Model):
    
    company_name = models.CharField(max_length=50, null=True,blank=True)
    company_website = models.CharField(max_length=50, null=True,blank=True)
    crm_domain = models.CharField(max_length=50, null=True,blank=True)
    logo_main = models.ImageField(upload_to="server_settings",null=True,blank=True)
    logo_login = models.ImageField(upload_to="server_settings",null=True,blank=True)
    favicon = models.ImageField(upload_to="server_settings",null=True,blank=True)
    apple_touch_icon = models.ImageField(upload_to="server_settings",null=True,blank=True)

    logo_dashboard_width = models.CharField(max_length=10,null=True,blank=True)
    logo_dashboard_height = models.CharField(max_length=10,null=True,blank=True)




    facebook = models.URLField(null=True,blank=True, default="/")
    instagram = models.URLField(null=True,blank=True, default="/")
    linkedin = models.URLField(null=True,blank=True, default="/")
    about_us = models.URLField(null=True,blank=True, default="/")
    privacy = models.URLField(null=True, blank=True, default="/")

    terms = models.URLField(null=True, blank=True, default="/")

    



    monthly_leadpoints_target= models.PositiveIntegerField(default=0, null=True, blank=True)
    negative_percentage = models.PositiveIntegerField(default=60, null=True, blank=True)
    neutral_percentage = models.PositiveIntegerField(default=80, null=True, blank=True)
    break_paid = models.BooleanField(default=False)
    
    
    sales_lookerstudio = models.TextField(blank=True, null=True)

    logins_webhook = models.TextField(blank=True, null=True)
    activity_webhook = models.TextField(blank=True, null=True)
    leads_webhook = models.TextField(blank=True, null=True)
    requests_webhook = models.TextField(blank=True, null=True)
    applications_webhook = models.TextField(blank=True, null=True)
    prepayments_webhook = models.TextField(blank=True, null=True)
    tasks_webhook = models.TextField(blank=True, null=True)
    sales_webhook = models.TextField(blank=True, null=True)
    clients_webhook = models.TextField(blank=True, null=True)


    whatsapp_template = models.TextField(blank=True, null=True)

    maintenance = models.BooleanField(default=False)

class Role(models.Model):
    role_name = models.CharField(max_length=50, null=True, blank=True)





    work_status = models.BooleanField(default=False)

    client_dashboard = models.BooleanField(default=False)
    client_lookerstudio = models.BooleanField(default=False)
    client_campaign_performance = models.BooleanField(default=False)

    affiliate_dashboard = models.BooleanField(default=False)

    caller_dashboard = models.BooleanField(default=False)

    lead_submission = models.BooleanField(default=False)
    my_leads = models.BooleanField(default=False)
    lead_scoring = models.BooleanField(default=False)
    leaderboard = models.BooleanField(default=False)

    campaign_documentation = models.BooleanField(default=False)
    campaign_sop = models.BooleanField(default=False)


    leave_request = models.BooleanField(default=False)
    prepayment_request = models.BooleanField(default=False)
    action_request = models.BooleanField(default=False)

    leave_handling = models.BooleanField(default=False)
    prepayment_handling = models.BooleanField(default=False)
    action_handling = models.BooleanField(default=False)
    delete_handling_request = models.BooleanField(default=False)

    qa_pending = models.BooleanField(default=False)
    qa_lead_handling = models.BooleanField(default=False)
    qa_unassign_lead = models.BooleanField(default=False)
    qa_lead_reports = models.BooleanField(default=False)
    qa_auditing = models.BooleanField(default=False)
    qa_auditing_handling = models.BooleanField(default=False)
    qa_agents_table = models.BooleanField(default=False)


    seats = models.BooleanField(default=False)
    camp_hours = models.BooleanField(default=False)
    camp_leads = models.BooleanField(default=False)

    dialer_reports = models.BooleanField(default=False)

    sales_dashboard = models.BooleanField(default=False)
    sales_lookerstudio = models.BooleanField(default=False)
    sales_performance = models.BooleanField(default=False)


    agents_table = models.BooleanField(default=False)
    working_hours = models.BooleanField(default=False)
    attendance_monitor = models.BooleanField(default=False)
    lateness_monitor = models.BooleanField(default=False)

    salaries_table = models.BooleanField(default=False)
    adjusting_hours = models.BooleanField(default=False)

    company_tasks = models.BooleanField(default=False)

    operations = models.BooleanField(default=False)


    admin_home = models.BooleanField(default=False)

    admin_applications = models.BooleanField(default=False)

    admin_accounts = models.BooleanField(default=False)
    admin_clients = models.BooleanField(default=False)
    admin_affiliates = models.BooleanField(default=False)

    admin_campaigns = models.BooleanField(default=False)
    admin_contactlists = models.BooleanField(default=False)

    admin_roles = models.BooleanField(default=False)
    admin_provided_services = models.BooleanField(default=False)
    admin_dialers = models.BooleanField(default=False)
    admin_sources = models.BooleanField(default=False)
    admin_packages = models.BooleanField(default=False)
    admin_contracts = models.BooleanField(default=False)

    admin_server_settings = models.BooleanField(default=False)


    active=models.BooleanField(default=True)



    ROLE_FIELD_NAMES = {
        "work_status": "Work Status",
        "client_dashboard": "Client Dashboard (Client Role Only)",
        "client_lookerstudio": "Client Looker Studio (Client Role Only)",
        "client_campaign_performance": "Client Campaign Performance (Client Role Only)",
        "affiliate_dashboard": "Affiliate Dashboard (Affiliate Role Only)",
        "caller_dashboard": "Caller Dashboard",
        "lead_submission": "Lead Submission",
        "my_leads": "My Leads",
        "lead_scoring": "Lead Scoring",
        "leaderboard": "Leaderboard",
        "campaign_documentation": "Campaigns Documentation",
        'campaign_sop':"QA Pushing SOP",
        "leave_request": "Leave Request",
        "prepayment_request": "Prepayment Request",
        "action_request": "Action Request",
        "leave_handling": "Leave Handling",
        "prepayment_handling": "Prepayment Handling",
        "action_handling": "Action Handling",
        "delete_handling_request": "Delete Handling Request",
        "qa_pending": "QA Pending",
        "qa_lead_handling": "QA Lead Handling",
        "qa_unassign_lead": "QA Lead Unassignment",
        "qa_lead_reports": "QA Lead Reports",
        "qa_auditing": "QA Auditing",
        "qa_auditing_handling": "QA Auditing Handling",
        "qa_agents_table": "QA Agents Table",
        "seats": "Seats",
        "camp_hours": "Campaign Hours",
        "camp_leads": "Campaign Leads",
        "dialer_reports": "Dialer Reports",
        "sales_dashboard": "Sales Dashboard",
        "sales_lookerstudio": "Sales Looker Studio",
        "sales_performance": "Sales Performance",
        "agents_table": "Agents Table",
        "working_hours": "Working Hours",
        "attendance_monitor": "Attendance Monitor",
        "lateness_monitor": "Lateness Monitor",
        "salaries_table": "Salaries Table",
        "adjusting_hours": "Adjusting Hours",
        "company_tasks": "Company Tasks",
        "operations": "Operations",
        "admin_home": "Admin Home",
        "admin_applications": "Admin Applications",
        "admin_accounts": "Admin Accounts",
        "admin_clients": "Admin Clients",
        "admin_affiliates": "Admin Affiliates",
        "admin_campaigns": "Admin Campaigns",
        "admin_contactlists": "Admin Contact Lists",
        "admin_roles": "Admin Roles",
        "admin_provided_services": "Admin Provided Services",
        "admin_dialers": "Admin Dialers",
        "admin_sources": "Admin Third-Parties",
        "admin_packages": "Admin Packages",
        "admin_contracts": "Admin Contracts",
        "admin_server_settings": "Admin Server Settings",
        }


    def __str__(self):
        return str(self.role_name)
    
    def get_field_labels(self):
        # Use self.__class__.ROLE_FIELD_NAMES to reference class-level attribute
        return {
            field.name: self.__class__.ROLE_FIELD_NAMES.get(field.name, field.name)
            for field in self._meta.fields
        }
    



class Application(models.Model):

    app_uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

    submission_date = models.DateTimeField(default=timezone.now)
    referrer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=50, choices=APPLICATION_POS_CHOICES, null=True, blank=True)
    full_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    education = models.CharField(max_length=50, choices=APPLICATION_EDU_CHOICES,null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    app_discovery = models.CharField(max_length=50, choices=APPLICATION_DISCOVERY,null=True, blank=True)
    discovery_details = models.CharField(max_length=255, blank=True, null=True) ## for more details on discovery
    shift = models.CharField(max_length=50, choices=APPLICATION_SHIFT_CHOICES,null=True, blank=True)
    language_exp = models.CharField(max_length=50, choices=APPLICATION_LANG_CHOICES,null=True, blank=True)

    skills = models.JSONField(default=list, blank=True, null=True)  # JSON field for skills

    recording_link = models.CharField(max_length=50, null=True, blank=True)
    
    audio_file = models.FileField(upload_to='applications_audio', blank=True, null=True)
    status = models.CharField(max_length=50, choices=APPLICATION_STATUS_CHOICES, blank=True, null=True,default="pending")
    comments = models.TextField(null=True, blank=True)
    handled_by = models.ForeignKey(User,on_delete=models.SET_NULL, related_name="handled_by_app",null=True,blank=True)

    active = models.BooleanField(default=True)

class Team(models.Model):
    team_name = models.CharField(max_length=50, null=True, blank=True)
    team_type = models.CharField(max_length=50, choices=TEAM_TYPES, blank=True, null=True)
    team_leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.team_name)

def random_name_national_id(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('national_ids/', filename)

def random_name_leave_files(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('leave_files/', filename)

def random_name_contract_files(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('contract_files/', filename)



def random_name_action_files(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('action_files/', filename)


def random_name_profile_pic(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('profile_images/', filename)


class Service(models.Model): #Company Provided Services
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=100, choices=SERVICE_TYPES, null=True, blank=True)
    status = models.CharField(max_length=50, default="active", choices=CAMP_ACTIVITY, null=True, blank=True)
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.name







    




    



class Dialer(models.Model): # Dialers List
    name = models.CharField(max_length=50, null=True, blank=True)
    dialer_type = models.CharField(max_length=50, choices=DIALER_TYPES, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DataSource(models.Model): # List Pull & Skip Tracing Sources

    name = models.CharField(max_length=50, null=True, blank=True)
    source_type = models.CharField(max_length=50, choices=DATASOURCE_TYPES, null=True, blank=True)
    data_source = models.BooleanField(default=True)

    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name



class AffiliateProfile(models.Model): #Profile Standard Information
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)
    picture = models.ImageField(upload_to=random_name_profile_pic, blank=True, null=True)
    full_name = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=50,blank=True,null=True)
    joining_date = models.DateField(blank=True, null=True)
    role = models.ForeignKey(Role, blank=True, null=True, related_name="affiliate_profile_role", on_delete=models.SET_NULL)

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50,null=True,blank=True)
    state = models.CharField(max_length=50, choices=US_STATES_CHOICES, null=True, blank=True)
    client_status = models.CharField(max_length=50, choices=CAMP_ACTIVITY, default='active',null=True, blank=True)
    discovery_method = models.CharField(max_length=20 , choices=DISCOVERY_TYPE, blank=True, null=True)

    commission_percentage = models.FloatField(blank=True, null=True)


    settings_theme = models.CharField(max_length=50,default="dark", choices=THEME_CHOICES)
    maps_theme = models.CharField(max_length=50,default="dark", choices=THEME_CHOICES)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.id:  # Check if the object has an ID (i.e., it's a new object)
            # Get the last ID in the table and increment by 1
            last_agent = AffiliateProfile.objects.order_by('-id').first()
            if last_agent:
                self.id = last_agent.id + 1
            else:
                self.id = 8000  # Start with ID 1000 if no agents exist yet
        super().save(*args, **kwargs)



class ClientProfile(models.Model): #Profile Standard Information
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)
    picture = models.ImageField(upload_to=random_name_profile_pic, blank=True, null=True)
    full_name = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=50,blank=True,null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL,blank=True,null=True)
    joining_date = models.DateField(blank=True, null=True)
    birth_date = models.DateField(blank=True,null=True)
    role = models.ForeignKey(Role, blank=True, null=True, related_name="client_profile_role", on_delete=models.SET_NULL)

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50,null=True,blank=True)
    state = models.CharField(max_length=50, choices=US_STATES_CHOICES, null=True, blank=True)
    services = models.ManyToManyField(Service, related_name='client_services', blank=True)
    client_status = models.CharField(max_length=50, choices=CAMP_ACTIVITY, default='active',null=True, blank=True)
    discovery_method = models.CharField(max_length=20 , choices=DISCOVERY_TYPE, blank=True, null=True)

    affiliate = models.ForeignKey(AffiliateProfile, blank=True, null=True, related_name="client_affiliate_profile", on_delete=models.SET_NULL )

    settings_theme = models.CharField(max_length=50,default="dark", choices=THEME_CHOICES)
    maps_theme = models.CharField(max_length=50,default="dark", choices=THEME_CHOICES)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.id:  # Check if the object has an ID (i.e., it's a new object)
            # Get the last ID in the table and increment by 1
            last_agent = ClientProfile.objects.order_by('-id').first()
            if last_agent:
                self.id = last_agent.id + 1
            else:
                self.id = 5000  # Start with ID 1000 if no agents exist yet
        super().save(*args, **kwargs)






class AffiliateInvoice(models.Model):
    id = models.AutoField(primary_key=True)
    affiliate = models.ForeignKey(AffiliateProfile, blank=True, null=True, related_name="invoice_affiliate_profile", on_delete=models.SET_NULL )
    client = models.ForeignKey(ClientProfile, blank=True, null=True, related_name="invoice_client_profile", on_delete=models.SET_NULL )
    revenue =  models.FloatField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)




class Campaign(models.Model): # Client Campaigns


    time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.SET_NULL, null=True, blank=True)
    agents_count = models.PositiveIntegerField(default=0)
    agents_rate = models.PositiveIntegerField(default=0)
    weekly_hours = models.PositiveIntegerField(default=0)
    weekly_leads = models.PositiveIntegerField(default=0)
    datasources = models.ManyToManyField(DataSource, related_name='datasources_campaign', blank=True)

    campaign_type = models.CharField(max_length=50, choices=SERVICE_TYPES, null=True, blank=True)

    lead_points = models.PositiveIntegerField(default=0)

    lookerstudio = models.TextField(null=True , blank=True)
    
    dialer = models.ForeignKey(Dialer, on_delete=models.SET_NULL,null=True, blank=True)

    dialer_type = models.CharField(max_length=50, choices=DIALERS, null=True, blank=True)
    
    dialer_api_key = models.TextField(null=True, blank=True)

    documentation = models.TextField(null=True, blank=True)
    qa_sop = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=50,default="active", choices=CAMP_ACTIVITY, null=True, blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

    def get_accumulated_durations(self, start_date=None, end_date=None):
        """
        Calculate the accumulated durations for all seat logs associated with this campaign
        within a specific date range, accounting for logs that span multiple days.
        """
        seat_logs = SeatAssignmentLog.objects.filter(dialer_credentials__campaign=self)

        # Apply date range filter if provided
        if start_date:
            seat_logs = seat_logs.filter(start_time__gte=start_date)
        if end_date:
            seat_logs = seat_logs.filter(end_time__lte=end_date)

        total_duration = timedelta()

        for log in seat_logs:
            log_start_time = log.start_time
            log_end_time = log.end_time or timezone.now()

            # Adjust log times to fall within the specified date range
            if start_date:
                log_start_time = max(log_start_time, start_date)
            if end_date:
                log_end_time = min(log_end_time, end_date)

            # Split the duration calculation into full days and partial days
            current_time = log_start_time

            while current_time < log_end_time:
                # Calculate the end of the current day
                end_of_day = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
                if end_of_day > log_end_time:
                    end_of_day = log_end_time

                # Calculate the duration for the current day
                duration = end_of_day - current_time
                total_duration += duration

                # Move to the next day
                current_time = end_of_day + timedelta(seconds=1)

        return total_duration.total_seconds()



    def get_accumulated_durations(self, start_date=None, end_date=None):
        """
        Calculate the accumulated durations for all seats associated with this campaign
        within a specific date range.
        """
        # Filter SeatAssignmentLogs based on the campaign ID through the related DialerCredentials
        seat_logs = SeatAssignmentLog.objects.filter(dialer_credentials__campaign=self)

        # Apply timezone-aware start_date and end_date filtering
        if start_date:
            start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
            seat_logs = seat_logs.filter(start_time__gte=start_date)

        if end_date:
            end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
            seat_logs = seat_logs.filter(end_time__lte=end_date)

        # Calculate the duration for each log entry
        total_duration = 0
        for log in seat_logs:
            log_start_time = timezone.localtime(log.start_time)  # Ensure timezone-aware
            log_end_time = timezone.localtime(log.end_time) if log.end_time else timezone.now()

            # Ensure that the duration is calculated only for the overlapping period with the given date range
            effective_start_time = max(log_start_time, start_date) if start_date else log_start_time
            effective_end_time = min(log_end_time, end_date) if end_date else log_end_time

            # Calculate the duration only within the effective date range
            if effective_end_time > effective_start_time:
                total_duration += (effective_end_time - effective_start_time).total_seconds()

        return total_duration


    def get_total_hours_per_account(self, start_date, end_date):
        """Calculate total hours and unique agents for each account within the date range."""
        account_data = {}

        # Fetch all DialerCredentials related to this campaign
        dialer_credentials = DialerCredentials.objects.filter(campaign=self)

        for dialer in dialer_credentials:
            # Calculate total accumulated duration and count unique agents for each dialer in the specified date range
            seat_logs = SeatAssignmentLog.objects.filter(
                dialer_credentials=dialer,
                start_time__lte=end_date,
                end_time__gte=start_date
            )

            total_seconds = 0
            unique_agents = set()

            for log in seat_logs:
                # Calculate overlap between log and date range
                overlap_start = max(start_date, log.start_time)
                overlap_end = min(end_date, log.end_time) if log.end_time else end_date
                
                if overlap_start < overlap_end:
                    total_seconds += (overlap_end - overlap_start).total_seconds()
                    unique_agents.add(log.agent_profile.id)

            # Convert seconds to hours
            total_hours = total_seconds / 3600

            # Format time in HH:MM:SS
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

            account_data[dialer] = {
                'total_hours': total_hours,
                'formatted_time': formatted_time,
                'unique_agents_count': len(unique_agents)
            }

        return account_data
    



class DialerReport(models.Model): 
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    client_profile = models.ForeignKey(ClientProfile, on_delete=models.SET_NULL, blank=True, null=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, blank=True, null=True)

    dialer = models.CharField(max_length=50, choices=DIALERS ,null=True, blank=True)
    api_key = models.TextField(null=True, blank=True)


    active = models.BooleanField(default=True)

    def __str__(self):
        return self.client_profile


class DialerCredentials(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    dialer = models.ForeignKey(Dialer, on_delete=models.SET_NULL, null=True, blank=True)
    agent_profile = models.ForeignKey('Profile',on_delete=models.SET_NULL,related_name="profile_dialercreds", null=True, blank=True)
    account_type = models.CharField(max_length=50, choices=DIALER_ACCOUNT_TYPE, null=True, blank=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.username)
    


class Profile(models.Model): #Profile Standard Information
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)
    picture = models.ImageField(upload_to=random_name_profile_pic, blank=True, null=True)
    full_name = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=50,blank=True,null=True)
    phone_name = models.CharField(max_length=50, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL,blank=True,null=True)
    hiring_date = models.DateField(blank=True, null=True)
    birth_date = models.DateField(blank=True,null=True)
    role = models.ForeignKey(Role, blank=True, null=True, related_name="profile_role", on_delete=models.SET_NULL)

    login_time = models.TimeField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', blank=True, null=True)
    hourly_rate = models.FloatField(default=0,null=True, blank=True)
    monthly_salary = models.FloatField(default=0,null=True, blank=True)
    salary_type = models.CharField(max_length=20 , choices=SALARY_TYPE, blank=True, null=True)
    phone_number = models.CharField(max_length=50,null=True,blank=True)
    residence = models.CharField(max_length=50, choices=COUNTRIES_CHOICES, null=True, blank=True)
    discord = models.CharField(max_length=100, null=True, blank=True)
    payoneer = models.CharField(max_length=100, null=True, blank=True)
    instapay = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(max_length=50,default="payoneer", choices=PAYMENT_CHOICES)

    national_id = models.ImageField(upload_to=random_name_national_id, blank=True, null=True)


    settings_theme = models.CharField(max_length=50,default="dark", choices=THEME_CHOICES)
    maps_theme = models.CharField(max_length=50,default="dark", choices=THEME_CHOICES)



    assigned_credentials = models.ForeignKey(DialerCredentials, on_delete=models.SET_NULL, null=True, blank=True)

    active = models.BooleanField(default=True)

    ## Assign campaign to each profile
    current_campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="current_campaign_users")


    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.id:  # Check if the object has an ID (i.e., it's a new object)
            # Get the last ID in the table and increment by 1
            last_agent = Profile.objects.order_by('-id').first()
            if last_agent:
                self.id = last_agent.id + 1
            else:
                self.id = 1000  # Start with ID 1000 if no agents exist yet
        super().save(*args, **kwargs)


    def get_current_status(self):
        try:
            # Fetch the latest work status based on the last_status_change field
            last_work_status = WorkStatus.objects.filter(user=self.user).latest('last_status_change')
            return last_work_status.current_status
        except WorkStatus.DoesNotExist:
            return "offline"


class DataSourceCredentials(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    datasource = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True)
    account_type = models.CharField(max_length=50, choices=SOURCE_ACCOUNT_TYPE, null=True, blank=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)
    active = models.BooleanField(default=True)


    def __str__(self):
        return str(self.campaign)

class CampaignDispoSetting(models.Model):

    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, related_name="camp_dispo",null=True, blank=True)
    slot1_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot2_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot3_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot4_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot5_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot6_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot7_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot8_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot9_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot10_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot11_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot12_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot13_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot14_dispo = models.CharField(max_length=50, null=True, blank=True)
    slot15_dispo = models.CharField(max_length=50, null=True, blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.campaign)
    
    def count_non_none_slot_names(self):
        count = 0
        for i in range(1, 11):
            if getattr(self, f'slot{i}_dispo') not in [None, '']:
                count += 1
        return count

class ContactList(models.Model): # List Pulled
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)   
    name = models.CharField(max_length=50, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, related_name="list_campaign",null=True, blank=True)
    contacts = models.IntegerField(null=True, blank=True)
    states = models.TextField(null=True, blank=True)  # Self-referential ManyToManyField
    source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, related_name="datasource_list",null=True, blank=True)
    skip_tracing = models.ForeignKey(DataSource, on_delete=models.SET_NULL, related_name="skiptracing_list",null=True, blank=True)
    dialer = models.ForeignKey(Dialer, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=50, choices=LIST_STATUS_CHOICES,null=True, blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ContactListPerformance(models.Model): # Call Dispos
    time = models.TimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    dialer_list = models.ForeignKey(ContactList, on_delete=models.SET_NULL, related_name="performance_list",null=True, blank=True)
    campaign = models.ForeignKey(ContactList, on_delete=models.SET_NULL, related_name="performance_camp",null=True, blank=True)
    dispo = models.ForeignKey(CampaignDispoSetting, on_delete=models.SET_NULL, related_name="performance_dispos",null=True, blank=True)
    dispo_count = models.IntegerField(default=0, null=True, blank=True)

    active = models.BooleanField(default=True)


    def __str__(self):
        return self.dialer_list


class LeadHandlingSettings(models.Model):
    campaign = models.OneToOneField(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    slot1_name = models.CharField(max_length=100, null=True, blank=True)
    slot1_percentage = models.FloatField(default=0)
    
    slot2_name = models.CharField(max_length=100, null=True, blank=True)
    slot2_percentage = models.FloatField(default=0)
    
    slot3_name = models.CharField(max_length=100, null=True, blank=True)
    slot3_percentage = models.FloatField(default=0)
    
    slot4_name = models.CharField(max_length=100, null=True, blank=True)
    slot4_percentage = models.FloatField(default=0)
    
    slot5_name = models.CharField(max_length=100, null=True, blank=True)
    slot5_percentage = models.FloatField(default=0)
    
    slot6_name = models.CharField(max_length=100, null=True, blank=True)
    slot6_percentage = models.FloatField(default=0)
    
    slot7_name = models.CharField(max_length=100, null=True, blank=True)
    slot7_percentage = models.FloatField(default=0)
    
    slot8_name = models.CharField(max_length=100, null=True, blank=True)
    slot8_percentage = models.FloatField(default=0)
    
    slot9_name = models.CharField(max_length=100, null=True, blank=True)
    slot9_percentage = models.FloatField(default=0)
    
    slot10_name = models.CharField(max_length=100, null=True, blank=True)
    slot10_percentage = models.FloatField(default=0)

    activated = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def count_non_none_slot_names(self):
        count = 0
        for i in range(1, 11):
            if getattr(self, f'slot{i}_name') not in [None, '']:
                count += 1
        return count

    def get_active_slots(self):
        slots = []
        for i in range(1, 11):
            name_field = getattr(self, f'slot{i}_name')
            percentage_field = getattr(self, f'slot{i}_percentage')
            if name_field and percentage_field > 0:
                slots.append({
                    'id': f'slot{i}',
                    'name': name_field,
                    'percentage': percentage_field
                })
        return slots


 
    

class Lead(models.Model):
    pushed = models.DateTimeField(default=timezone.now)
    handled = models.DateTimeField(null=True, blank=True)

    lead_id = models.AutoField(primary_key=True)
    agent_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="lead_profile")
    
    lead_type = models.CharField(max_length=50, choices=LEAD_TYPE_CHOICES, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, related_name="lead_campaign", null=True, blank=True)
    contact_list = models.ForeignKey(ContactList, on_delete=models.SET_NULL, related_name="lead_list", null=True, blank=True)
    property_type = models.CharField(max_length=50, choices=PROPERTY_CHOICES, default="house",null=True, blank=True)
    seller_name = models.CharField(max_length=50, null=True, blank=True)
    seller_phone = models.CharField(max_length=50, null=True, blank=True)
    seller_email = models.CharField(max_length=50, null=True, blank=True)
    timeline = models.CharField(max_length=50, choices=TIMELINE_CHOICES, default="two_weeks" ,null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    property_address = models.TextField( null=True, blank=True)
    asking_price = models.CharField(max_length=50, null=True, blank=True)
    market_value = models.CharField(max_length=50, null=True, blank=True)
    general_info = models.TextField( null=True, blank=True)
    property_url = models.TextField(null=True,blank=True)
    callback = models.CharField(max_length=50, null=True, blank=True)
    extra_notes = models.TextField( null=True, blank=True)



    roof_age = models.CharField(max_length=50, null=True, blank=True)
    appointment_time = models.CharField(max_length=50, null=True, blank=True)
    known_issues = models.TextField(null=True, blank=True)



    state = models.CharField(max_length=50, default=0, null=True, blank=True)
    county = models.CharField(max_length=50, default=0, null=True, blank=True)
    latitude = models.FloatField(default=0, null=True, blank=True)
    longitude = models.FloatField(default=0, null=True , blank=True)
    status = models.CharField(max_length=50, choices=LEAD_CHOICES, default='pending', null=True, blank=True)
    quality_notes = models.TextField( null=True, blank=True)
    quality_to_agent_notes = models.TextField(  null=True, blank=True)
    assigned = models.ForeignKey(Profile,on_delete=models.SET_NULL, related_name="assigned_profile", null=True, blank=True)
    assigned_time = models.DateTimeField(null=True, blank=True)
    fireback = models.BooleanField(default=False)
    handling_time = models.DurationField(null=True, blank=True)
    handled_by = models.ForeignKey(User,on_delete=models.SET_NULL, related_name="handled_by_lead_post",null=True,blank=True)
    lead_flow = models.FloatField(default=0,null=True, blank=True)
    lead_flow_json = models.JSONField(default=dict, null=True, blank=True)

    
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.agent_profile) +" #"+str(self.lead_id)
    

class SalesLead(models.Model):
    pushed = models.DateTimeField(default=timezone.now)

    lead_id = models.AutoField(primary_key=True)
    agent_user = models.ForeignKey(User, on_delete=models.SET_NULL,related_name="sales_agent_user", null=True, blank=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,related_name="sales_agent_profile", null=True, blank=True, )
    
    contact = models.CharField(max_length=50, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    contact_email = models.CharField(max_length=50, null=True, blank=True)
    interest_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)

    followup_date = models.DateField(null=True, blank=True)
    followup_time = models.TimeField(null=True, blank=True)


    status = models.CharField(max_length=50, choices=SALES_LEAD_CHOICES, default='follow_up', null=True, blank=True)

    notes = models.TextField(null=True , blank=True)
    
    modified_by = models.ForeignKey(User,on_delete=models.SET_NULL, related_name="sales_modified_by",null=True,blank=True)


    
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.agent_profile) +" #"+str(self.lead_id)
    





class Task(models.Model):
    created = models.DateTimeField(default=timezone.now)
    due =  models.DateField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)


    id = models.AutoField(primary_key=True)
    agent_user = models.ForeignKey(User, on_delete=models.SET_NULL,related_name="task_agent_user", null=True, blank=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,related_name="task_agent_profile", null=True, blank=True, )

    title = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True , blank=True)
    notes = models.TextField(null=True , blank=True)

    priority = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)

    executive_dep = models.BooleanField(default=False)
    ops_dep = models.BooleanField(default=False)
    data_dep = models.BooleanField(default=False)
    workforce_dep = models.BooleanField(default=False)
    quality_dep = models.BooleanField(default=False)
    dev_dep = models.BooleanField(default=False)
    sales_dep = models.BooleanField(default=False)
    hr_dep = models.BooleanField(default=False)

    assigned_department = models.CharField(max_length=50, choices=TASK_DEPARTMENTS, null=True, blank=True)


    notes = models.TextField(null=True,blank=True)



    status = models.CharField(max_length=50, choices=TASK_RESULT_CHOICES, default='in_progress', null=True, blank=True)

    
    modified_by = models.ForeignKey(Profile,on_delete=models.SET_NULL, related_name="task_modified_by",null=True,blank=True)


    
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.title) +" #"+str(self.id)
    







class Leave(models.Model):
    created = models.DateTimeField(default=timezone.now)
    agent_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_profile")
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_profile")
    agent_name = models.CharField(max_length=50, null=True,blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL,null=True, blank=True,  related_name='team_leave', )
    leave_type = models.CharField(max_length=20, choices=LEAVE_CHOICES, default='UPL', blank=True, null=True)
    submission_date = models.DateTimeField(default=timezone.now)
    requested_date = models.DateField( blank=True, null=True)
    reason = models.TextField( blank=True, null=True)
    file = models.FileField(upload_to=random_name_leave_files, null=True, blank=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="handled_by_leave", blank=True,null=True)
    status = models.CharField(max_length=50, choices=REQUESTS_STATUS_CHOICES, blank=True, null=True,default="pending")
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.agent_profile) +" #"+str(self.id)





class Action(models.Model):
    created = models.DateTimeField(default=timezone.now)
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,null=True, related_name="agent_profile_action")
    accuser = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='action_accuser')
    accuser_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,null=True, related_name="accuser_profile_action")
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    submission_date = models.DateField(default=timezone.now)
    incident_date = models.DateField( blank=True, null=True)
    deduction_amount= models.FloatField(default=0,blank=True, null=True)
    file = models.FileField(upload_to=random_name_action_files, null=True, blank=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='handled_by_deduction', blank=True, null=True)
    status = models.CharField(max_length=50, choices=REQUESTS_STATUS_CHOICES, blank=True, null=True,default="pending")
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.agent_profile) +" #"+str(self.id)



class Prepayment(models.Model):
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,null=True, related_name="agent_profile_prepayment")

    submission_date = models.DateField(default=timezone.now)
    timeframe = models.CharField(max_length=50, blank=True, null=True)
    payment_account = models.TextField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="handled_by_prepayment", blank=True, null=True)
    status = models.CharField(max_length=50, choices=REQUESTS_STATUS_CHOICES, blank=True, null=True,default="pending")
    active = models.BooleanField(default=True)



class Feedback(models.Model):
    created = models.DateTimeField(default=timezone.now)
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,null=True, related_name="agent_profile_feedback")
    auditor = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='auditor_feedback')
    auditor_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,null=True, related_name="auditor_feedback")
    campaign = models.ManyToManyField(Campaign, blank=True)
    type = models.CharField(max_length=50, choices=FEEDBACK_CHOICES,null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    feedback_text = models.TextField(null=True, blank=True)
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPE_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=50,default="pending", choices=FEEDBACK_STATUS_CHOICES,null=True, blank=True)
    trainer_text = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.agent_profile) +" #"+str(self.id)


class Absence(models.Model):
    created = models.DateTimeField(default=timezone.now)
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="reporter_user_absence")
    reporter_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name="reporter_profile_absence")
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,null=True, related_name="agent_profile_absence")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    absence_date = models.DateField( blank=True, null=True)
    absence_type = models.CharField(max_length=50, choices=ABSENCE_CHOICES, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)


    def __str__(self):
        return str(self.agent_profile) +" #"+str(self.id)

class WorkStatus(models.Model):
    STATUS_CHOICES = [
        ('ready', 'Ready'),
        ('meeting', 'Meeting'),
        ('break', 'Break'),
        ('offline', 'Offline'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    current_status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    last_status_change = models.DateTimeField(default=timezone.now)
    ready_time = models.DurationField(default=timezone.timedelta())
    meeting_time = models.DurationField(default=timezone.timedelta())
    break_time = models.DurationField(default=timezone.timedelta())
    offline_time = models.DurationField(default=timezone.timedelta())
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    lateness = models.DurationField(null=True, blank=True)
    lateness_status = models.CharField(
        max_length=10,
        choices=[
            ('late', 'Late'),
            ('early', 'Early'),
            ('on_time', 'On Time')
        ],
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user} - {self.date} - {self.current_status}"

    def save(self, *args, **kwargs):
        # Set login time if the object is being created and current_status is active
        

        if self.current_status in ['ready', 'meeting', 'break'] and self.should_set_login_time():
                self.login_time = timezone.now()

                # Calculate lateness details
                profile = Profile.objects.filter(user=self.user).first()
                if profile and profile.login_time:
                    default_login_time = profile.login_time  # This is a datetime.time object
                    actual_login_time = timezone.localtime(self.login_time).time()  # Extract only the time part

                    # Convert both times to seconds since midnight
                    default_login_seconds = (
                        default_login_time.hour * 3600
                        + default_login_time.minute * 60
                        + default_login_time.second
                    )
                    actual_login_seconds = (
                        actual_login_time.hour * 3600
                        + actual_login_time.minute * 60
                        + actual_login_time.second
                    )

                    # Calculate lateness in seconds
                    lateness_seconds = actual_login_seconds - default_login_seconds

                    # Convert seconds back into timedelta
                    lateness = timedelta(seconds=abs(lateness_seconds))

                    # Determine lateness status
                    self.lateness = lateness
                    if lateness_seconds > 0:
                        self.lateness_status = 'late'
                    elif lateness_seconds < 0:
                        self.lateness_status = 'early'
                    else:
                        self.lateness_status = 'on_time'




        super().save(*args, **kwargs)  # Call parent save method

    def update_status(self, new_status):
        now = timezone.now()

        if self.current_status != new_status:
            # Update time spent in the previous status
            duration = now - self.last_status_change
            setattr(
                self,
                f"{self.current_status}_time",
                getattr(self, f"{self.current_status}_time") + duration,
            )

            # Set login time for active statuses
            
            # Set logout time for 'offline' status
            if new_status == 'offline':
                self.logout_time = now

            self.current_status = new_status
            self.last_status_change = now
            self.save()

    def should_set_login_time(self):
        """Check if login time should be set based on time fields."""
        return all(
            getattr(self, f"{status}_time") in [None, timezone.timedelta()]
            for status in ['ready', 'meeting', 'break']
        )

    def get_total_seconds(self, status):
        return getattr(self, f"{status}_time").total_seconds()

    def get_total_times_in_seconds(self):
        return {
            'ready': self.get_total_seconds('ready'),
            'meeting': self.get_total_seconds('meeting'),
            'break': self.get_total_seconds('break'),
            'offline': self.get_total_seconds('offline'),
        }

    def get_login_time_in_timezone(self):
        if self.login_time:
            return timezone.localtime(self.login_time)
        return None

    def get_current_duration(self):
        """Returns the time spent in the current status since the last status change."""
        now = timezone.now()
        duration = now - self.last_status_change
        return duration - timezone.timedelta(microseconds=duration.microseconds)

    @classmethod
    def get_workstatus_with_login_time(cls, agent_profile, month, year):
        return cls.objects.filter(
            user__profile=agent_profile,
            login_time__isnull=False,
            date__month=month,
            date__year=year,
        )

    class Meta:
        indexes = [
            models.Index(fields=['user', 'last_status_change']),
        ]




class SeatAssignmentLog(models.Model):
    agent_profile = models.ForeignKey(Profile,null=True, blank=True,  on_delete=models.SET_NULL)
    dialer_credentials = models.ForeignKey(DialerCredentials, null=True, blank=True, on_delete=models.SET_NULL)
    start_time = models.DateTimeField(default=timezone.now)  # When the seat was assigned
    end_time = models.DateTimeField(null=True, blank=True)  # When the seat was released
    created_time = models.DateTimeField(auto_now_add=True)  # Time when the log entry was created

    def __str__(self):
        return f" [{self.id}]   {self.agent_profile.full_name} on Seat {self.dialer_credentials.id} from {self.start_time} to {self.end_time}"

    def duration(self):
        """Calculate the duration of seat usage."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (timezone.now() - self.start_time).total_seconds()
    

    def duration_formatted(self):
        """Calculate the duration of seat usage."""
        if self.end_time:
            duration_seconds = (self.end_time - self.start_time).total_seconds()
        else:
            duration_seconds = (timezone.now() - self.start_time).total_seconds()
        
        # Convert seconds to HH:MM:SS format
        hours, remainder = divmod(int(duration_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours:02}:{minutes:02}:{seconds:02}"





class ManualHours(models.Model):
 
    created = models.DateTimeField(default=timezone.now)

    agent_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_user_hours")
    agent_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_profile_hours")
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_user_hours")
    admin_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_profile_hours")

    hours = models.IntegerField(null=True, blank=True)

    positive = models.BooleanField(default=True)

    reason = models.CharField(max_length=200,blank=True, null=True)

    active = models.BooleanField(default=True)














class ContractSample(models.Model):
    creator = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100)
    field = models.CharField(max_length=100, choices=CONTRACT_FIELD_TYPES, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.name
    



class Package(models.Model): #Company Provided Services
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)


    count_va = models.CharField(max_length=100, null=True, blank=True)
    rate_va = models.CharField(max_length=100, null=True, blank=True)

    count_lm = models.CharField(max_length=100, null=True, blank=True)
    rate_lm = models.CharField(max_length=100, null=True, blank=True)

    count_acq = models.CharField(max_length=100, null=True, blank=True)
    rate_acq = models.CharField(max_length=100, null=True, blank=True)

    count_dm = models.CharField(max_length=100, null=True, blank=True)
    rate_dm = models.CharField(max_length=100, null=True, blank=True)

    active = models.BooleanField(default=True)
    def __str__(self):
        return self.name


class Contract(models.Model):
    created = models.DateTimeField(default=timezone.now)
    unique_id = models.CharField(max_length=10, unique=True, editable=False, blank=True)

    field = models.CharField(max_length=100, choices=CONTRACT_FIELD_TYPES, null=True, blank=True)

    client_name = models.CharField(max_length=100, null=True, blank=True)
    client_phone = models.CharField(max_length=100, null=True, blank=True)
    client_email = models.CharField(max_length=100, null=True, blank=True)

    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)
    sample = models.ForeignKey(ContractSample, on_delete=models.SET_NULL, null=True, blank=True)
    contract_text = models.TextField(null=True, blank=True)


    count_va = models.CharField(max_length=100, null=True, blank=True)
    rate_va = models.CharField(max_length=100, null=True, blank=True)

    count_lm = models.CharField(max_length=100, null=True, blank=True)
    rate_lm = models.CharField(max_length=100, null=True, blank=True)

    count_acq = models.CharField(max_length=100, null=True, blank=True)
    rate_acq = models.CharField(max_length=100, null=True, blank=True)

    count_dm = models.CharField(max_length=100, null=True, blank=True)
    rate_dm = models.CharField(max_length=100, null=True, blank=True)

    strip_link = models.TextField(null=True, blank=True)

    clicked = models.BooleanField(default=False)


    pref_submitted = models.BooleanField(default=False)


    active = models.BooleanField(default=True)



    def save(self, *args, **kwargs):
        if not self.unique_id:  # Generate only if it doesn't already exist
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_id():
        return secrets.token_urlsafe(8)[:10]
    



    


class ContractVisit(models.Model):

    created = models.DateTimeField(default=timezone.now)
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.CharField(null=True, blank=True, max_length=100)
    location = models.CharField(null=True, blank=True, max_length=100)
    isp = models.CharField(null=True, blank=True, max_length=100)

    active = models.BooleanField(default=True)




class ContractPref(models.Model):

    created = models.DateTimeField(default=timezone.now)
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(null=True, blank=True, max_length=100)
    phone = models.CharField(null=True, blank=True, max_length=100)
    email = models.CharField(null=True, blank=True, max_length=100)
    company_name = models.CharField(null=True, blank=True, max_length=100)

    mention_company = models.BooleanField(default=False)
    remodeled = models.BooleanField(default=False)
    on_market = models.BooleanField(default=False)
    listed_owner = models.BooleanField(default=False)
    closing_fees = models.BooleanField(default=False)
    realtor_fees = models.BooleanField(default=False)
    re_license = models.BooleanField(default=False)
    lots_type = models.CharField(null=True, blank=True,choices=CONTRACT_PREF_PROPERTY_TYPE, max_length=100)
    property_type_re = models.JSONField(default=list, blank=True, null=True)  # JSON field for skills
    res_type = models.JSONField(default=list, blank=True, null=True)  # JSON field for skills
    equity = models.CharField(null=True, blank=True, max_length=100)
    above_market_perc = models.CharField(null=True, blank=True, max_length=100)

    property_type = models.CharField(null=True, blank=True,choices=CONTRACT_PREF_PROPERTY_TYPE, max_length=100)
    owner_type = models.CharField(null=True, blank=True,choices=CONTRACT_PREF_OWNER_TYPE, max_length=100)
    price_range = models.JSONField(default=list, blank=True, null=True)  # JSON field for skills

    coverage =  models.TextField(null=True, blank=True)
    standout =  models.TextField(null=True, blank=True)
    questions =  models.TextField(null=True, blank=True)
    company_info =  models.TextField(null=True, blank=True)
    extra_notes =  models.TextField(null=True, blank=True)

    script_file = models.FileField(upload_to=random_name_contract_files, null=True, blank=True)

    active = models.BooleanField(default=True)



