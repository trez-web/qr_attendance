from django.urls import path
from . import views

urlpatterns = [
    path('login/',    views.user_login,    name='user_login'),
    path('logout/',   views.user_logout,   name='user_logout'),
    path('change-password/', views.change_password, name='change_password'),

    # Student
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('generate-qr/<int:meeting_id>/', views.generate_qr, name='generate_qr'),

    # Staff scanner
    path('scan/', views.scan_qr, name='scan'),

    # Admin panel
    path('admin-panel/',                          views.admin_dashboard,    name='admin_dashboard'),
    path('admin-panel/meetings/',                 views.admin_meetings,     name='admin_meetings'),
    path('admin-panel/meetings/add/',             views.admin_add_meeting,  name='admin_add_meeting'),
    path('admin-panel/meetings/<int:pk>/delete/', views.admin_delete_meeting, name='admin_delete_meeting'),
    path('admin-panel/assign-staff/',             views.admin_assign_staff, name='admin_assign_staff'),
    path('admin-panel/unassign/<int:pk>/',        views.admin_unassign_staff, name='admin_unassign_staff'),
    path('admin-panel/users/',                    views.admin_users,        name='admin_users'),
    path('admin-panel/staff/',                    views.admin_staff,        name='admin_staff'),
    path('admin-panel/attendance/',               views.admin_attendance,   name='admin_attendance'),
    path('admin-panel/attendance/<int:meeting_id>/', views.admin_attendance, name='admin_attendance_meeting'),
    path('admin-panel/attendance/<int:meeting_id>/csv/', views.admin_download_csv, name='admin_download_csv'),

    # Legacy
    path('meetings/',              views.meeting_list,        name='meeting_list'),
    path('add-meeting/',           views.add_meeting,         name='add_meeting'),
    path('assign-staff/',          views.assign_staff,        name='assign_staff'),
    path('custom-add-staff/',      views.custom_add_staff,    name='custom_add_staff'),
    path('download/<int:meeting_id>/', views.download_attendance, name='download_attendance'),
]
