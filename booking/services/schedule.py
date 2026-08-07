from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.utils import timezone

ZERO = Decimal("0")

STAGE_SUBSIDY = 1
STAGE_FULL = 2

STATUS_PAID = "paid"
STATUS_PARTIAL = "partial"
STATUS_OVERDUE = "overdue"
STATUS_PENDING = "pending"


def _d(value):
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def add_months(start, months, day=None):
    total = start.year * 12 + (start.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    target_day = day or start.day
    return date(year, month, min(target_day, monthrange(year, month)[1]))


@dataclass
class Installment:
    no: int
    due_date: date
    planned_amount: Decimal
    stage: int
    filled: Decimal = ZERO
    paid_on: date | None = None
    status: str = STATUS_PENDING
    payment_ids: list = field(default_factory=list)

    @property
    def remaining(self):
        value = self.planned_amount - self.filled
        return value if value > ZERO else ZERO

    def as_dict(self):
        return {
            "no": self.no,
            "due_date": self.due_date,
            "planned_amount": self.planned_amount,
            "filled": self.filled,
            "remaining": self.remaining,
            "stage": self.stage,
            "status": self.status,
            "paid_on": self.paid_on,
            "payment_ids": self.payment_ids,
        }


def schedule_start_date(booking):
    if booking.payment_start_date:
        return booking.payment_start_date
    if booking.created_at:
        return timezone.localtime(booking.created_at).date()
    return timezone.localdate()


def down_payment_amount(booking):
    if booking.client_payment is not None:
        return _d(booking.client_payment)
    return _d(booking.manual_down_payment)


def build_schedule(booking):
    months = int(booking.credit_years or 0) * 12
    if months <= 0 or booking.monthly_full is None:
        return []

    start = schedule_start_date(booking)
    pay_day = booking.monthly_payment_day or start.day
    monthly_full = _d(booking.monthly_full)

    stage1_months = 0
    if booking.monthly_stage1 is not None:
        stage1_months = min(int(booking.subsidy_years or 0) * 12, months)
    monthly_stage1 = _d(booking.monthly_stage1)

    schedule = []
    for no in range(1, months + 1):
        stage = STAGE_SUBSIDY if no <= stage1_months else STAGE_FULL
        schedule.append(
            Installment(
                no=no,
                due_date=add_months(start, no, pay_day),
                planned_amount=monthly_stage1 if stage == STAGE_SUBSIDY else monthly_full,
                stage=stage,
            )
        )
    return schedule


def total_planned(booking):
    schedule = build_schedule(booking)
    if not schedule:
        return None
    return down_payment_amount(booking) + sum((i.planned_amount for i in schedule), ZERO)


def _payment_sort_key(payment):
    payment_date = payment.payment_date
    if payment_date is None and payment.created_at:
        payment_date = timezone.localtime(payment.created_at).date()
    return (payment_date or date.min, payment.id or 0)


def allocate(down_payment, schedule, payments, today):
    down_total = _d(down_payment)
    down_filled = ZERO
    down_payment_ids = []
    advance = ZERO
    cursor = 0

    for payment in sorted(payments, key=_payment_sort_key):
        remaining = _d(payment.amount)
        if remaining <= ZERO:
            continue

        if down_filled < down_total:
            take = min(remaining, down_total - down_filled)
            down_filled += take
            remaining -= take
            down_payment_ids.append(payment.id)

        while remaining > ZERO and cursor < len(schedule):
            installment = schedule[cursor]
            need = installment.planned_amount - installment.filled
            if need <= ZERO:
                cursor += 1
                continue
            take = min(remaining, need)
            installment.filled += take
            remaining -= take
            installment.payment_ids.append(payment.id)
            if installment.filled >= installment.planned_amount:
                installment.paid_on = payment.payment_date
                cursor += 1

        if remaining > ZERO:
            advance += remaining

    arrears = ZERO
    prepaid_months = 0
    next_due = None
    for installment in schedule:
        overdue = installment.due_date < today
        if installment.filled >= installment.planned_amount:
            installment.status = STATUS_PAID
            if not overdue:
                prepaid_months += 1
        elif installment.filled > ZERO:
            installment.status = STATUS_OVERDUE if overdue else STATUS_PARTIAL
        else:
            installment.status = STATUS_OVERDUE if overdue else STATUS_PENDING

        if overdue:
            arrears += installment.remaining
        if next_due is None and installment.filled < installment.planned_amount:
            next_due = installment

    if down_filled >= down_total:
        down_status = STATUS_PAID
    elif down_filled > ZERO:
        down_status = STATUS_PARTIAL
    else:
        down_status = STATUS_PENDING

    return {
        "schedule": schedule,
        "arrears": arrears,
        "advance": advance,
        "prepaid_months": prepaid_months,
        "next_due": next_due,
        "down_payment": {
            "amount": down_total,
            "paid": down_filled,
            "status": down_status,
            "payment_ids": down_payment_ids,
        },
    }


def booking_schedule(booking, today=None, payments=None):
    today = today or timezone.localdate()
    payments = list(booking.payments.all()) if payments is None else list(payments)

    schedule = build_schedule(booking)
    result = allocate(down_payment_amount(booking), schedule, payments, today)

    down = result["down_payment"]
    total_planned = down["amount"] + sum((i.planned_amount for i in schedule), ZERO)
    total_paid = sum((_d(p.amount) for p in payments), ZERO)
    next_due = result["next_due"]

    if down["status"] != STATUS_PAID and schedule_start_date(booking) < today:
        down["status"] = STATUS_OVERDUE

    return {
        "kpi": {
            "total_planned": total_planned,
            "total_paid": total_paid,
            "remaining": total_planned - total_paid,
            "arrears": result["arrears"],
            "advance": result["advance"],
            "prepaid_months": result["prepaid_months"],
            "next_due": (
                {
                    "no": next_due.no,
                    "due_date": next_due.due_date,
                    "amount": next_due.planned_amount,
                    "remaining": next_due.remaining,
                }
                if next_due
                else None
            ),
        },
        "down_payment": down,
        "installments": [i.as_dict() for i in schedule],
    }
