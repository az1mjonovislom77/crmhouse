import os
from django.conf import settings
import pandas as pd
from django.core.management.base import BaseCommand
from home.models import Home
from utils.models import Blocks, Floors


class Command(BaseCommand):
    help = 'Import homes from Excel file'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'data', 'homes8.xlsx')

        df = pd.read_excel(file_path)

        block_obj, _ = Blocks.objects.get_or_create(title="B-2")

        for _, row in df.iterrows():
            floor_number = int(row['floor'])
            home_number = int(row['home_number'])
            area = float(row['area'])
            rooms = int(row['rooms'])
            price = float(row['price'])

            floor_obj, _ = Floors.objects.get_or_create(number=floor_number)

            Home.objects.update_or_create(
                home_number=home_number,
                floor=floor_obj,
                blocks=block_obj,
                defaults={
                    "area": area,
                    "rooms": rooms,
                    "price_per_sqm": price,
                    "entrance": 1,
                }
            )

        self.stdout.write(self.style.SUCCESS('Import tugadi ✅'))
