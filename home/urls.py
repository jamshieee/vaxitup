from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.conf.urls import handler404
from django.shortcuts import render

urlpatterns = [
    path('', views.index, name='index'),
    path('userlog/', views.userlog, name='userlog'),
    path('userreg/', views.userreg, name='userreg'),
    path('homeuser/', views.homeuser, name='homeuser'),
    path('register/', views.register, name='register'),
    path('DBLogin/', views.DBLogin, name='DBLogin'),
    path('USERProfile/', views.USERProfile, name='USERProfile'),
    path('DBAdmin/', views.DBAdmin, name='DBAdmin'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('center/', views.center, name='center'),
    path('center_home/', views.center_home, name='center_home'),
    path('add_vaccines/', views.add_vaccines, name='add_vaccines'),
    path('edit_vaccine/<int:id>/', views.edit_vaccine, name='edit_vaccine'),
    path('delete_vaccine/<int:id>/', views.delete_vaccine, name='delete_vaccine'),
    path('center_vaccines/', views.display_vaccines, name='display_vaccines'),
    path('center_registration/', views.center_registration, name='center_registration'),
    path('approve_center/<int:center_id>/', views.approve_center, name='approve_center'),
    path('manage_centers/', views.manage_centers, name='manage_centers'),
    path('pending_verification/', views.pending_verification, name='pending_verification'),
    path('approved_centers/', views.approved_centers, name='approved_centers'),
    path('center_login/', views.center_login, name='center_login'),
    path('check-approval-status/', views.check_approval_status, name='check_approval_status'),
    path('unapprove_center/<int:center_id>/', views.unapprove_center, name='unapprove_center'),
    path("update_center_holidays/", views.update_center_holidays, name="update_center_holidays"),
    path("view_holidays/", views.view_holidays, name="view_holidays"),
    path('confirm_booking/', views.confirm_booking, name='confirm_booking'),
    path("center_bookings/", views.center_bookings, name="center_bookings"),
    path("update_booking_status/<int:booking_id>/<str:status>/", views.update_booking_status, name="update_booking_status"),
    # path("generate_vaccine_certificate/", views.generate_vaccine_certificate, name="generate_vaccine_certificate"),
    path("user_notifications_json/json", views.user_notifications_json, name="user_notifications_json"),
    path("user_notifications/", views.user_notifications, name="user_notifications"),
    path('search_vaccines/', views.search_vaccines, name="search_vaccines"),
    path('select_center/', views.select_center, name="select_center"),
    path('check_vaccine_availability/', views.check_vaccine_availability, name="check_vaccine_availability"),
    path('center_welcome/', views.center_welcome, name="center_welcome"),
    path('center_profile', views.center_profile, name="center_profile"),
    path('edit_center_profile/<int:center_id>/', views.edit_center_profile, name="edit_center_profile"),
    path('cancel_booking/<int:booking_id>/', views.cancel_booking, name="cancel_booking"),
    path("update_profile/", views.update_profile, name="update_profile"),
    path('feedback/', views.feedback_view, name="feedback_view"),
    path("submit-feedback/", views.submit_feedback, name="submit_feedback"),
    path('admin_feedback_view/', views.admin_feedback_view, name="admin_feedback_view"),
    path('admin_users_view/', views.admin_users_view, name='admin_users_view'),
    path('reject_user/<int:user_id>/', views.reject_user, name='reject_user'),
    path('vaccinated_users/', views.vaccinated_users_view, name='vaccinated_users_view'),
    path('completed-users/', views.completed_users_view, name='completed_users_view'),
    path("user_logout/", views.user_logout, name="user_logout"),
    path("delete-center/<int:center_id>/", views.delete_center, name="delete_center"),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("send-reset-otp/", views.send_reset_otp, name="send_reset_otp"),
    path("verify-reset-otp/", views.verify_reset_otp, name="verify_reset_otp"),
    path("center_logout/", views.center_logout, name="center_logout"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("cancelled_users/", views.cancelled_users, name="cancelled_users"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404_view