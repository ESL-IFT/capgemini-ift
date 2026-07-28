from django.core.management.base import BaseCommand
from students.models import School
import requests


class Command(BaseCommand):
    help = 'Check all schools against TCE API and update is_tata_classedge status'

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.TCE_API_TOKEN:
            self.stderr.write('TCE_API_TOKEN not configured')
            return

        schools = School.objects.all()
        updated = 0
        for school in schools:
            try:
                resp = requests.post(
                    settings.TCE_API_URL,
                    json={
                        'school_name': school.name,
                        'address': school.address or '',
                        'city': school.city or '',
                        'state': school.state or '',
                        'pin_code': school.pin_code or '',
                    },
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {settings.TCE_API_TOKEN}',
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    is_tce = resp.json().get('is_tce_school', False)
                    if school.is_tata_classedge != is_tce:
                        school.is_tata_classedge = is_tce
                        school.save(update_fields=['is_tata_classedge'])
                        updated += 1
                        self.stdout.write(f'  Updated: {school.name} -> TCE={is_tce}')
                    else:
                        self.stdout.write(f'  OK: {school.name} (TCE={is_tce})')
                else:
                    self.stderr.write(f'  API {resp.status_code}: {school.name}')
            except Exception as e:
                self.stderr.write(f'  Error: {school.name} - {e}')

        self.stdout.write(self.style.SUCCESS(f'Done. {updated} schools updated out of {schools.count()}'))
