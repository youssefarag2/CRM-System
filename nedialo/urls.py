from django.contrib import admin
from django.urls import path
from core.views import *
from admin.views import *
from operations.views import *
from sales.views import *
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [


    path('admin', applications_table),
    path('maintenance/', maintenance, name='maintenance'),
    path('heartbeat/', heartbeat_view, name='heartbeat'),
    path('logout_all/', logout_all, name='logout_all'),  # Add this URL

    #path('applications', applications_table),
    path('application-form/<int:app_id>', application_report),
    path('application-success', application_success),
    path('check-duplicate-application/', check_duplicate_application),
    path('application-stages-<int:year>', application_stages),
    path('crm-admin/', admin.site.urls),
    path('', home),
    path('affiliate-dashboard/<int:month>-<int:year>',affiliate_dashboard),
    path('login', loginview),
    path('logout/',logoutview),
    path('settings',account_settings),
    path('payment_info/', payment_info, name='payment_info'),
    path('update-theme/', update_theme, name='update_theme'),
    path('maps-theme/', maps_theme, name='maps_theme'),
    path('autocomplete/', address_autocomplete, name='address_autocomplete'),
    path('upload-profile/', upload_profile, name='upload_profile'),
    path('upload-id/<int:userid>/', upload_id, name='upload_id'),

    #get agents for the filter feature
    path('agents/', fetch_agents, name='fetch_agents'),


    path('campaign-documentation/<int:id>',camp_doc),
    path('campaign-sop/<int:id>',camp_sop),

    path('admin-roles', roles_table),
    path('role-modify/<int:role_id>', role_modify),


    path('admin-campaigns', campaigns_table),
    path('campaign-create', campaign_create),
    path('campaign-modify/<int:camp_id>', campaign_modify),
    path('campaign-delete/<int:camp_id>/', DeleteCampaignView.as_view()),

    path('admin-contactlists', contactlists_table),
    path('contactlist-create', contactlist_create),
    #path('contactlist-modify/<int:contactlist_id>', contactlist_modify),
    path('contactlist-delete/<int:contactlist_id>/', DeleteContactListView.as_view()),



    path('dialercredentials/<int:campaign_id>', dialer_creds_table),
    path('dialercredentials-create/<int:campaign_id>', dialer_cred_create),
    path('dialercredentials-modify/<int:cred_id>', dialer_cred_modify),

    path('dialercredentials-delete/<int:cred_id>/', DeleteDialerCredView.as_view()),


    path('sourcecredentials/<int:campaign_id>', source_creds_table),
    path('sourcecredentials-create/<int:campaign_id>', source_cred_create),
    path('sourcecredentials-modify/<int:cred_id>', source_cred_modify),
    path('sourcecredentials-delete/<int:cred_id>/', DeleteSourceCredView.as_view()),

    path('admin-agents', agents_table),
    path('agent-create',agent_create),
    path('agent-modify/<str:username>',agent_modify),
    path('agent-delete/<str:username>/', DeleteUserView.as_view()),


    path('admin-clients', clients_table),
    path('client-create',client_create),
    path('client-modify/<str:username>',client_modify),
    path('client-delete/<str:username>/', DeleteClientView.as_view()),

    path('client-dashboard/<int:month>-<int:year>',client_dashboard),
    path('client-lead-report/<int:lead_id>', client_lead_report),
    path('client-lookerstudio', client_lookerstudio),


    path('admin-affiliates', affiliates_table),
    path('affiliate-data/<str:username>-<int:month>-<int:year>', affiliate_data),
    path('affiliate-create', affiliate_create),
    path('affiliate-invoice-create/<str:username>', affiliate_invoice_create),

    path('affiliate-modify/<str:username>', affiliate_modify),
    path('affiliate-delete/<str:username>/', DeleteAffiliateView.as_view()),



    path('admin-services', services_table),
    path('service-create',service_create),
    path('service-delete/<int:service_id>/', DeleteServiceView.as_view()),

    path('admin-dialers', dialers_table),
    path('dialer-create',dialer_create),
    path('dialer-delete/<int:dialer_id>/', DeleteDialerView.as_view()),


    path('admin-datasources', dataSources_table),
    path('datasource-create',dataSource_create),
    path('datasource-delete/<int:source_id>/', DeleteDataSourceView.as_view()),

    path('admin-serversettings', server_settings),

    path('admin-packages', packages_table),
    path('package-create', package_create),
    path('package-modify/<int:id>', package_modify),
    path('package-delete/<int:id>/', DeletePackageView.as_view()),


    path('admin-contracts', contracts_table),
    path('contract-create', contract_create),
    path('contract-create-actual', contract_create_actual),
    path('contract-delete/<int:id>/', DeleteContractView.as_view()),

    path('contract-view/<str:id>', contract_view),


    path('admin-contract-samples', contract_samples_table),
    path('sample-create', sample_create),
    path('sample-modify/<int:id>', sample_modify),
    path('sample-delete/<int:id>/', DeleteSampleView.as_view()),

    path('contract-pref/<str:id>',contract_pref),

    path('contract-pref-success/<str:id>',contract_pref_success),

    path('client-preferences/<str:id>',contract_pref_view),




    path('re-lead-submission',lead_submission_re),
    path('roofing-lead-submission',lead_submission_roofing),
    path('apply', application_form),
    path('application-record/',handle_audio_upload, name='application_record'),



    path('my-leads/<int:month>-<int:year>',my_leads),
    path('lead-report/<int:lead_id>', lead_report),
    path('quality-feedback/<int:month>-<int:year>', leads_quality),
    path('lead-scoring/<int:month>-<int:year>',lead_scoring),
    path('leads-leaderboard/<int:month>-<int:year>',leads_leaderboard),

    path('quality-pending',quality_pending),
    path('lead-reports/<int:month>-<int:year>',quality_lead_reports),
    path('agent-leads/<int:agent_id>-<int:month>-<int:year>',agent_lead_reports),
    path('fireback-lead/<int:lead_id>/', fire_lead, name='fire-lead'),

    path('lead-handling/<int:lead_id>', lead_handling, name='lead_handling'),
    path('get-lead-status/<int:lead_id>/',get_lead_status, name='get_lead_status'),
    path('unassign-lead/<int:lead_id>/',unassign_lead, name='get_lead_status'),
    path('feedbacks', feedbacks_table),
    path('feedbacks-agent/<int:agent_id>', feedbacks_agent),

    path('feedback-single', feedback_single),
    path('feedback-monthly', feedback_monthly),
    path('feedback-report/<int:id>',feedback_report),

    path('quality-agents/<int:month>-<int:year>',quality_agents),


    path('work-status-data/', work_status_data, name='work_status_data'),

    path('update-status/', update_status, name='update_status'),




    path('leave-requests',leave_request_list),
    path('new-leave',leave_request, name="file_upload"),

    path('delete-leave/<int:leave_id>/', delete_leave, name='delete-leave'),

    path('leave-handling',leave_handling_list),

    path('leave-report/<int:leave_id>',leave_report),


    path('prepayment-requests',prepayment_request_list),
    path('new-prepayment',prepayment_request, name="file_upload"),

    path('delete-prepayment/<int:prepayment_id>/', delete_prepayment, name='delete-prepayment'),

    path('prepayments-handling',prepayment_handling_list),

    path('prepayment-report/<int:prepayment_id>',prepayment_report),





    path('action-requests',action_request_list),
    path('new-action',action_request, name="file_upload"),

    path('delete-action/<int:action_id>/', delete_action, name='delete-action'),

    path('action-handling',action_handling_list),

    path('action-report/<int:action_id>',action_report),

    path('dialer-report/<int:camp_id>',dialer_report),




    path('seats', seats),
    path('seat-breakdown/<int:seat_id>-<int:month>-<int:year>', seat_breakdown),
    path('agent-seat-breakdown/<int:agent_id>-<int:month>-<int:year>', agent_seat_breakdown),

    path('update-seat-agent/<int:seat_id>/', update_seat_agent_profile, name='update_seat_agent_profile'),
    path('unseat/<int:agent_id>/', unseat_agent, name='unseat_agent'),
    path('seatlog-delete/<int:log_id>/', DeleteSeatLogView.as_view()),


    path('agents-list-company', agents_list_company),
    path('agents-list-team/<int:team_id>', agents_list_team),
    path('agent-login-update/', update_agent_login_time, name='update_agent_login_time'),

    path('agent-seat-update/', update_seat_admin, name='update_seat_admin'),


    path('agents-moderation-<int:month>-<int:year>', agents_moderation),
    path('update-agent-campaign/<int:agent_id>/', update_agent_campaign, name='update_agent_campaign'),


    path('update_status_admin/', update_status_admin, name='update_status_admin'),

    path('camphours-daily/<int:camp_id>-<int:month>-<int:year>', camp_hours_daily),

    path('camphours-monthly/<int:camp_id>-<int:month>-<int:year>', camp_hours_monthly),
    path('camphours-yearly/<int:camp_id>-<int:year>', camp_hours_yearly),

    path('all-campaigns-performance/<int:month>-<int:year>', all_campaigns_performance),

    path('campleads-daily/<int:camp_id>-<int:month>-<int:year>', camp_leads_daily),

    path('campleads-monthly/<int:camp_id>-<int:month>-<int:year>', camp_leads_monthly),
    path('campleads-yearly/<int:camp_id>-<int:year>', camp_leads_yearly),


    path('working-hours-company/<int:month>-<int:year>', working_hours_company),
    path('working-hours-team/<int:team_id>-<int:month>-<int:year>', working_hours_team),
    path('agent-hours/<int:agent_id>-<int:month>-<int:year>', agent_hours),

    path('adjusting-hours', adjusting_hours),
    path('adjusting-hours-form', adjusting_hours_form),

    path('salaries-table-company/<int:month>-<int:year>', salary_company),
    path('salaries-table-team/<int:team_id>-<int:month>-<int:year>', salary_team),
    path('invoice/<int:agent_id>-<int:month>-<int:year>', invoice),


    path('attendance-monitor-company/<int:month>-<int:year>',attendance_company),
    path('attendance-monitor-team/<int:team_id>-<int:month>-<int:year>',attendance_team),
    path('attendance-monitor-agent/<int:agent_id>-<int:month>-<int:year>',attendance_agent),


    path('lateness-monitor-company/<int:month>-<int:year>', lateness_company),
    path('lateness-monitor-team/<int:team_id>-<int:month>-<int:year>',lateness_team),
    path('lateness-monitor-agent/<int:agent_id>-<int:month>-<int:year>',lateness_agent),

    

    path('report-absence',report_absence),


    path('sales-dashboard-<int:year>',sales_dashboard),
    path('sales-clients-list-<int:year>',sales_clients_list),
    path('sales-lookerstudio',sales_lookerstudio),
    path('sales-calendar-<int:month>-<int:year>', sales_calendar),
    path('new-sales-lead',sales_lead_create),
    path('sales-lead-info/<int:lead_id>',sales_lead_info),



    path('company-tasks-<int:year>',company_tasks),
    path('new-task',task_creation),
    path('task-info/<int:task_id>',task_info),

 
    path('sales-lead-submit/', SalesLeadSubmitView.as_view(), name='sales_lead_submit'),

    path('sales-lead-update/', update_sales_lead, name='sales_lead_update'),

    path('sales-lead-update-status/', UpdateLeadStatusView.as_view(), name='update-lead-status'),


    path('sales-lead-data/', sales_leads_data, name='sales_leads_data'),


]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




