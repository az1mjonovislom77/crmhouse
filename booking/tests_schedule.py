from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from booking.models import Booking, Commitment, InstallmentAdjustment, Payment
from booking.services.schedule import (
    add_months,
    allocate,
    apply_adjustments,
    booking_schedule,
    build_schedule,
    down_payment_amount,
    set_installment_planned_amount,
)
from common.factories import make_client, make_company, make_home, make_user

CONTRACT_PRICE = Decimal("369685000")
DOWN_PAYMENT = Decimal("73938000")
MONTHLY = Decimal("3880086")
SIGN_DATE = date(2024, 8, 26)
TODAY = date(2026, 8, 7)


def make_installment_booking(**kwargs):
    defaults = {
        "home": make_home(),
        "client": make_client(),
        "company": make_company(),
        "booking_no": "07/70",
        "contract_price": CONTRACT_PRICE,
        "client_payment": DOWN_PAYMENT,
        "credit_amount": CONTRACT_PRICE - DOWN_PAYMENT,
        "payment_start_date": SIGN_DATE,
        "credit_years": 20,
        "monthly_payment_day": 26,
        "monthly_full": MONTHLY,
        "subsidy_years": 0,
        "monthly_stage1": None,
    }
    defaults.update(kwargs)
    return Booking.objects.create(**defaults)


def add_mock_payments(booking):
    Payment.objects.create(booking=booking, amount=DOWN_PAYMENT, payment_date=SIGN_DATE, note="Bosh to'lov")
    for index in range(9):
        Payment.objects.create(booking=booking, amount=MONTHLY, payment_date=add_months(date(2024, 9, 27), index))
    Payment.objects.create(booking=booking, amount=MONTHLY * 3, payment_date=date(2025, 8, 5), note="3 oylik birga")
    for index in range(9):
        Payment.objects.create(booking=booking, amount=MONTHLY, payment_date=add_months(date(2025, 9, 26), index))


class AddMonthsTest(TestCase):
    def test_keeps_payment_day(self):
        self.assertEqual(add_months(date(2024, 8, 26), 1, 26), date(2024, 9, 26))
        self.assertEqual(add_months(date(2024, 8, 26), 12, 26), date(2025, 8, 26))

    def test_clamps_to_short_month(self):
        self.assertEqual(add_months(date(2025, 1, 31), 1, 31), date(2025, 2, 28))
        self.assertEqual(add_months(date(2024, 1, 31), 1, 31), date(2024, 2, 29))

    def test_crosses_year_boundary(self):
        self.assertEqual(add_months(date(2024, 12, 26), 1, 26), date(2025, 1, 26))


class BuildScheduleTest(TestCase):
    def test_generates_one_row_per_month(self):
        booking = make_installment_booking()
        schedule = build_schedule(booking)
        self.assertEqual(len(schedule), 240)
        self.assertEqual(schedule[0].no, 1)
        self.assertEqual(schedule[0].due_date, date(2024, 9, 26))
        self.assertEqual(schedule[-1].no, 240)
        self.assertEqual(schedule[-1].due_date, date(2044, 8, 26))
        self.assertTrue(all(i.planned_amount == MONTHLY for i in schedule))

    def test_subsidy_stage_uses_stage1_amount(self):
        booking = make_installment_booking(
            credit_years=10, subsidy_years=3, monthly_stage1=Decimal("1000000"), monthly_full=Decimal("2000000")
        )
        schedule = build_schedule(booking)
        self.assertEqual(len(schedule), 120)
        self.assertEqual([i.stage for i in schedule[:36]], [1] * 36)
        self.assertEqual([i.stage for i in schedule[36:]], [2] * 84)
        self.assertEqual(schedule[35].planned_amount, Decimal("1000000"))
        self.assertEqual(schedule[36].planned_amount, Decimal("2000000"))

    def test_no_schedule_without_credit_terms(self):
        self.assertEqual(build_schedule(make_installment_booking(credit_years=None)), [])
        self.assertEqual(build_schedule(make_installment_booking(monthly_full=None)), [])

    def test_falls_back_to_start_day_when_payment_day_missing(self):
        booking = make_installment_booking(monthly_payment_day=None)
        self.assertEqual(build_schedule(booking)[0].due_date, date(2024, 9, 26))


class InstallmentAdjustmentTest(TestCase):
    def make_flat_booking(self, **kwargs):
        defaults = {
            "home": make_home(home_number=101),
            "client": make_client(phone_number="+998900000101"),
            "credit_years": 1,
            "monthly_full": Decimal("7000000"),
            "client_payment": Decimal("0"),
        }
        defaults.update(kwargs)
        return make_installment_booking(**defaults)

    def test_increase_cascades_forward_and_conserves_total(self):
        booking = self.make_flat_booking()
        set_installment_planned_amount(booking, 5, Decimal("50000000"))

        schedule = build_schedule(booking)
        amounts = [i.planned_amount for i in schedule]

        self.assertEqual(amounts[:4], [Decimal("7000000")] * 4)
        self.assertEqual(amounts[4], Decimal("50000000"))
        self.assertEqual(amounts[5:11], [Decimal("0")] * 6)
        self.assertEqual(amounts[11], Decimal("6000000"))
        self.assertEqual(sum(amounts, Decimal("0")), Decimal("84000000"))

    def test_edited_installment_stays_full_until_paid(self):
        booking = self.make_flat_booking()
        set_installment_planned_amount(booking, 5, Decimal("50000000"))

        data = booking_schedule(booking, today=SIGN_DATE)
        edited = data["installments"][4]
        self.assertEqual(edited["planned_amount"], Decimal("50000000"))
        self.assertEqual(edited["remaining"], Decimal("50000000"))

    def test_partial_payment_on_edited_installment_shows_remaining_debt(self):
        booking = self.make_flat_booking()
        set_installment_planned_amount(booking, 5, Decimal("50000000"))
        for index in range(4):
            Payment.objects.create(
                booking=booking, amount=Decimal("7000000"), payment_date=add_months(SIGN_DATE, index + 1)
            )
        Payment.objects.create(booking=booking, amount=Decimal("40000000"), payment_date=add_months(SIGN_DATE, 5))

        data = booking_schedule(booking, today=add_months(SIGN_DATE, 5))
        edited = data["installments"][4]
        self.assertEqual(edited["filled"], Decimal("40000000"))
        self.assertEqual(edited["remaining"], Decimal("10000000"))
        self.assertEqual(edited["status"], "partial")

    def test_decrease_spreads_freed_amount_forward_and_conserves_total(self):
        booking = self.make_flat_booking()
        set_installment_planned_amount(booking, 3, Decimal("2500000"))

        amounts = [i.planned_amount for i in build_schedule(booking)]
        self.assertEqual(amounts[:2], [Decimal("7000000")] * 2)
        self.assertEqual(amounts[2], Decimal("2500000"))
        # 4,500,000 freed from month 3, spread evenly across the 9 following months.
        expected_share = Decimal("7000000") + Decimal("4500000") / 9
        self.assertTrue(all(a == expected_share for a in amounts[3:]))
        self.assertEqual(sum(amounts, Decimal("0")), Decimal("84000000"))

    def test_zeroing_several_months_spreads_freed_total_over_remaining(self):
        booking = self.make_flat_booking(credit_years=Decimal("30") / 12, monthly_full=Decimal("27000000"))
        for no in (1, 2, 3):
            set_installment_planned_amount(booking, no, Decimal("0"))

        amounts = [i.planned_amount for i in build_schedule(booking)]
        self.assertEqual(len(amounts), 30)
        self.assertEqual(amounts[:3], [Decimal("0")] * 3)
        # 81,000,000 freed total, spread evenly across the remaining 27 months.
        expected_share = Decimal("27000000") + Decimal("81000000") / 27
        self.assertTrue(all(a == expected_share for a in amounts[3:]))
        self.assertEqual(sum(amounts, Decimal("0")), Decimal("810000000"))

    def test_second_adjustment_recomputes_cascade_from_scratch(self):
        booking = self.make_flat_booking()
        set_installment_planned_amount(booking, 5, Decimal("50000000"))
        set_installment_planned_amount(booking, 5, Decimal("7000000"))

        amounts = [i.planned_amount for i in build_schedule(booking)]
        self.assertTrue(all(a == Decimal("7000000") for a in amounts))

    def test_rejects_out_of_range_installment_number(self):
        booking = self.make_flat_booking()
        with self.assertRaises(ValidationError):
            set_installment_planned_amount(booking, 13, Decimal("1000000"))
        with self.assertRaises(ValidationError):
            set_installment_planned_amount(booking, 0, Decimal("1000000"))

    def test_rejects_negative_amount(self):
        booking = self.make_flat_booking()
        with self.assertRaises(ValidationError):
            set_installment_planned_amount(booking, 1, Decimal("-1"))

    def test_apply_adjustments_helper_is_pure_and_idempotent(self):
        booking = self.make_flat_booking()
        schedule = build_schedule(booking)
        adjustment = InstallmentAdjustment(booking=booking, no=1, planned_amount=Decimal("14000000"))
        apply_adjustments(schedule, [adjustment])
        self.assertEqual(schedule[0].planned_amount, Decimal("14000000"))
        self.assertEqual(schedule[1].planned_amount, Decimal("0"))

    def test_balance_after_running_total(self):
        booking = self.make_flat_booking(credit_years=Decimal("0.25"), monthly_full=Decimal("10000000"))
        schedule = build_schedule(booking)
        self.assertEqual(len(schedule), 3)
        self.assertEqual([i.balance_after for i in schedule], [Decimal("20000000"), Decimal("10000000"), Decimal("0")])


class InstallmentAdjustmentApiTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="installment_adjust_user")
        self.client.force_authenticate(self.user)
        self.booking = make_installment_booking(credit_years=1, monthly_full=Decimal("7000000"))

    def test_patch_installment_cascades_and_persists(self):
        url = reverse("booking-installment", args=[self.booking.id, 5])
        response = self.client.put(url, {"planned_amount": "50000000"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        installments = response.json()["installments"]
        self.assertEqual(Decimal(installments[4]["planned_amount"]), Decimal("50000000"))
        self.assertEqual(Decimal(installments[5]["planned_amount"]), Decimal("0"))
        self.assertEqual(Decimal(installments[11]["planned_amount"]), Decimal("6000000"))

        self.assertEqual(
            InstallmentAdjustment.objects.get(booking=self.booking, no=5).planned_amount, Decimal("50000000")
        )

    def test_patch_out_of_range_returns_400(self):
        url = reverse("booking-installment", args=[self.booking.id, 999])
        response = self.client.put(url, {"planned_amount": "1000000"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_requires_planned_amount(self):
        url = reverse("booking-installment", args=[self.booking.id, 1])
        response = self.client.put(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AllocateTest(TestCase):
    def setUp(self):
        self.booking = make_installment_booking()
        add_mock_payments(self.booking)

    def test_matches_spec_expected_state(self):
        data = booking_schedule(self.booking, today=TODAY)
        installments = data["installments"]

        self.assertEqual(data["down_payment"]["status"], "paid")
        self.assertEqual(data["down_payment"]["paid"], DOWN_PAYMENT)

        self.assertTrue(all(i["status"] == "paid" for i in installments[:21]))
        self.assertEqual(installments[21]["status"], "overdue")
        self.assertEqual(installments[21]["due_date"], date(2026, 6, 26))
        self.assertEqual(installments[22]["status"], "overdue")
        self.assertEqual(installments[23]["status"], "pending")

        kpi = data["kpi"]
        self.assertEqual(kpi["total_planned"], Decimal("1005158640"))
        self.assertEqual(kpi["total_paid"], Decimal("155419806"))
        self.assertEqual(kpi["remaining"], Decimal("849738834"))
        self.assertEqual(kpi["arrears"], MONTHLY * 2)
        self.assertEqual(kpi["prepaid_months"], 0)
        self.assertEqual(kpi["next_due"]["no"], 22)
        self.assertEqual(kpi["next_due"]["due_date"], date(2026, 6, 26))

    def test_batch_payment_closes_three_months(self):
        data = booking_schedule(self.booking, today=TODAY)
        batch = Payment.objects.get(note="3 oylik birga")
        covered = [i["no"] for i in data["installments"] if batch.id in i["payment_ids"]]
        self.assertEqual(covered, [10, 11, 12])
        for no in (10, 11, 12):
            self.assertEqual(data["installments"][no - 1]["paid_on"], date(2025, 8, 5))

    def test_partial_payment_marks_partial_then_overdue(self):
        booking = make_installment_booking(
            home=make_home(home_number=2), client=make_client(phone_number="+998900000002")
        )
        Payment.objects.create(booking=booking, amount=DOWN_PAYMENT + Decimal("1000000"), payment_date=SIGN_DATE)

        data = booking_schedule(booking, today=date(2024, 9, 1))
        self.assertEqual(data["installments"][0]["status"], "partial")
        self.assertEqual(data["installments"][0]["filled"], Decimal("1000000"))
        self.assertEqual(data["kpi"]["arrears"], Decimal("0"))

        data = booking_schedule(booking, today=date(2024, 10, 1))
        self.assertEqual(data["installments"][0]["status"], "overdue")
        self.assertEqual(data["kpi"]["arrears"], MONTHLY - Decimal("1000000"))

    def test_prepaid_months_and_advance(self):
        booking = make_installment_booking(
            home=make_home(home_number=3),
            client=make_client(phone_number="+998900000003"),
            credit_years=1,
            monthly_full=MONTHLY,
        )
        Payment.objects.create(
            booking=booking, amount=DOWN_PAYMENT + MONTHLY * 12 + Decimal("500000"), payment_date=SIGN_DATE
        )
        data = booking_schedule(booking, today=date(2024, 9, 1))
        self.assertEqual(data["kpi"]["prepaid_months"], 12)
        self.assertEqual(data["kpi"]["advance"], Decimal("500000"))
        self.assertIsNone(data["kpi"]["next_due"])
        self.assertEqual(data["kpi"]["arrears"], Decimal("0"))

    def test_payments_are_applied_in_date_order_not_insert_order(self):
        booking = make_installment_booking(
            home=make_home(home_number=4), client=make_client(phone_number="+998900000004")
        )
        late = Payment.objects.create(booking=booking, amount=MONTHLY, payment_date=date(2024, 10, 26))
        early = Payment.objects.create(booking=booking, amount=DOWN_PAYMENT, payment_date=SIGN_DATE)

        data = booking_schedule(booking, today=date(2024, 11, 1))
        self.assertEqual(data["down_payment"]["payment_ids"], [early.id])
        self.assertEqual(data["installments"][0]["payment_ids"], [late.id])

    def test_unpaid_down_payment_is_overdue(self):
        booking = make_installment_booking(
            home=make_home(home_number=5), client=make_client(phone_number="+998900000005")
        )
        data = booking_schedule(booking, today=TODAY)
        self.assertEqual(data["down_payment"]["status"], "overdue")
        self.assertEqual(data["down_payment"]["paid"], Decimal("0"))

    def test_down_payment_falls_back_to_manual_value(self):
        booking = make_installment_booking(
            home=make_home(home_number=6),
            client=make_client(phone_number="+998900000006"),
            client_payment=None,
            manual_down_payment=Decimal("50000000"),
        )
        self.assertEqual(down_payment_amount(booking), Decimal("50000000"))

    def test_zero_amount_payment_is_ignored(self):
        booking = make_installment_booking(
            home=make_home(home_number=7), client=make_client(phone_number="+998900000007")
        )
        schedule = build_schedule(booking)
        payment = Payment(id=1, amount=Decimal("0"), payment_date=SIGN_DATE)
        result = allocate(DOWN_PAYMENT, schedule, [payment], TODAY)
        self.assertEqual(result["down_payment"]["paid"], Decimal("0"))
        self.assertEqual(result["down_payment"]["payment_ids"], [])


class PayableRemainingTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="payable_user")
        self.client.force_authenticate(self.user)
        self.booking = make_installment_booking()
        self.url = reverse("payment-list")

    def _pay(self, amount):
        return self.client.post(self.url, {"booking": self.booking.id, "amount": str(amount)})

    def test_total_planned_covers_interest(self):
        self.assertEqual(self.booking.total_planned, Decimal("1005158640"))
        self.assertEqual(self.booking.payable_remaining, Decimal("1005158640"))
        self.assertEqual(self.booking.remaining_debt, CONTRACT_PRICE)

    def test_payment_above_contract_price_is_accepted(self):
        response = self._pay(500000000)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_above_total_planned_is_rejected(self):
        response = self._pay(1005158641)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_cannot_pay_after_full_amount_covered(self):
        self.assertEqual(self._pay(1005158640).status_code, status.HTTP_201_CREATED)
        self.assertEqual(self._pay(1).status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_uses_same_limit(self):
        self._pay(1000000)
        payment = Payment.objects.get(booking=self.booking)
        detail_url = reverse("payment-detail", args=[payment.id])

        ok = self.client.put(detail_url, {"booking": self.booking.id, "amount": "500000000"})
        self.assertEqual(ok.status_code, status.HTTP_200_OK)

        too_much = self.client.put(detail_url, {"booking": self.booking.id, "amount": "1005158641"})
        self.assertEqual(too_much.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_without_credit_terms_keeps_contract_price_limit(self):
        booking = make_installment_booking(
            home=make_home(home_number=11),
            client=make_client(phone_number="+998900000011"),
            credit_years=None,
            monthly_full=None,
        )
        self.assertIsNone(booking.total_planned)
        self.assertEqual(booking.payable_remaining, booking.remaining_debt)

        response = self.client.post(self.url, {"booking": booking.id, "amount": str(CONTRACT_PRICE + 1)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ScheduleApiTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="schedule_user")
        self.client.force_authenticate(self.user)
        self.booking = make_installment_booking()
        add_mock_payments(self.booking)

    def test_schedule_endpoint_returns_full_payload(self):
        url = reverse("booking-schedule", args=[self.booking.id])
        response = self.client.get(url, {"date": "2026-08-07"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(set(data), {"kpi", "down_payment", "installments", "payments", "commitments"})
        self.assertEqual(len(data["installments"]), 240)
        self.assertEqual(len(data["payments"]), 20)
        self.assertEqual(data["kpi"]["arrears"], 7760172)
        self.assertEqual(data["kpi"]["next_due"]["no"], 22)
        self.assertEqual(data["down_payment"]["status"], "paid")

    def test_schedule_rejects_bad_date(self):
        url = reverse("booking-schedule", args=[self.booking.id])
        response = self.client.get(url, {"date": "07.08.2026"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_schedule_defaults_to_today(self):
        url = reverse("booking-schedule", args=[self.booking.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["installments"]), 240)


class CommitmentApiTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="commitment_user")
        self.client.force_authenticate(self.user)
        self.booking = make_installment_booking()

    def test_create_and_list_via_nested_route(self):
        url = reverse("booking-commitments", args=[self.booking.id])
        payload = {
            "expected_date": "2026-08-20",
            "amount": "12000000",
            "note": "Qo'ng'iroq qilindi — 3 oylikni birga beraman dedi",
            "reminder": True,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], "pending")
        self.assertEqual(response.json()["booking"], self.booking.id)
        self.assertEqual(Commitment.objects.get().created_by, self.user)

        listed = self.client.get(url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.json()), 1)

    def test_commitment_viewset_filters_by_booking(self):
        other = make_installment_booking(
            home=make_home(home_number=9), client=make_client(phone_number="+998900000009")
        )
        Commitment.objects.create(booking=self.booking, expected_date=date(2026, 8, 20), amount=Decimal("1000"))
        Commitment.objects.create(booking=other, expected_date=date(2026, 8, 21), amount=Decimal("2000"))

        response = self.client.get(reverse("commitment-list"), {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["booking"], self.booking.id)

    def test_booking_cannot_be_reassigned(self):
        commitment = Commitment.objects.create(
            booking=self.booking, expected_date=date(2026, 8, 20), amount=Decimal("1000")
        )
        other = make_installment_booking(
            home=make_home(home_number=10), client=make_client(phone_number="+998900000010")
        )
        response = self.client.put(
            reverse("commitment-detail", args=[commitment.id]),
            {"booking": other.id, "expected_date": "2026-08-20", "amount": "1000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RemindersApiTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="reminders_user")
        self.client.force_authenticate(self.user)
        self.booking = make_installment_booking()
        add_mock_payments(self.booking)
        self.url = reverse("reminders")

    def test_lists_overdue_and_commitments(self):
        Commitment.objects.create(
            booking=self.booking, expected_date=date(2026, 8, 20), amount=Decimal("12000000"), note="Va'da"
        )
        response = self.client.get(self.url, {"date": "2026-08-07", "days": "30"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["counts"]["overdue"], 2)
        self.assertEqual([item["no"] for item in data["overdue"]], [22, 23])
        self.assertEqual(data["overdue"][0]["days"], 42)
        self.assertEqual(data["overdue"][0]["contract_no"], "07/70")
        self.assertEqual(data["counts"]["commitments"], 1)
        self.assertEqual(data["commitments"][0]["note"], "Va'da")

    def test_upcoming_window_is_respected(self):
        narrow = self.client.get(self.url, {"date": "2026-08-07", "days": "7"}).json()
        self.assertEqual(narrow["counts"]["upcoming"], 0)

        wide = self.client.get(self.url, {"date": "2026-08-07", "days": "30"}).json()
        self.assertEqual([item["no"] for item in wide["upcoming"]], [24])
        self.assertEqual(wide["upcoming"][0]["days"], 19)

    def test_canceled_booking_is_excluded(self):
        self.booking.status = Booking.BookingStatus.CANCELED
        self.booking.save(update_fields=["status"])
        data = self.client.get(self.url, {"date": "2026-08-07", "days": "30"}).json()
        self.assertEqual(data["counts"]["overdue"], 0)

    def test_rejects_invalid_days(self):
        self.assertEqual(self.client.get(self.url, {"days": "500"}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get(self.url, {"days": "abc"}).status_code, status.HTTP_400_BAD_REQUEST)
