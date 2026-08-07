# Vazifa: To'lov jadvali (installment) sahifasini real backendga ulash

`PaymentSchedulePrototype.tsx` hozir mock ma'lumot bilan ishlaydi. **Backend tayyor va deploy qilingan** —
mock'ni real API bilan almashtir. UI/dizayn o'zgarmaydi, faqat data manbasi almashadi.
Quyida API shartnomasi to'liq keltirilgan — hammasi ishlaydi, taxmin qilish shart emas.

---

## 0. Umumiy qoidalar

- **Auth:** JWT. Har bir so'rovda `Authorization: Bearer <access_token>`.
  - Login: `POST /user/login/` → `{ access, refresh }`
  - Refresh: `POST /user/auth/refresh/` (access 15 daqiqa, refresh 7 kun, rotatsiya bor)
- **Base URL:** env orqali (`VITE_API_URL` yoki loyihada qanday bo'lsa).
- **Ro'yxatlar paginatsiya QILINMAYDI** — `results`/`count` wrapper yo'q, to'g'ridan-to'g'ri massiv qaytadi.
- **Xato formati:** `400` → maydon bo'yicha `{ "amount": ["..."] }` yoki umumiy `{ "detail": "..." }`.
  Xato matnlari o'zbekcha — to'g'ridan-to'g'ri toast'da ko'rsatsa bo'ladi.
- **Swagger:** `/api/swagger/` — hamma endpoint va sxemalar shu yerda.

### ⚠️ Summalar turi — E'TIBOR BER

| Qayerda | Turi | Misol |
|---|---|---|
| `schedule` javobidagi `kpi`, `down_payment`, `installments` | **number** | `3880086.0` |
| `payments[].amount`, `commitments[].amount` | **string** | `"3880086.00"` |

Ya'ni `payments`/`commitments` massivlarida `Number(x)` qilib olish kerak,
`installments`/`kpi` da esa allaqachon son.

### 🚫 `remaining_debt` ni ISHLATMA

`payments[].remaining_debt` va booking obyektidagi `remaining_debt` — bu **eski, foizsiz**
ko'rsatkich (`shartnoma narxi − to'langan`). Bo'lib to'lashda umumiy summa foiz bilan
shartnoma narxidan katta, shuning uchun bu qiymat vaqt o'tib **manfiy bo'lib ketadi**.

**Qoldiqni faqat `kpi.remaining` dan ol. Qarzni faqat `kpi.arrears` dan ol.**

---

## 1. Asosiy endpoint — to'lov jadvali

### `GET /booking/{booking_id}/schedule/`

Query (ixtiyoriy):

- `date=YYYY-MM-DD` — "bugun" sifatida qaysi sanani olish. Berilmasa server sanasi.
  (Test/demo uchun qulay: `?date=2026-08-07`.)

Bitta so'rov bilan sahifaga kerak bo'lgan HAMMA narsa keladi — alohida `payments`
yoki `commitments` so'rovi shart emas.

```jsonc
{
  "kpi": {
    "total_planned": 1005158640.0,   // bosh to'lov + barcha oyliklar (foiz bilan)
    "total_paid": 155419806.0,       // haqiqatda to'langan jami
    "remaining": 849738834.0,        // ✅ QOLDIQ — shuni ko'rsat
    "arrears": 7760172.0,            // ✅ QARZ: muddati o'tgan, to'lanmagan summa
    "advance": 0.0,                  // barcha oylar yopilgandan keyin oshib qolgan pul
    "prepaid_months": 0,             // oldindan to'liq to'langan kelajakdagi oylar soni
    "next_due": {                    // birinchi to'liq to'lanmagan oy. Hammasi yopilgan bo'lsa null
      "no": 22,
      "due_date": "2026-06-26",
      "amount": 3880086.0,           // shu oyning reja summasi
      "remaining": 3880086.0         // shu oydan qancha qolgan (qisman to'langan bo'lishi mumkin)
    }
  },

  "down_payment": {                  // BOSH TO'LOV — oylik jadvaldan alohida
    "amount": 73938000.0,
    "paid": 73938000.0,
    "status": "paid",
    "payment_ids": [1]               // qaysi to'lov(lar) bilan yopilgan
  },

  "installments": [                  // UZUNLIGI = credit_years * 12 (240 tagacha!)
    {
      "no": 1,
      "due_date": "2024-09-26",
      "planned_amount": 3880086.0,   // reja
      "filled": 3880086.0,           // shu oyga tushgan pul
      "remaining": 0.0,              // planned_amount - filled (manfiy bo'lmaydi)
      "stage": 2,                    // 1 = subsidiya davri (past oylik), 2 = to'liq stavka
      "status": "paid",
      "paid_on": "2024-09-27",       // to'liq yopilgan sana (yopilmagan bo'lsa null)
      "payment_ids": [2]             // shu oyni qoplagan to'lov id'lari
    }
    // ...
  ],

  "payments": [ /* 2-bo'lim, sana bo'yicha o'sish tartibida */ ],
  "commitments": [ /* 3-bo'lim */ ]
}
```

### Enumlar

`installments[].status` va `down_payment.status`:

| Qiymat | Ma'nosi | Taklif qilingan rang |
|---|---|---|
| `paid` | To'liq to'langan | yashil |
| `partial` | Qisman to'langan, muddati hali kelmagan | sariq |
| `overdue` | Muddati o'tgan (to'lanmagan yoki qisman) — **QARZ** | qizil |
| `pending` | Kutilmoqda, muddati kelmagan | kulrang |

`installments[].stage`: `1` = subsidiya davri (arzon oylik), `2` = to'liq stavka.
Subsidiyasiz shartnomada hamma qator `2` bo'ladi. Subsidiyali shartnomada
stage 1 → 2 o'tish joyida jadvalda ajratuvchi chiziq qo'ysa chiroyli bo'ladi.

### Muhim UI eslatmalari

1. **`installments` 240 tagacha element** — hammasini birdan DOM'ga chizma.
   Virtualizatsiya (`react-window` va sh.k.) yoki "yil bo'yicha yig'ish / ko'proq ko'rsatish" qil.
   Default ko'rinish sifatida `next_due` atrofidagi oynani ochish qulay.
2. **FIFO taqsimot avtomatik** — to'lovni "qaysi oyga" deb belgilash shart emas va
   bunday maydon YO'Q. Mijoz 3 oylikni birga to'lasa, backend o'zi eng eski 3 ta
   to'lanmagan oyni yopadi. `payment_ids` orqali "bu to'lov qaysi oylarni yopdi"
   ni ko'rsatsa bo'ladi (drill-down uchun juda qulay).
3. `arrears > 0` bo'lsa sahifa tepasida qizil banner — "Qarz: X so'm".
4. `advance > 0` yoki `prepaid_months > 0` bo'lsa ko'k banner — "Oldindan to'langan".

---

## 2. To'lovlar

### `GET /booking/payments/?booking_id={id}`

Massiv qaytadi (`schedule` javobidagi `payments` bilan bir xil).

```jsonc
{
  "id": 1,
  "booking": 1,
  "amount": "3880086.00",              // STRING
  "payment_date": "2024-09-27",
  "payment_number": "KV-1000",         // kvitansiya raqami
  "payment_data": "Agrobank o'tkazma", // bank/karta ma'lumoti
  "file": "/media/payments/xxx.jpg",   // kvitansiya rasmi, null bo'lishi mumkin
  "note": "3 oylik birga",
  "created_at": "2026-08-07T15:43:15+05:00",
  "remaining_debt": 214265194.0        // 🚫 ISHLATMA (0-bo'limga qara)
}
```

### `POST /booking/payments/`

Yangi to'lov. Fayl bo'lsa `multipart/form-data`, bo'lmasa JSON.

| Maydon | Majburiy | Izoh |
|---|---|---|
| `booking` | ✅ | booking id |
| `amount` | ✅ | 0 dan katta |
| `payment_date` | ❌ | berilmasa bugun |
| `payment_number` | ❌ | kvitansiya raqami |
| `payment_data` | ❌ | bank/karta |
| `file` | ❌ | pdf/jpg/jpeg/png/webp |
| `note` | ❌ | |

Muvaffaqiyatdan keyin **`schedule/` ni qayta so'ra** — jadval va KPI qayta hisoblanadi
(FIFO taqsimot o'zgaradi, bir necha oy birdan yopilishi mumkin).

Yagona rad etish holati: summa umumiy qoldiqdan (`kpi.remaining`) katta bo'lsa `400`:
`{"amount": ["Kiritilgan summa qoldiq qarzdan (X) ko'p bo'lishi mumkin emas."]}`.
Formada `max = kpi.remaining` qo'ysang, foydalanuvchi bunga umuman duch kelmaydi.

`PUT /booking/payments/{id}/` va `DELETE /booking/payments/{id}/` ham bor —
ikkalasidan keyin ham `schedule/` ni qayta so'ra.

---

## 3. Kelishuvlar (Commitment) — "pul topganda beraman"

Oylik jadvaldan **mustaqil**. Mijoz "falon sanada falon pul beraman" desa shu yerga yoziladi.

### `GET /booking/{booking_id}/commitments/`

### `POST /booking/{booking_id}/commitments/`

Body (`booking` ni yozish shart emas — URL'dan olinadi):

```json
{
  "expected_date": "2026-08-20",
  "amount": "12000000",
  "note": "Qo'ng'iroq qilindi — 3 oylikni birga beraman dedi",
  "reminder": true
}
```

Javob:

```jsonc
{
  "id": 1,
  "booking": 1,
  "expected_date": "2026-08-20",
  "amount": "12000000.00",   // STRING
  "note": "...",
  "status": "pending",       // pending | fulfilled | broken
  "reminder": true,          // eslatmalar ro'yxatiga chiqsinmi
  "created_at": "2026-08-07T15:43:15+05:00",
  "created_by": 3
}
```

### Tahrirlash / o'chirish

- `GET /booking/commitments/?booking_id={id}&status=pending` — filtrlangan ro'yxat
- `PUT /booking/commitments/{id}/` — masalan `{"status": "fulfilled"}` (partial update ishlaydi)
- `DELETE /booking/commitments/{id}/`

`status` **qo'lda** o'zgartiriladi (avtomatik emas): mijoz va'dasini bajarsa `fulfilled`,
bajarmasa `broken`. UI'da ikkita tugma qo'y.

> `booking` maydonini keyin o'zgartirib bo'lmaydi — `400` qaytaradi.

---

## 4. Eslatmalar (quruvchi/menejer uchun umumiy ro'yxat)

### `GET /reminders/?date=YYYY-MM-DD&days=7`

- `date` — ixtiyoriy, default bugun
- `days` — oldinga necha kunlik oyna. Default `7`, maksimum `90`

```jsonc
{
  "date": "2026-08-07",
  "days": 30,
  "counts": { "overdue": 2, "upcoming": 1, "commitments": 1 },  // badge uchun

  "overdue": [      // muddati o'tgan, to'lanmagan oyliklar (barcha aktiv bookinglar bo'yicha)
    {
      "kind": "overdue",
      "booking_id": 1,
      "client": "Abdullayeva Musavvar Fayzulloyevna",
      "phone": "+998947072838",
      "apartment": "4A-blok · 2-xonadon · 1-qavat",
      "contract_no": "07/70",
      "no": 22,                  // installment raqami
      "due_date": "2026-06-26",
      "amount": 3880086.0,       // QOLDIQ (qisman to'langan bo'lsa kamayadi), number
      "days": 42,                // necha kun kechikkan
      "note": null
    }
  ],

  "upcoming": [ /* shu ko'rinishda, "days" = necha kun qolgani */ ],

  "commitments": [ /* kind: "commitment", "no": null, "note" to'ldirilgan */ ]
}
```

Sahifa: 3 ta tab yoki 3 ta ustun — **Qarzlar** (qizil) / **Yaqin to'lovlar** (sariq) /
**Kelishuvlar** (ko'k). Har bir qatorda telefon raqamiga `tel:` link va bookingga o'tish tugmasi.
`counts` ni sidebar badge sifatida ishlat.

Faqat **aktiv** bookinglar chiqadi (bekor qilinganlar avtomatik chiqib ketadi),
va foydalanuvchining tashkiloti bo'yicha filtrlanadi.

---

## 5. Qabul qilish mezoni (demo booking bilan tekshir)

`GET /booking/{id}/schedule/?date=2026-08-07` — 20 yillik, 240 oylik shartnoma uchun:

- bosh to'lov `paid`
- #1–#21 → `paid` (shundan #10, #11, #12 bitta batch to'lov bilan yopilgan — `payment_ids` bir xil)
- #22 (26.06.2026) va #23 (26.07.2026) → `overdue`
- #24+ → `pending`
- `kpi.arrears` = 7 760 172
- `kpi.next_due.no` = 22
- `kpi.remaining` = 849 738 834
- `kpi.total_planned` = 1 005 158 640

Bu raqamlar backend testlarida qat'iy tekshirilgan — agar boshqacha chiqsa, backendga ayt.

---

## 6. Nima YO'Q (hozircha qilinmaydi)

- Jarima/penya (0.04%/kun) — o'chirilgan, keyinroq `penalty` qatlami qo'shiladi
- SMS / Telegram / push eslatma — hozircha faqat ilova ichidagi ro'yxat
- To'lovni qo'lda ma'lum bir oyga biriktirish — taqsimot faqat FIFO
- Oylik summani qo'lda o'zgartirish — reja booking maydonlaridan generatsiya qilinadi
