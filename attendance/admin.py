from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.utils import timezone
import csv
from .models import Meeting, Attendance, MeetingStaff, ScannedAttendance

# ── Admin site customization ──────────────────────────────────────
admin.site.site_header = "QR Attendance Admin"
admin.site.site_title = "QR Attendance"
admin.site.index_title = "System Management"

# ── Custom UserAdmin ──────────────────────────────────────────────
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'get_groups')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    actions = ['make_scanner', 'remove_scanner']

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()]) or '—'
    get_groups.short_description = 'Groups'

    def make_scanner(self, request, queryset):
        queryset.update(is_staff=True)
        self.message_user(request, f"{queryset.count()} user(s) promoted to Scanner/Staff.")
    make_scanner.short_description = "✔ Grant scanner (staff) privilege"

    def remove_scanner(self, request, queryset):
        queryset.update(is_staff=False)
        self.message_user(request, f"{queryset.count()} user(s) revoked scanner privilege.")
    remove_scanner.short_description = "✘ Revoke scanner privilege"

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'groups')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'groups'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.is_staff:
            obj.save()
            qr_group, _ = Group.objects.get_or_create(name='QR Scanners')
            obj.groups.add(qr_group)
        super().save_model(request, obj, form, change)

# ── Attendance Inline (show in Meeting admin) ────────────────────
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    readonly_fields = ('user', 'timestamp')
    can_delete = False
    verbose_name_plural = 'Attendance Records'
    fields = ('user', 'timestamp')

# ── MeetingStaff Inline ───────────────────────────────────────────
class MeetingStaffInline(admin.TabularInline):
    model = MeetingStaff
    extra = 1
    verbose_name_plural = 'Staff Assignments'
    fields = ('staff', 'role')
    raw_id_fields = ['staff']

# ── Meeting Admin with CSV export ─────────────────────────────────
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'attendance_count', 'qr_token')
    list_filter = ('date',)
    search_fields = ('title', 'location')
    readonly_fields = ('qr_token',)
    inlines = [AttendanceInline, MeetingStaffInline]
    actions = ['export_attendance_csv']

    def attendance_count(self, obj):
        return Attendance.objects.filter(meeting=obj).count()
    attendance_count.short_description = 'Attendees'

    def export_attendance_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Meeting', 'User ID', 'Username', 'Email', 'Timestamp'])
        for meeting in queryset:
            for att in Attendance.objects.filter(meeting=meeting).select_related('user'):
                writer.writerow([
                    meeting.title,
                    att.user.id,
                    att.user.username,
                    att.user.email,
                    att.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
        return response
    export_attendance_csv.short_description = "Export attendance as CSV"

# ── Attendance Admin ──────────────────────────────────────────────
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'meeting', 'timestamp')
    list_filter = ('meeting', 'timestamp')
    search_fields = ('user__username', 'meeting__title')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

# ── MeetingStaff Admin ────────────────────────────────────────────
class MeetingStaffAdmin(admin.ModelAdmin):
    list_display = ('staff', 'meeting', 'role')
    list_filter = ('meeting', 'role')
    search_fields = ('staff__username', 'meeting__title')

# ── ScannedAttendance Admin ───────────────────────────────────────
class ScannedAttendanceAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'qr_data', 'scanned_by', 'timestamp', 'is_processed')
    list_filter = ('meeting', 'is_processed', 'timestamp')
    search_fields = ('qr_data', 'meeting__title')
    readonly_fields = ('timestamp',)

# ── Register models ───────────────────────────────────────────────
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(MeetingStaff, MeetingStaffAdmin)
admin.site.register(ScannedAttendance, ScannedAttendanceAdmin)
