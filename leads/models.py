from django.db import models
from django.conf import settings

SALES_STATUSES = {
    'yangi_murojaat': ['murojaat_qildi', 'kordi_eshitdi'],
    'uchrashuv': ['uchrashuv_belgilandi', 'keldi'],
    'jarayon': ['band_qildi', 'shartnoma_qildi', 'notarius'],
    'muvaffaqiyatli': ['uy_oldi'],
    'bekor_qilingan': ['atkaz_qildi', 'nohaq_haqorat'],
}

COLD_STATUSES = {
    'yangi': ['yangi'],
    'oylab_koradi': ['oylab_koradi'],
    'kotarmadi': ['kotarmadi'],
    'qiziqmadi': ['qiziqmadi'],
}

BOARD_STATUSES = {
    'sales': SALES_STATUSES,
    'cold': COLD_STATUSES,
}

BOARD_FIRST_STATUS = {
    'sales': 'yangi_murojaat',
    'cold': 'yangi',
}


class Lead(models.Model):
    BOARD_SALES = 'sales'
    BOARD_COLD = 'cold'
    BOARD_CHOICES = [
        (BOARD_SALES, 'Sales'),
        (BOARD_COLD, 'Cold'),
    ]
    SOURCE_CHOICES = [
        ('Instagram', 'Instagram'),
        ('Telegram', 'Telegram'),
        ('Facebook', 'Facebook'),
        ('LinkedIn', 'LinkedIn'),
        ("Qo'ng'iroq", "Qo'ng'iroq"),
        ('Veb-sayt', 'Veb-sayt'),
        ('Tavsiya', 'Tavsiya'),
        ('Reklama', 'Reklama'),
        ('Boshqa', 'Boshqa'),
    ]

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='Boshqa')
    board = models.CharField(max_length=10, choices=BOARD_CHOICES, default=BOARD_SALES)
    status = models.CharField(max_length=50)
    sub_status = models.CharField(max_length=50, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name='owned_leads')
    score = models.PositiveSmallIntegerField(default=0)
    note = models.TextField(null=True, blank=True)
    meeting_at = models.DateTimeField(null=True, blank=True)
    meeting_type = models.CharField(max_length=20, null=True, blank=True)
    subsidiya = models.BooleanField(default=False)
    contacted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['board', 'status']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.board}:{self.status})"


class LeadEvent(models.Model):
    TYPE_CREATED = 'created'
    TYPE_STATUS = 'status'
    TYPE_SUB_STATUS = 'sub_status'
    TYPE_COMMENT = 'comment'
    TYPE_CALL = 'call'
    TYPE_TRANSFER = 'transfer'
    TYPE_MEETING = 'meeting'
    TYPE_SUBSIDIYA = 'subsidiya'

    TYPE_CHOICES = [
        (TYPE_CREATED, 'Created'),
        (TYPE_STATUS, 'Status changed'),
        (TYPE_SUB_STATUS, 'Sub-status changed'),
        (TYPE_COMMENT, 'Comment'),
        (TYPE_CALL, 'Call'),
        (TYPE_TRANSFER, 'Transfer'),
        (TYPE_MEETING, 'Meeting'),
        (TYPE_SUBSIDIYA, 'Subsidiya changed'),
    ]
    MEETING_TYPE_CHOICES = [
        ('Ofisda', 'Ofisda'),
        ('Showroomda', 'Showroomda'),
        ('Online', 'Online'),
        ('Obyektda', 'Obyektda'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='events')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    from_value = models.CharField(max_length=200, null=True, blank=True)
    to_value = models.CharField(max_length=200, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    meeting_at = models.DateTimeField(null=True, blank=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, null=True, blank=True)
    subsidiya = models.BooleanField(default=False)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='lead_events')
    at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ['at']

    def __str__(self):
        return f"{self.lead_id} — {self.type} @ {self.at}"
