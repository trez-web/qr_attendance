from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import timezone
from functools import wraps
import csv, json

from .models import Meeting, Attendance, MeetingStaff
from .forms import MeetingForm
from .utils import generate_meeting_qr


# ── Decorators ────────────────────────────────────────────────────
def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('user_login')
        if not request.user.is_superuser:
            return redirect('user_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def _is_student(user):
    return user.is_authenticated and not user.is_staff and not user.is_superuser


# ── Login / Logout ────────────────────────────────────────────────
def user_login(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    if request.method == "POST":
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            return _redirect_by_role(user)
        return render(request, 'attendance/login.html', {'error': 'Invalid credentials'})
    return render(request, 'attendance/login.html')

def _redirect_by_role(user):
    if user.is_superuser:
        return redirect('admin_dashboard')
    if user.is_staff:
        return redirect('scan')
    return redirect('student_dashboard')

def user_logout(request):
    logout(request)
    return redirect('user_login')


@login_required
def change_password(request):
    error = success = None
    if request.method == "POST":
        current  = request.POST.get('current_password', '')
        new_pw   = request.POST.get('new_password', '')
        confirm  = request.POST.get('confirm_password', '')
        if not request.user.check_password(current):
            error = "Current password is incorrect."
        elif len(new_pw) < 6:
            error = "New password must be at least 6 characters."
        elif new_pw != confirm:
            error = "New passwords do not match."
        else:
            request.user.set_password(new_pw)
            request.user.save()
            # Re-authenticate so session stays valid
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            success = "Password changed successfully."
    return render(request, 'attendance/change_password.html', {'error': error, 'success': success})


# ══════════════════════════════════════════════════════════════════
# ADMIN PANEL (superuser only)
# ══════════════════════════════════════════════════════════════════

@superuser_required
def admin_dashboard(request):
    ctx = {
        'stats': [
            ('Meetings',   Meeting.objects.count(),                                         'text-blue-400',   '📅', '#3b82f6'),
            ('Users',      User.objects.filter(is_staff=False, is_superuser=False).count(), 'text-green-400',  '👤', '#10b981'),
            ('Staff',      User.objects.filter(is_staff=True,  is_superuser=False).count(), 'text-yellow-400', '🔍', '#f59e0b'),
            ('Attendance', Attendance.objects.count(),                                       'text-purple-400', '✅', '#8b5cf6'),
        ],
        'recent_attendance': Attendance.objects.select_related('user','meeting').order_by('-timestamp')[:10],
    }
    return render(request, 'attendance/admin/dashboard.html', ctx)


# ── Meetings ──────────────────────────────────────────────────────
@superuser_required
def admin_meetings(request):
    meetings = Meeting.objects.all().order_by('-date')
    for m in meetings:
        m.attendee_count = Attendance.objects.filter(meeting=m).count()
        m.qr_url = generate_meeting_qr(m)
        m.assigned_staff = MeetingStaff.objects.filter(meeting=m).select_related('staff')
    all_staff = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    return render(request, 'attendance/admin/meetings.html', {'meetings': meetings, 'all_staff': all_staff})

@superuser_required
def admin_add_meeting(request):
    error = None
    if request.method == "POST":
        title    = request.POST.get('title','').strip()
        location = request.POST.get('location','').strip()
        date     = request.POST.get('date','').strip()
        if title and date:
            Meeting.objects.create(title=title, location=location, date=date)
            return redirect('admin_meetings')
        error = "Title and date are required."
    return render(request, 'attendance/admin/add_meeting.html', {'error': error})

@superuser_required
def admin_delete_meeting(request, pk):
    get_object_or_404(Meeting, pk=pk).delete()
    return redirect('admin_meetings')


# ── Staff assignment ──────────────────────────────────────────────
@superuser_required
def admin_assign_staff(request):
    if request.method == "POST":
        meeting_id = request.POST.get('meeting_id')
        staff_id   = request.POST.get('staff_id')
        if meeting_id and staff_id:
            meeting = get_object_or_404(Meeting, id=meeting_id)
            staff   = get_object_or_404(User, id=staff_id, is_staff=True, is_superuser=False)
            MeetingStaff.objects.get_or_create(meeting=meeting, staff=staff)
        return redirect('admin_meetings')
    return redirect('admin_meetings')

@superuser_required
def admin_unassign_staff(request, pk):
    get_object_or_404(MeetingStaff, pk=pk).delete()
    return redirect('admin_meetings')


# ── Users (students) ─────────────────────────────────────────────
@superuser_required
def admin_users(request):
    success = error = None
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'create':
            username = request.POST.get('username','').strip()
            password = request.POST.get('password','').strip()
            email    = request.POST.get('email','').strip()
            if not username or not password:
                error = "Username and password required."
            elif User.objects.filter(username=username).exists():
                error = f"'{username}' already exists."
            else:
                User.objects.create_user(username=username, password=password,
                                         email=email, is_staff=False)
                success = f"Student '{username}' created."
        elif action == 'delete':
            uid = request.POST.get('user_id')
            User.objects.filter(id=uid, is_staff=False, is_superuser=False).delete()
            success = "User deleted."

    students = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    return render(request, 'attendance/admin/users.html',
                  {'students': students, 'success': success, 'error': error})


# ── Staff ─────────────────────────────────────────────────────────
@superuser_required
def admin_staff(request):
    success = error = None
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'create':
            username = request.POST.get('username','').strip()
            password = request.POST.get('password','').strip()
            email    = request.POST.get('email','').strip()
            if not username or not password:
                error = "Username and password required."
            elif User.objects.filter(username=username).exists():
                error = f"'{username}' already exists."
            else:
                User.objects.create_user(username=username, password=password,
                                         email=email, is_staff=True)
                success = f"Staff '{username}' created."
        elif action == 'delete':
            uid = request.POST.get('staff_id')
            User.objects.filter(id=uid, is_staff=True, is_superuser=False).delete()
            success = "Staff deleted."

    staff_list = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    return render(request, 'attendance/admin/staff.html',
                  {'staff_list': staff_list, 'success': success, 'error': error})


# ── Attendance ────────────────────────────────────────────────────
@superuser_required
def admin_attendance(request, meeting_id=None):
    meetings = Meeting.objects.all().order_by('-date')
    selected = None
    records  = []
    if meeting_id:
        selected = get_object_or_404(Meeting, id=meeting_id)
        records  = Attendance.objects.filter(meeting=selected).select_related('user').order_by('-timestamp')
    return render(request, 'attendance/admin/attendance.html',
                  {'meetings': meetings, 'selected': selected, 'records': records})

@superuser_required
def admin_download_csv(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    records = Attendance.objects.filter(meeting=meeting).select_related('user')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{meeting.title}_{timezone.now().strftime("%Y%m%d")}.csv"'
    w = csv.writer(response)
    w.writerow(['Username', 'Email', 'Meeting', 'Date', 'Timestamp'])
    for a in records:
        w.writerow([a.user.username, a.user.email, meeting.title,
                    str(meeting.date), a.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    return response


# ══════════════════════════════════════════════════════════════════
# STAFF: scan only assigned meetings
# ══════════════════════════════════════════════════════════════════

@login_required
def scan_qr(request):
    if _is_student(request.user):
        return redirect('student_dashboard')
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    # Only meetings assigned to this staff member
    assigned = MeetingStaff.objects.filter(staff=request.user).select_related('meeting')
    meetings  = [a.meeting for a in assigned]
    students  = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    last_scanned = error = success = None

    if request.method == "POST":
        meeting_id = request.POST.get('meeting_id')
        student_id = request.POST.get('student_id')
        qr_data    = request.POST.get('qr_data')

        if not meeting_id:
            error = "No meeting detected from QR."
        elif not student_id:
            error = "Student not identified. Try again."
        elif not qr_data:
            error = "QR data missing."
        else:
            # Verify this staff is assigned to this meeting
            meeting = get_object_or_404(Meeting, id=meeting_id)
            if not MeetingStaff.objects.filter(staff=request.user, meeting=meeting).exists():
                error = "You are not assigned to scan this meeting."
            else:
                try:
                    payload = json.loads(qr_data)
                    if str(meeting.id) != payload['meeting_id'] or \
                       str(meeting.qr_token) != payload['token']:
                        error = "QR does not match this meeting."
                    else:
                        student = get_object_or_404(User, id=student_id)
                        _, created = Attendance.objects.get_or_create(user=student, meeting=meeting)
                        last_scanned = student.username
                        success = f"✔ {student.username} marked present" if created \
                                  else f"{student.username} already marked present."
                except (json.JSONDecodeError, KeyError):
                    error = "Invalid QR code."
                except Exception:
                    error = "Unexpected error."

    meetings_json = json.dumps([{'id': m.id, 'title': m.title, 'token': str(m.qr_token)} for m in meetings])
    students_json = json.dumps([{'id': s.id, 'username': s.username} for s in students])

    return render(request, 'attendance/scan.html', {
        'meetings': meetings, 'students': students,
        'meetings_json': meetings_json, 'students_json': students_json,
        'last_scanned': last_scanned, 'success': success, 'error': error,
        'no_meetings': len(meetings) == 0,
    })


# ══════════════════════════════════════════════════════════════════
# STUDENT
# ══════════════════════════════════════════════════════════════════

@login_required
def student_dashboard(request):
    if not _is_student(request.user):
        return redirect('scan') if request.user.is_staff else redirect('admin_dashboard')
    meetings = Meeting.objects.filter(date__gte=timezone.now()).order_by('date')
    for m in meetings:
        m.qr_url  = generate_meeting_qr(m)
        m.attended = Attendance.objects.filter(user=request.user, meeting=m).exists()
    return render(request, 'attendance/student_dashboard.html', {'meetings': meetings})

@login_required
def generate_qr(request, meeting_id):
    return redirect('student_dashboard')

# Legacy redirects
def meeting_list(request):
    return redirect('admin_meetings')
def add_meeting(request):
    return redirect('admin_add_meeting')
def assign_staff(request):
    return redirect('admin_meetings')
def custom_add_staff(request):
    return redirect('admin_staff')
def download_attendance(request, meeting_id):
    return redirect('admin_download_csv', meeting_id=meeting_id)
