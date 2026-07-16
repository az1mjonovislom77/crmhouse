# Home raqamlarini tuzatish:
# har bir (block, entrance) ichida floor 1+ homelar 1 dan boshlab ketma-ket,
# undan keyin -1 (va boshqa manfiy/0) floordagi homelar davomidan raqamlanadi.
#
# Ishga tushirish (avval DRY_RUN=True bilan tekshirib ko'ring):
#   python manage.py shell < fix_home_numbers.py

from collections import defaultdict

from django.db import transaction

from home.models import Home

DRY_RUN = False  # tekshirib bo'lgach False qilib qayta ishga tushiring
ORG_NAME = "Qamashi Xonadonlar"  # faqat shu organizationdagi homelar tuzatiladi

qs = Home.objects.select_related('floor', 'blocks').filter(organization__name=ORG_NAME)
print(f"'{ORG_NAME}' organizationida {qs.count()} ta home topildi.")

groups = defaultdict(list)
skipped = []

for h in qs.order_by('pk'):
    if h.floor is None:
        skipped.append(h)
        continue
    groups[h.blocks_id].append(h)

changed = []

for block_id, homes in sorted(groups.items(), key=lambda x: x[0] or 0):
    number = 0
    for entrance in sorted({h.entrance for h in homes}):
        ent_homes = [h for h in homes if h.entrance == entrance]
        upper = [h for h in ent_homes if h.floor.number >= 1]
        lower = [h for h in ent_homes if h.floor.number < 1]

        # yuqori floorlar: floor o'sish tartibida, floor ichida eski home_number tartibida
        upper.sort(key=lambda h: (h.floor.number, h.home_number, h.pk))
        # pastki floorlar: 0, -1, -2 ... tartibida, floor ichida eski home_number tartibida
        lower.sort(key=lambda h: (-h.floor.number, h.home_number, h.pk))

        for h in upper + lower:
            number += 1
            if h.home_number != number:
                changed.append(h)
                print(f"block={block_id} entrance={entrance} floor={h.floor.number} "
                      f"home_id={h.pk}: {h.home_number} -> {number}")
                h.home_number = number

if skipped:
    print(f"\nDIQQAT: floor=None bo'lgan {len(skipped)} ta home o'tkazib yuborildi: "
          f"{[h.pk for h in skipped]}")

print(f"\nJami o'zgaradigan homelar: {len(changed)}")

if DRY_RUN:
    print("DRY_RUN=True — hech narsa saqlanmadi. Natijani tekshirib, DRY_RUN=False qiling.")
else:
    with transaction.atomic():
        Home.objects.bulk_update(changed, ['home_number'], batch_size=500)
    print("Saqlandi.")
