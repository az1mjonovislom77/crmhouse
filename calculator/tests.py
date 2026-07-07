from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from calculator.engine import calculate, ceil_step
from calculator.models import CalculatorConfig, GuaranteeOption, SubsidyOption
from user.models import User

AREA = Decimal("49.35")
PRICE = Decimal("7700000")


def make_user(**kwargs):
    password = kwargs.pop("password", "pass123")
    defaults = {"username": "calc_user", "full_name": "Calc User",
                "role": User.UserRoles.SELLER, "is_staff": True}
    defaults.update(kwargs)
    u = User(**defaults)
    u.set_password(password)
    u.save()
    return u


class CeilStepTest(TestCase):
    def test_ceils_up(self):
        self.assertEqual(ceil_step(56999250, 1000), Decimal("57000000"))

    def test_exact_multiple_unchanged(self):
        self.assertEqual(ceil_step(57000000, 1000), Decimal("57000000"))

    def test_step_zero_returns_value(self):
        self.assertEqual(ceil_step(Decimal("123.45"), 0), Decimal("123.45"))


class EngineTest(TestCase):

    def setUp(self):
        self.config = CalculatorConfig.load()

    def _calc(self, payment_type, g, s, **kw):
        return calculate(area=AREA, price_per_m2=PRICE, payment_type=payment_type,
                         guarantee_percent=g, subsidy_amount=s, credit_years=20,
                         rounding=True, config=self.config, **kw)

    def assert_case(self, r, contract, firm, client, credit, monthly,
                    stage1=None, gov=None):
        self.assertEqual(r['contract_price'], Decimal(contract))
        self.assertEqual(r['firm_covers'], Decimal(firm))
        self.assertEqual(r['client_payment'], Decimal(client))
        self.assertEqual(r['credit_amount'], Decimal(credit))
        self.assertEqual(r['monthly_full'], Decimal(monthly))
        if stage1 is None:
            self.assertIsNone(r['monthly_stage1'])
            self.assertIsNone(r['gov_monthly'])
        else:
            self.assertEqual(r['monthly_stage1'], Decimal(stage1))
            self.assertEqual(r['gov_monthly'], Decimal(gov))

    def test_case_1_bosh_tolovli_15_yoq(self):
        r = self._calc('bosh_tolovli', 15, 0)
        self.assert_case(r, "379995000", "0", "57000000", "322995000", "4737692")

    def test_case_2_bosh_tolovli_20_yoq(self):
        r = self._calc('bosh_tolovli', 20, 0)
        self.assert_case(r, "379995000", "0", "75999000", "303996000", "4459015")

    def test_case_3_bosh_tolovli_15_oddiy(self):
        r = self._calc('bosh_tolovli', 15, 30000000)
        self.assert_case(r, "379995000", "0", "27000000", "322995000", "4737692",
                         "4016510", "721182")

    def test_case_4_bosh_tolovli_20_oddiy(self):
        r = self._calc('bosh_tolovli', 20, 30000000)
        self.assert_case(r, "379995000", "0", "45999000", "303996000", "4459015",
                         "3780254", "678761")
    def test_case_5_bosh_tolovsiz_15_yoq(self):
        r = self._calc('bosh_tolovsiz', 15, 0)
        self.assert_case(r, "460043000", "69007000", "11042000", "379994000", "5573754")

    def test_case_6_bosh_tolovsiz_20_yoq(self):
        r = self._calc('bosh_tolovsiz', 20, 0)
        self.assert_case(r, "494786000", "98958000", "15834000", "379994000", "5573754")

    def test_case_7_bosh_tolovsiz_20_oddiy(self):
        r = self._calc('bosh_tolovsiz', 20, 30000000)
        self.assert_case(r, "449473000", "59895000", "0", "359578000", "5274292",
                         "4471427", "802865")

    def test_case_8_bosh_tolovsiz_15_oddiy(self):
        r = self._calc('bosh_tolovsiz', 15, 30000000)
        self.assert_case(r, "417912000", "32687000", "0", "355225000", "5210442",
                         "4417297", "793145")

    def test_manual_down_payment(self):
        r = self._calc('bosh_tolovli', 15, 0, manual_down_payment=Decimal("60000000"))
        self.assertEqual(r['client_payment'], Decimal("60000000"))
        self.assertEqual(r['credit_amount'], Decimal("319995000"))


class ConfigTest(TestCase):
    def test_singleton_load(self):
        c1 = CalculatorConfig.load()
        c2 = CalculatorConfig.load()
        self.assertEqual(c1.pk, c2.pk)
        self.assertEqual(CalculatorConfig.objects.count(), 1)

    def test_save_forces_single_row(self):
        c = CalculatorConfig.load()
        c.annual_rate_pct = 18
        c.save()
        self.assertEqual(CalculatorConfig.objects.count(), 1)
        self.assertEqual(CalculatorConfig.objects.get(pk=1).annual_rate_pct, 18)

    def test_seed_options_exist(self):
        self.assertTrue(GuaranteeOption.objects.filter(key="kafillik").exists())
        self.assertTrue(SubsidyOption.objects.filter(key="oddiy").exists())


class ConfigApiTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="calc_api")
        self.client.force_authenticate(user=self.user)

    def test_get_config(self):
        resp = self.client.get(reverse("calculator-config"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["annual_rate_pct"], "17.00")
        self.assertEqual(len(resp.data["guarantee_options"]), 2)
        self.assertEqual(resp.data["term_options"], [20, 15])

    def test_update_config_admin(self):
        resp = self.client.put(reverse("calculator-config"),
                               {"annual_rate_pct": "18.00"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(CalculatorConfig.load().annual_rate_pct, Decimal("18.00"))

    def test_unauthenticated_denied(self):
        self.client.logout()
        resp = self.client.get(reverse("calculator-config"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TengUlushFormulaTest(TestCase):

    def test_equal_split(self):
        config = CalculatorConfig.load()
        config.formula_key = 'teng_ulush'
        r = calculate(area=AREA, price_per_m2=PRICE, payment_type='bosh_tolovli',
                      guarantee_percent=15, subsidy_amount=0, credit_years=20,
                      rounding=True, config=config)
        self.assertEqual(r['contract_price'], Decimal("379995000"))
        self.assertEqual(r['client_payment'], Decimal("57000000"))
        self.assertEqual(r['credit_amount'], Decimal("322995000"))
        self.assertEqual(r['monthly_full'], Decimal("1345813"))
        self.assertIsNone(r['monthly_stage1'])

    def test_dispatcher_picks_by_formula_key(self):
        std = CalculatorConfig.load()
        std.formula_key = 'standart'
        teng = CalculatorConfig.load()
        teng.formula_key = 'teng_ulush'
        kw = dict(area=AREA, price_per_m2=PRICE, payment_type='bosh_tolovli',
                  guarantee_percent=15, subsidy_amount=0, credit_years=20, rounding=True)
        self.assertNotEqual(calculate(config=std, **kw)['monthly_full'],
                            calculate(config=teng, **kw)['monthly_full'])


class OrgScopedConfigTest(TestCase):
    def setUp(self):
        from organization.models import Organization
        self.org = Organization.objects.create(name="OrgB")

    def test_org_gets_own_config(self):
        cfg = CalculatorConfig.objects.create(organization=self.org, formula_key='teng_ulush')
        self.assertEqual(CalculatorConfig.for_org(self.org).pk, cfg.pk)
        self.assertEqual(CalculatorConfig.for_org(self.org).formula_key, 'teng_ulush')

    def test_org_without_config_falls_back_to_global(self):
        self.assertEqual(CalculatorConfig.for_org(self.org).formula_key, 'standart')

    def test_global_is_standart(self):
        self.assertEqual(CalculatorConfig.for_org(None).formula_key, 'standart')


class OrgScopedApiTest(APITestCase):
    def test_two_orgs_see_different_config(self):
        from organization.models import Organization
        orgb = Organization.objects.create(name="OrgB")
        CalculatorConfig.objects.create(
            organization=orgb, formula_key='teng_ulush', annual_rate_pct=15)

        user_a = make_user(username="orga_user")
        self.client.force_authenticate(user=user_a)
        resp_a = self.client.get(reverse("calculator-config"))
        self.assertEqual(resp_a.data["formula_key"], "standart")
        self.assertEqual(resp_a.data["annual_rate_pct"], "17.00")

        user_b = make_user(username="orgb_user", organization=orgb)
        self.client.force_authenticate(user=user_b)
        resp_b = self.client.get(reverse("calculator-config"))
        self.assertEqual(resp_b.data["formula_key"], "teng_ulush")
        self.assertEqual(resp_b.data["annual_rate_pct"], "15.00")


class CalculateApiTest(APITestCase):
    def setUp(self):
        from home.models import Home
        self.user = make_user(username="calc_calc")
        self.client.force_authenticate(user=self.user)
        self.guarantee = GuaranteeOption.objects.get(key="kafillik")
        self.subsidy = SubsidyOption.objects.get(key="oddiy")
        self.home = Home.objects.create(
            home_number=1, area=AREA, price_per_sqm=PRICE)

    def test_calculate_case_3(self):
        resp = self.client.post(reverse("calculator-calculate"), {
            "home_id": self.home.id,
            "payment_type": "bosh_tolovli",
            "guarantee_id": self.guarantee.id,
            "subsidy_id": self.subsidy.id,
            "credit_years": 20,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["contract_price"], Decimal("379995000"))
        self.assertEqual(resp.data["client_payment"], Decimal("27000000"))
        self.assertEqual(resp.data["credit_amount"], Decimal("322995000"))
        self.assertEqual(resp.data["monthly_full"], Decimal("4737692"))

    def test_calculate_requires_home_id(self):
        resp = self.client.post(reverse("calculator-calculate"), {
            "payment_type": "bosh_tolovli",
            "guarantee_id": self.guarantee.id,
            "credit_years": 20,
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
