from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from common.utils import last_months, to_millions, MONTH_LABELS_UZ
from home.models import Home, HomeStatusHistory
from leads.models import Lead, LeadEvent, STATUS_NEW, STATUS_SUCCESS
from projects.models.project_models import Block, Floors
from stats.selectors.home_selectors import (
    get_block_occupancy, get_home_status_counts, get_homes, get_monthly_sales,
    get_sold_events, get_top_sellers,
)
from stats.selectors.lead_selectors import (
    get_lead_funnel, get_lead_sources, get_lead_stats, get_leads, get_success_conversions,
)

User = get_user_model()


def aware(year, month, day, hour=12):
    return timezone.make_aware(datetime(year, month, day, hour, 0))


def make_sold_event(home, changed_at, changed_by=None, to_status='sold', from_status='reserved'):
    event = HomeStatusHistory.objects.create(
        home=home, from_status=from_status, to_status=to_status, changed_by=changed_by,
    )
    HomeStatusHistory.objects.filter(pk=event.pk).update(changed_at=changed_at)
    return event


class MonthWindowTests(TestCase):
    def test_window_length_and_order(self):
        window = last_months(8)
        self.assertEqual(len(window), 8)
        today = timezone.localdate()
        self.assertEqual(window[-1], (today.year, today.month))

    def test_consecutive_months_roll_over_year(self):
        for (y1, m1), (y2, m2) in zip(last_months(14), last_months(14)[1:]):
            if m1 == 12:
                self.assertEqual((y2, m2), (y1 + 1, 1))
            else:
                self.assertEqual((y2, m2), (y1, m1 + 1))

    def test_to_millions(self):
        self.assertEqual(to_millions(50_000_000), 50.0)
        self.assertEqual(to_millions(1_250_000), 1.2)
        self.assertEqual(to_millions(None), 0.0)


class HomeStatsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create(username='seller1', full_name='Akmal Sotuvchi')
        floor = Floors.objects.create(number=1)
        cls.block1 = Block.objects.create(title='1-blok')
        cls.block2 = Block.objects.create(title='2-blok')
        cls.home1 = Home.objects.create(
            home_number=1, rooms=2, area=50, floor=floor, price_per_sqm=1_000_000,
            blocks=cls.block1, home_status='sold',
        )
        cls.home2 = Home.objects.create(
            home_number=2, rooms=3, area=60, floor=floor, price_per_sqm=1_000_000,
            blocks=cls.block1, home_status='available',
        )
        cls.home3 = Home.objects.create(
            home_number=3, rooms=1, area=40, floor=floor, price_per_sqm=1_000_000,
            blocks=cls.block2, home_status='reserved',
        )

    def test_home_status_counts_include_zero_statuses(self):
        counts = get_home_status_counts(get_homes())
        self.assertEqual(counts['sold'], 1)
        self.assertEqual(counts['available'], 1)
        self.assertEqual(counts['reserved'], 1)
        self.assertEqual(counts['kalit_topshirildi'], 0)

    def test_sold_move_within_sold_group_is_not_a_new_sale(self):
        now = timezone.now()
        make_sold_event(self.home1, now)
        make_sold_event(self.home1, now, to_status='kalit_topshirildi', from_status='sold')
        self.assertEqual(get_sold_events().count(), 1)

    def test_monthly_sales_counts_distinct_homes_per_month(self):
        year, month = last_months(2)[0]
        make_sold_event(self.home1, aware(year, month, 5))
        make_sold_event(self.home2, aware(year, month, 20))
        series = get_monthly_sales(get_sold_events(), months=2)
        self.assertEqual(series[0]['sold'], 2)
        self.assertEqual(series[0]['month'], MONTH_LABELS_UZ[month - 1])
        self.assertEqual(series[1]['sold'], 0)

    def test_top_sellers_do_not_double_count_resold_home(self):
        now = timezone.now()
        # home1 sotildi, qaytarildi, yana sotildi — narxi bir marta sanalishi kerak
        make_sold_event(self.home1, now, changed_by=self.seller)
        make_sold_event(self.home1, now, changed_by=self.seller)
        sellers = get_top_sellers(get_sold_events())
        self.assertEqual(len(sellers), 1)
        self.assertEqual(sellers[0]['sold'], 1)
        self.assertEqual(sellers[0]['revenue'], 50.0)  # 50m2 * 1 mln = 50 mln

    def test_block_occupancy(self):
        blocks = get_block_occupancy(get_homes())
        self.assertEqual(blocks[0], {'block': '1-blok', 'total': 2, 'occupied': 1})
        self.assertEqual(blocks[1], {'block': '2-blok', 'total': 1, 'occupied': 1})


class LeadStatsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sales_lead = Lead.objects.create(
            full_name='A', phone='1', board=Lead.BOARD_SALES, status=STATUS_NEW, source='Instagram',
        )
        cls.cold_lead = Lead.objects.create(
            full_name='B', phone='2', board=Lead.BOARD_COLD, status='yangi', source='Telegram',
        )

    def test_lead_scope_is_sales_board_only(self):
        stats = get_lead_stats(get_leads())
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['new'], 1)
        sources = get_lead_sources(get_leads())
        self.assertEqual(sources, [{'name': 'Instagram', 'value': 1}])

    def test_funnel_has_all_stages_with_zeros(self):
        funnel = get_lead_funnel(get_leads())
        self.assertEqual([s['stage'] for s in funnel],
                         ['Yangi murojaat', 'Uchrashuv', 'Jarayon', 'Muvaffaqiyatli'])
        self.assertEqual(funnel[0]['count'], 1)
        self.assertEqual(funnel[3]['count'], 0)

    def test_success_counted_by_conversion_time_not_created_time(self):
        event = LeadEvent.objects.create(
            lead=self.sales_lead, type=LeadEvent.TYPE_STATUS,
            from_value='jarayon', to_value=STATUS_SUCCESS,
        )
        LeadEvent.objects.filter(pk=event.pk).update(at=aware(2026, 7, 2))
        # lead created_at bugun, lekin konversiya 2-iyulda — iyul oynasida sanaladi
        self.assertEqual(get_success_conversions(get_leads(), date(2026, 7, 1), date(2026, 7, 31)), 1)
        self.assertEqual(get_success_conversions(get_leads(), date(2026, 6, 1), date(2026, 6, 30)), 0)

    def test_success_same_lead_converted_twice_counts_once(self):
        for _ in range(2):
            event = LeadEvent.objects.create(
                lead=self.sales_lead, type=LeadEvent.TYPE_STATUS,
                from_value='jarayon', to_value=STATUS_SUCCESS,
            )
            LeadEvent.objects.filter(pk=event.pk).update(at=aware(2026, 7, 2))
        self.assertEqual(get_success_conversions(get_leads(), date(2026, 7, 1), date(2026, 7, 31)), 1)

    def test_success_legacy_lead_without_events_falls_back_to_created_at(self):
        # Import qilingan lead: statusi success, lekin LeadEvent yozuvi yo'q
        legacy = Lead.objects.create(
            full_name='C', phone='3', board=Lead.BOARD_SALES, status=STATUS_SUCCESS, source='Boshqa',
        )
        today = timezone.localdate()
        self.assertEqual(get_success_conversions(get_leads(), today, today), 1)
        # Eventi bor lead legacy fallback'ka tushmasligi kerak (ikki marta sanalmaydi)
        event = LeadEvent.objects.create(
            lead=legacy, type=LeadEvent.TYPE_STATUS, from_value='jarayon', to_value=STATUS_SUCCESS,
        )
        LeadEvent.objects.filter(pk=event.pk).update(at=aware(today.year, today.month, today.day))
        self.assertEqual(get_success_conversions(get_leads(), today, today), 1)
