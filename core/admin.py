from django.contrib import admin
from .models import *
from django.utils.html import format_html


# Register your models here.

@admin.register(ServerSetting)
class ServerSettingAdmin(admin.ModelAdmin):
    list_display = ('company_name',)
    readonly_fields = ('id',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name','active')
    readonly_fields = ('id',)

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name','id','user','password','role','active')
    filter_horizontal = ('services',)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name','id','user','password','role','hourly_rate','phone_number','active')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name','phone','submission_date','position','active')
    readonly_fields = ('id','app_uuid')     


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name','team_type','active')
    readonly_fields = ('id',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type','active')


@admin.register(Dialer)
class DialerAdmin(admin.ModelAdmin):
    list_display = ('name', 'dialer_type','active')

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type','active')



@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'client','active')
    filter_horizontal = ('datasources',)


@admin.register(DialerCredentials)
class DialerCredentialsAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'agent_profile','account_type',"username",'password','active')
    

@admin.register(DataSourceCredentials)
class DataSourceCredentialsAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'datasource','account_type',"username",'password','active')

@admin.register(LeadHandlingSettings)
class LeadHandlingSettingsAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'activated', 'active')

@admin.register(CampaignDispoSetting)
class CampaignDispoSettingAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'active')

@admin.register(ContactList)
class ContactListAdmin(admin.ModelAdmin):
    list_display = ('name','campaign', 'active')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('agent_user', 'lead_id','campaign','pushed','seller_name','status','handled_by')

 


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('agent_profile', 'leave_type', 'active')


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'action_type', 'active')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('agent_profile', 'auditor_profile','type', 'feedback_type', 'status')



@admin.register(ManualHours)
class ManualHoursAdmin(admin.ModelAdmin):
    list_display = ('agent_profile','created', 'positive','hours', 'active')




@admin.register(WorkStatus)
class WorkStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'formatted_current_status', 'login_time', 'logout_time')

    def formatted_current_status(self, obj):
        if obj.current_status == 'ready':
            color = 'green'
        elif obj.current_status == 'meeting':
            color = 'blue'
        elif obj.current_status == 'break':
            color = 'orange'
        elif obj.current_status == 'offline':
            color = 'red'
        else:
            color = 'black'

        return format_html(
            '<span style="font-weight: bold; color: {};">{}</span>',
            color,
            obj.current_status.upper()  # Optional: Convert to uppercase
        )

    formatted_current_status.short_description = 'Current Status'



admin.site.register(Absence)

admin.site.register(SeatAssignmentLog)

admin.site.register(Prepayment)


admin.site.register(SalesLead)

admin.site.register(AffiliateInvoice)
admin.site.register(AffiliateProfile)
admin.site.register(Task)

admin.site.register(ContractSample)

admin.site.register(Contract)
admin.site.register(Package)

admin.site.register(ContractVisit)
admin.site.register(ContractPref)
