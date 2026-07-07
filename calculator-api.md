# Kalkulyator — Backend spetsifikatsiyasi

> Frontend'dagi kalkulyator (Kalkulyator sahifasi + Band qilish modali) hozir
> mock rejimda ishlaydi. Maqsad: **sozlamalar ham, hisob-kitob ham to'liq
> backenddan kelishi**. Bu hujjatda hamma narsa bor: konfiguratsiya sxemasi,
> formulalar, yaxlitlash qoidasi, endpoint takliflari, booking maydonlari va
> tekshirilgan 8 ta test-holat.

---

## 1. Umumiy tushuncha

Kalkulyator uy narxi bo'yicha to'lov rejasini hisoblaydi. Kiritmalar:

| Kiritma | Tavsif | Misol |
|---|---|---|
| `area` | Uy maydoni (m²) | 49.35 |
| `price_per_m2` | 1 m² narxi (so'm) — sotuvchi o'zgartira oladi | 7 700 000 |
| `payment_type` | To'lov turi | `bosh_tolovli` \| `bosh_tolovsiz` |
| `guarantee` | Kafillik turi → bosh to'lov ulushi | Kafillik 15% \| Kafilsiz 20% |
| `subsidy` | Subsidiya turi → davlat yordami summasi | Yo'q (0) \| Oddiy (30 mln) |
| `credit_years` | Kredit muddati (yil) | 20 \| 15 |
| `manual_down_payment` | Mijoz qo'lda kiritgan bosh to'lov (ixtiyoriy, faqat bosh to'lovlida) | 60 000 000 |
| `rounding` | Yaxlitlash yoqilganmi | true |

Chiqishlar: shartnoma narxi, firma qoplaydigan summa, mijoz to'lovi, kredit
summasi, oylik to'lov(lar).

---

## 2. Sozlamalar (config) — backendda saqlanadi

Bu qiymatlar **o'zgaruvchan** (egalari o'zgartiradi), shuning uchun backendda
saqlanib, frontendga bitta endpoint orqali beriladi:

### `GET /calculator/config/`

```jsonc
{
  "annual_rate_pct": 17,          // kredit yillik foizi (o'zgarishi mumkin)
  "state_threshold_pct": 14,      // subsidiya davrida MIJOZ to'laydigan foiz;
                                  // davlat (annual_rate − threshold) farqini qoplaydi
  "subsidy_years": 5,             // subsidiya davri (yil)
  "firm_markup_pct": 16,          // firma ustamasi / davlatga soliq (16 yoki 15)
  "round_step": 1000,             // yaxlitlash qadami (so'm)
  "default_price_per_m2": 7700000,

  "guarantee_options": [          // kafillik turlari (admin qo'shadi/o'chiradi)
    { "id": 1, "key": "kafillik", "label": "Kafillik 15%", "percent": 15 },
    { "id": 2, "key": "kafilsiz", "label": "Kafilsiz 20%", "percent": 20 }
  ],
  "subsidy_options": [            // subsidiya turlari (admin qo'shadi/o'chiradi)
    { "id": 1, "key": "yoq",   "label": "Yo'q",  "amount": 0 },
    { "id": 2, "key": "oddiy", "label": "Oddiy", "amount": 30000000 }
    // "pedagog" keyinroq qo'shiladi — summasi hali aniqlanmagan
  ],
  "term_options": [20, 15]        // tanlab bo'ladigan kredit muddatlari (yil)
]
```

### Admin boshqaruvi

- `PUT /calculator/config/` — umumiy parametrlarni yangilash (foiz, soliq, ...)
- Kafillik/subsidiya turlari uchun CRUD (yoki hammasi bitta PUT ichida) —
  frontendda allaqachon "qo'shish/tahrirlash/o'chirish" UI tayyor.
- Faqat admin/superadmin o'zgartira oladi; o'qish — hamma uchun.

---

## 3. Formulalar

Belgilashlar: `g` = kafillik ulushi (kasr, 0.15/0.20), `m` = firma ustamasi
(kasr, 0.16), `S` = subsidiya summasi (0 yoki 30 000 000), `R` = yillik foiz
(17), `T` = subsidiya davridagi mijoz foizi (14), `Y` = kredit muddati (yil).

```
base = area × price_per_m2
```

### 3.1 Yaxlitlash qoidasi (MUHIM!)

`rounding = true` bo'lsa: **1000 ga YUQORIGA yaxlitlash (ceil)**:

```
ceil1000(v) = ceil(v / 1000) × 1000
```

- Yaxlitlash **bosqichma-bosqich** qo'llanadi (quyida ko'rsatilgan joylarda),
  kredit esa yaxlitlangan qiymatlardan **ayirma** sifatida chiqadi.
- **Oylik to'lovlar yaxlitlanMAYdi** — so'mgacha aniq ko'rsatiladi
  (masalan 4 737 692 so'm).

### 3.2 Bosh to'lovli (`payment_type = bosh_tolovli`)

```
contract      = base
full_initial  = ceil1000(g × contract)          // to'liq bosh to'lov
firm_covers   = 0

agar manual_down_payment berilgan bo'lsa (M):
  client_payment = M
  credit         = contract − M − S
aks holda:
  client_payment = max(0, full_initial − S)     // davlat S ni qoplaydi
  credit         = contract − full_initial      // subsidiya kreditga ta'sir qilmaydi
```

### 3.3 Bosh to'lovsiz (`payment_type = bosh_tolovsiz`)

Narx shunday oshiriladiki, kredit taxminan `base` atrofida qoladi; bosh
to'lovni firma o'z zimmasiga oladi (ustama `m` bilan):

```
eff           = base − (1 + m) × S
contract      = ceil1000( eff / (1 − g × (1 + m)) )
firm_covers   = ceil1000( g × contract − S )
client_payment= S > 0 ? 0 : ceil1000( firm_covers × m )   // subsidiyali bo'lsa mijoz 0 to'laydi
credit        = contract − firm_covers − client_payment − S
```

### 3.4 Oylik to'lov — annuitet

```
n = Y × 12                          // oylar soni
r = R / 100 / 12                    // oylik foiz
factor(R, Y) = r × (1+r)^n / ((1+r)^n − 1)

monthly_full = credit × factor(R, Y)            // to'liq oylik (yaxlitlanmaydi)
```

Tekshiruv: `factor(17, 20) = 0.0146679...` → 322 995 000 × f = 4 737 692 ✓

### 3.5 Subsidiyali oylik (S > 0)

Davlat dastlabki `subsidy_years` (5) yil davomida **T% (14) dan yuqori
foizni** to'laydi. Ya'ni mijoz shu davrda go'yo kredit T% bo'lganday to'laydi:

```
monthly_stage1 = credit × factor(T, Y)          // mijoz: dastlabki 5 yil (14% annuitet)
gov_monthly    = monthly_full − monthly_stage1  // davlat qoplaydi
// 5 yildan keyin mijoz monthly_full (to'liq 17%) to'laydi
```

Tekshiruv: `factor(14, 20) = 0.0124352...` → 322 995 000 × f = 4 016 510 ✓,
davlat: 4 737 692 − 4 016 510 = 721 182 ✓ (ekran bilan aynan).

---

## 4. Hisoblash endpointi (taklif)

Frontend hech narsa hisoblamasligi uchun:

### `POST /calculator/calculate/`

Request:
```jsonc
{
  "home_id": 61,                  // ixtiyoriy — berilsa area/price_per_m2 uydan olinadi
  "area": 49.35,                  // home_id bo'lmasa majburiy
  "price_per_m2": 7700000,        // sotuvchi o'zgartirgan bo'lishi mumkin
  "payment_type": "bosh_tolovli", // "bosh_tolovli" | "bosh_tolovsiz"
  "guarantee_id": 1,
  "subsidy_id": 2,
  "credit_years": 20,
  "manual_down_payment": null,    // yoki summa (faqat bosh_tolovli)
  "rounding": true
}
```

Response:
```jsonc
{
  "contract_price": 379995000,
  "firm_covers": 0,
  "client_payment": 27000000,
  "subsidy_amount": 30000000,
  "credit_amount": 322995000,
  "monthly_full": 4737692,        // to'liq oylik (subsidiyasiz davr)
  "monthly_stage1": 4016510,      // subsidiyali: dastlabki 5 yil (S=0 bo'lsa null)
  "gov_monthly": 721182,          // subsidiyali: davlat oyligi (S=0 bo'lsa null)
  "subsidy_years": 5,
  "credit_years": 20,
  "annual_rate_pct": 17,
  "state_threshold_pct": 14
}
```

> Variant B (soddaroq): backend faqat `GET /calculator/config/` beradi,
> hisob-kitobni frontend qiladi (formula yuqorida). Lekin **tavsiya — Variant A**
> (backend hisoblaydi): booking'da saqlanadigan summalar manipulyatsiyadan
> himoyalanadi va formula bir joyda turadi.

---

## 5. Booking (Band qilish / Rasmiylashtirish) maydonlari

### 5.1 ESKI payload (hozirgi backend qabul qiladigan)

`POST /booking/` (uy `reserved` bo'lsa `PUT /booking/{id}/`):
```jsonc
{
  "home": 61,
  "client": 354,
  "home_status": "reserved",          // "reserved" | "sold"
  "payment_term": 3,                  // to'lov muddati ID (/booking/payment-term/) yoki null
  "down_payment": 20,                 // boshlang'ich to'lov FOIZI (foizli usulda)
  // yoki naqd usulda:
  "cash_payment": 74151000,
  "cash_payment_percent": "19.51"
}
```

### 5.2 HOZIRGI o'tish holati

Eski to'lov UI olib tashlangan — hozircha shu ketyapti:
`{ home, client, home_status, payment_term: null, down_payment: 0 }`

### 5.3 YANGI payload (kalkulyator bilan — taklif)

```jsonc
{
  "home": 61,
  "client": 354,
  "home_status": "reserved",

  // kalkulyator KIRITMALARI:
  "payment_type": "bosh_tolovli",
  "guarantee_id": 1,                  // yoki key: "kafillik"
  "subsidy_id": 2,                    // yoki key: "oddiy"
  "credit_years": 20,
  "price_per_m2": 7700000,
  "manual_down_payment": null,
  "rounding": true,

  // frontend ko'rsatgan NATIJALAR (solishtirish uchun; asosiy hisob backendda):
  "contract_price": 379995000,
  "firm_covers": 0,
  "client_payment": 27000000,
  "credit_amount": 322995000,
  "monthly_full": 4737692,
  "monthly_stage1": 4016510,
  "gov_monthly": 721182
}
```

Eski maydonlar bilan moslik: `down_payment`(%) → `guarantee_percent`;
`payment_term`(oy ID) → `credit_years`; `cash_payment` → `manual_down_payment`.

---

## 6. Test-holatlar (unit-test uchun) ✅

Barcha holatlarda: `area = 49.35`, `price_per_m2 = 7 700 000`
(base = 379 995 000), `R = 17`, `T = 14`, `m = 16%`, `S(oddiy) = 30 000 000`,
`Y = 20`, `rounding = true`.

| # | To'lov turi | Kafillik | Subsidiya | Shartnoma | Firma | Mijoz | Kredit | Oylik (to'liq) | 5 yil (mijoz) | Davlat |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Bosh to'lovli | 15% | Yo'q | 379 995 000 | 0 | 57 000 000 | 322 995 000 | 4 737 692 | — | — |
| 2 | Bosh to'lovli | 20% | Yo'q | 379 995 000 | 0 | 75 999 000 | 303 996 000 | 4 459 015 | — | — |
| 3 | Bosh to'lovli | 15% | Oddiy | 379 995 000 | 0 | 27 000 000 | 322 995 000 | 4 737 692 | 4 016 510 | 721 182 |
| 4 | Bosh to'lovli | 20% | Oddiy | 379 995 000 | 0 | 45 999 000 | 303 996 000 | 4 459 015 | 3 780 254 | 678 761 |
| 5 | Bosh to'lovsiz | 15% | Yo'q | 460 043 000 | 69 007 000 | 11 042 000 * | 379 994 000 * | 5 573 753 | — | — |
| 6 | Bosh to'lovsiz | 20% | Yo'q | 494 786 000 | 98 958 000 | 15 834 000 * | 379 994 000 * | 5 573 753 | — | — |
| 7 | Bosh to'lovsiz | 20% | Oddiy | 449 473 000 | 59 895 000 | 0 | 359 578 000 | 5 274 292 | 4 471 427 | 802 865 |
| 8 | Bosh to'lovsiz | 15% | Oddiy | 417 912 000 | 32 687 000 | 0 | 355 225 000 | 5 210 442 | 4 417 297 | 793 145 |

`*` — 5/6-holatlarda namunaviy tizim mijozga **11 037 000 / 15 829 000**,
kreditga **379 999 000** ko'rsatgan (jami summa biznikí bilan bir xil, faqat
mijoz↔kredit taqsimotida 5 ming so'm farq). Bu ularning yaxlitlash tartibiga
bog'liq — **egalari bilan aniqlashtirish kerak** (7-bo'limga qarang). Qolgan
6 holat so'migacha aynan mos.

---

## 7. Ochiq savollar (egalari/backend bilan aniqlashtirish)

1. **Bosh to'lovsiz + subsidiyasiz** holatda mijoz to'lovi qaysi tartibda
   yaxlitlanadi? (5 ming so'mlik farq — 6-bo'limdagi `*`)
2. **Pedagog subsidiyasi** — summasi va shartlari (hozircha ro'yxatda yo'q;
   config orqali qo'shiladi).
3. **Qo'lda kiritilgan bosh to'lov** (`manual_down_payment`) uchun cheklovlar
   bormi? (minimal %? maksimal? subsidiya bilan birga bo'lishi mumkinmi?)
4. `annual_rate_pct` / `firm_markup_pct` o'zgarganda **eski shartnomalar**
   eski qiymatda qoladimi? (tavsiya: booking yaratilganda qiymatlar snapshot
   sifatida booking yozuvida saqlansin)
5. Yaxlitlash har doim yoqiqmi, yoki sotuvchi o'chira oladimi? (frontendda
   checkbox bor — default yoniq)

---

## 8. Frontend holati (ma'lumot uchun)

- Engine: `src/app/lib/calculator.ts` — yuqoridagi formulaning aynan o'zi
  (TypeScript). Backendchi solishtirishi mumkin.
- Sozlamalar UI: Kalkulyator sahifasi → "Sozlamalar" tabi (hozircha
  localStorage'da; `GET /calculator/config/` tayyor bo'lgach o'shanga o'tadi).
- Band qilish modali: kalkulyator paneli o'rnatilgan, booking'ga yuborish
  keyingi bosqichda ulanadi (5.3-bo'lim).
