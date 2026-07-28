from django.core.management.base import BaseCommand
from students.models import LearningVideo

class Command(BaseCommand):
    help = 'Load IFT Season 6 learning videos'

    def handle(self, *args, **options):
        LearningVideo.objects.all().update(is_active=False)
        self.stdout.write("Deactivated old videos")

        videos = [
            {'title': 'Session 1: Introduction to Entrepreneurship', 'youtube_url': 'https://youtu.be/OhrPg_LKUXo', 'youtube_id': 'OhrPg_LKUXo', 'order': 1, 'is_mandatory': False},
            {'title': 'Session 2: What is Entrepreneurial Idea?', 'youtube_url': 'https://youtu.be/2xcDY46Gzr8', 'youtube_id': '2xcDY46Gzr8', 'order': 2, 'is_mandatory': False},
            {'title': 'Session 3: Identifying Which Problems to Solve', 'youtube_url': 'https://youtu.be/_jS6-R62zKg', 'youtube_id': '_jS6-R62zKg', 'order': 3, 'is_mandatory': False},
            {'title': 'Session 4: Empathizing with the User/Consumer', 'youtube_url': 'https://youtu.be/GAcGvyJ-QXc', 'youtube_id': 'GAcGvyJ-QXc', 'order': 4, 'is_mandatory': False},
            {'title': 'Session 5: Defining a Problem', 'youtube_url': 'https://youtu.be/s29mCpXwzTs', 'youtube_id': 's29mCpXwzTs', 'order': 5, 'is_mandatory': False},
            {'title': 'Session 6: How to Generate Creative Ideas?', 'youtube_url': 'https://youtu.be/mJIi-DGJU8o', 'youtube_id': 'mJIi-DGJU8o', 'order': 6, 'is_mandatory': False},
            {'title': 'Session 7: Journey of Converting Idea into Product/Service', 'youtube_url': 'https://youtu.be/PUydUNHBKbo', 'youtube_id': 'PUydUNHBKbo', 'order': 7, 'is_mandatory': False},
            {'title': 'Session 8: Building Value', 'youtube_url': 'https://youtu.be/r2p-e71ToLk', 'youtube_id': 'r2p-e71ToLk', 'order': 8, 'is_mandatory': False},
            {'title': 'Session 9: Creating Venture', 'youtube_url': 'https://youtu.be/PausVvudk08', 'youtube_id': 'PausVvudk08', 'order': 9, 'is_mandatory': False},
            {'title': 'Session 10: Communicating Your Venture Story', 'youtube_url': 'https://youtu.be/2e949Ta3IDk', 'youtube_id': '2e949Ta3IDk', 'order': 10, 'is_mandatory': False},
            {'title': 'Session 11: Be India\'s Future Tycoon', 'youtube_url': 'https://youtu.be/2-JMrxoFlHw', 'youtube_id': '2-JMrxoFlHw', 'order': 11, 'is_mandatory': False},
        ]
        for v in videos:
            LearningVideo.objects.update_or_create(
                youtube_id=v['youtube_id'],
                defaults=v
            )
            self.stdout.write(f"  + {v['title']}")
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(videos)} videos'))
