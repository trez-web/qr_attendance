import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Meeting(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return self.title

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'meeting')

    def __str__(self):
        return f"{self.user.username} - {self.meeting.title}"

class MeetingStaff(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="staff_assignments")
    staff = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': False})
    role = models.CharField(max_length=50, default='Staff')

    class Meta:
        unique_together = ('meeting', 'staff')

    def __str__(self):
        return f"{self.staff.username} ({self.role}) - {self.meeting.title}"

class ScannedAttendance(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    qr_data = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_processed = models.BooleanField(default=False)
    scanned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="scans")

    def __str__(self):
        return f"{self.qr_data} - {self.meeting.title}"