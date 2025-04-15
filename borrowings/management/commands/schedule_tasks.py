from django_q.models import Schedule
from datetime import datetime, time
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Schedule overdue notification task"

    def handle(self, *args, **kwargs):
        run_time = make_aware(datetime.combine(datetime.today(), time(9, 0)))

        Schedule.objects.update_or_create(
            name="Send overdue borrowings",
            defaults={
                "func": "notifications.tasks.check_overdue_borrowings",
                "schedule_type": Schedule.DAILY,
                "next_run": run_time,
                "repeats": -1,
            },
        )

        self.stdout.write("Scheduled overdue task.")
