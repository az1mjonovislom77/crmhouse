from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from user.models import User
from user.selectors.user_selectors import get_user_stats
from user.services.auth.auth_service import AuthService
from user.services.auth.rate_limit import check_login_rate_limit, reset_login_rate_limit
from user.services.user.user_service import UserService

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}


def make_user(**kwargs):
    password = kwargs.pop("password", "testpass123")
    defaults = {"username": "testuser", "full_name": "Test User", "role": User.UserRoles.SELLER}
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


class UserModelTest(TestCase):
    def test_create_user_via_manager(self):
        user = User.objects.create_user(username="newuser", password="pass123", full_name="New")
        self.assertEqual(user.username, "newuser")
        self.assertTrue(user.check_password("pass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        user = User.objects.create_superuser(username="sadmin", password="pass123")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_superuser_requires_is_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username="bad", password="p", is_staff=False)

    def test_superuser_requires_is_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(username="bad2", password="p", is_superuser=False)

    def test_create_user_empty_username_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username="")

    def test_str_returns_full_name(self):
        user = make_user(username="u1", full_name="Ali Vali")
        self.assertEqual(str(user), "Ali Vali")

    def test_str_returns_username_when_no_full_name(self):
        user = make_user(username="u2", full_name="")
        self.assertEqual(str(user), "u2")

    def test_default_role_is_seller(self):
        user = User.objects.create_user(username="s1", password="p")
        self.assertEqual(user.role, User.UserRoles.SELLER)

    def test_username_is_unique(self):
        make_user(username="unique1")
        with self.assertRaises(Exception):
            make_user(username="unique1")

    def test_user_roles_choices(self):
        self.assertEqual(User.UserRoles.SELLER, "s")
        self.assertEqual(User.UserRoles.ADMIN, "a")
        self.assertEqual(User.UserRoles.SUPERADMIN, "sa")


class UserServiceTest(TestCase):
    def test_create_user_hashes_password(self):
        data = {"username": "svc1", "full_name": "Svc", "role": "s", "password": "raw123"}
        user = UserService.create_user(data)
        self.assertNotEqual(user.password, "raw123")
        self.assertTrue(user.check_password("raw123"))

    def test_create_user_saves_to_db(self):
        data = {"username": "svc2", "full_name": "Svc2", "password": "pass"}
        UserService.create_user(data)
        self.assertTrue(User.objects.filter(username="svc2").exists())

    def test_update_user_changes_fields(self):
        user = make_user(username="upd1", full_name="Old")
        UserService.update_user(user, {"full_name": "New Name"})
        user.refresh_from_db()
        self.assertEqual(user.full_name, "New Name")

    def test_update_user_hashes_new_password(self):
        user = make_user(username="upd2", password="oldpass")
        UserService.update_user(user, {"password": "newpass"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass"))

    def test_update_user_no_password_keeps_old(self):
        user = make_user(username="upd3", password="keepme")
        UserService.update_user(user, {"full_name": "Changed"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("keepme"))

    def test_update_user_returns_instance(self):
        user = make_user(username="upd4")
        result = UserService.update_user(user, {"full_name": "X"})
        self.assertEqual(result.pk, user.pk)


@override_settings(CACHES=LOCMEM_CACHE)
class RateLimitTest(TestCase):
    def test_allows_up_to_limit(self):
        for _ in range(7):
            result = check_login_rate_limit("10.0.0.1", "user_a")
            self.assertTrue(result)

    def test_blocks_after_limit_exceeded(self):
        for _ in range(7):
            check_login_rate_limit("10.0.0.2", "user_b")
        self.assertFalse(check_login_rate_limit("10.0.0.2", "user_b"))

    def test_reset_allows_again(self):
        for _ in range(7):
            check_login_rate_limit("10.0.0.3", "user_c")
        reset_login_rate_limit("10.0.0.3", "user_c")
        self.assertTrue(check_login_rate_limit("10.0.0.3", "user_c"))

    def test_different_ips_are_independent(self):
        for _ in range(7):
            check_login_rate_limit("10.0.0.4", "user_d")
        self.assertFalse(check_login_rate_limit("10.0.0.4", "user_d"))
        self.assertTrue(check_login_rate_limit("10.0.0.5", "user_d"))

    def test_different_usernames_are_independent(self):
        for _ in range(7):
            check_login_rate_limit("10.0.0.6", "user_e")
        self.assertFalse(check_login_rate_limit("10.0.0.6", "user_e"))
        self.assertTrue(check_login_rate_limit("10.0.0.6", "user_f"))


@override_settings(CACHES=LOCMEM_CACHE)
class AuthServiceTest(TestCase):
    def setUp(self):
        self.user = make_user(username="authuser", password="pass123")

    def test_login_returns_tokens(self):
        result = AuthService.login_user("authuser", "pass123", "127.0.0.1")
        self.assertIn("tokens", result)
        self.assertIn("access", result["tokens"])
        self.assertIn("refresh", result["tokens"])
        self.assertEqual(result["user"].pk, self.user.pk)

    def test_login_wrong_password_raises(self):
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            AuthService.login_user("authuser", "wrong", "127.0.0.1")

    def test_login_nonexistent_user_raises(self):
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            AuthService.login_user("nobody", "pass123", "127.0.0.1")

    def test_login_inactive_user_raises(self):
        from rest_framework.exceptions import ValidationError
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(ValidationError):
            AuthService.login_user("authuser", "pass123", "127.0.0.1")

    def test_refresh_returns_access_token(self):
        refresh = str(RefreshToken.for_user(self.user))
        result = AuthService.refresh_user_token(refresh)
        self.assertIn("access", result)
        self.assertIsInstance(result["access"], str)

    def test_refresh_none_token_raises(self):
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            AuthService.refresh_user_token(None)

    def test_refresh_invalid_token_raises(self):
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            AuthService.refresh_user_token("invalid.token.here")

    def test_logout_blacklists_token(self):
        from rest_framework.exceptions import ValidationError
        refresh = RefreshToken.for_user(self.user)
        AuthService.logout_user(str(refresh))
        with self.assertRaises(ValidationError):
            AuthService.logout_user(str(refresh))

    def test_logout_invalid_token_raises(self):
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            AuthService.logout_user("bad.token")


class UserSelectorTest(TestCase):
    def setUp(self):
        make_user(username="sel_s1", role=User.UserRoles.SELLER)
        make_user(username="sel_s2", role=User.UserRoles.SELLER)
        make_user(username="sel_a1", role=User.UserRoles.ADMIN)

    def test_counts_by_role(self):
        stats = get_user_stats()
        self.assertGreaterEqual(stats["total_users"], 3)
        self.assertGreaterEqual(stats["total_salers"], 2)
        self.assertGreaterEqual(stats["total_admins"], 1)

    def test_returns_correct_keys(self):
        stats = get_user_stats()
        self.assertIn("total_users", stats)
        self.assertIn("total_salers", stats)
        self.assertIn("total_admins", stats)


@override_settings(CACHES=LOCMEM_CACHE)
class SignInAPIViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="loginuser", password="pass123")
        self.url = reverse("login")

    def test_login_success_returns_access(self):
        resp = self.client.post(self.url, {"username": "loginuser", "password": "pass123"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertIn("access", resp.data["data"])

    def test_login_sets_refresh_cookie(self):
        resp = self.client.post(self.url, {"username": "loginuser", "password": "pass123"})
        self.assertIn("refresh_token", resp.cookies)

    def test_login_wrong_password_returns_400(self):
        resp = self.client.post(self.url, {"username": "loginuser", "password": "wrong"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password_returns_400(self):
        resp = self.client.post(self.url, {"username": "loginuser"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_username_returns_400(self):
        resp = self.client.post(self.url, {"password": "pass123"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user_returns_400(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(self.url, {"username": "loginuser", "password": "pass123"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(CACHES=LOCMEM_CACHE)
class RefreshTokenAPIViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="refuser")
        self.url = reverse("token_refresh")

    def test_refresh_with_valid_cookie(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.client.cookies["refresh_token"] = refresh
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_refresh_without_cookie_returns_400(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(CACHES=LOCMEM_CACHE)
class LogOutAPIViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="logoutuser")
        self.url = reverse("logout")

    def test_logout_authenticated(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated_returns_401(self):
        resp = self.client.post(self.url, {"refresh": "token"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_token_returns_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"refresh": "invalid.token"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class MeAPIViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="meuser", full_name="Me User")
        self.url = reverse("me")

    def test_me_authenticated_returns_user_data(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "meuser")
        self.assertEqual(resp.data["full_name"], "Me User")

    def test_me_unauthenticated_returns_401(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_correct_fields(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        for field in ("id", "full_name", "username", "phone_number", "role", "is_active"):
            self.assertIn(field, resp.data)


class UserViewSetTest(APITestCase):
    def setUp(self):
        self.admin = make_user(username="admin1", role=User.UserRoles.ADMIN)
        self.client.force_authenticate(user=self.admin)
        self.list_url = reverse("user-list")

    def test_list_users_authenticated(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user(self):
        data = {"username": "newone", "full_name": "New One", "password": "pass123", "role": "s"}
        resp = self.client.post(self.list_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newone").exists())

    def test_create_user_password_is_hashed(self):
        data = {"username": "hashtest", "full_name": "H", "password": "mypassword", "role": "s"}
        self.client.post(self.list_url, data)
        user = User.objects.get(username="hashtest")
        self.assertNotEqual(user.password, "mypassword")
        self.assertTrue(user.check_password("mypassword"))

    def test_retrieve_user(self):
        user = make_user(username="retuser", full_name="Ret User")
        url = reverse("user-detail", args=[user.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "retuser")

    def test_update_user(self):
        user = make_user(username="upduser", full_name="Old")
        url = reverse("user-detail", args=[user.id])
        resp = self.client.put(url, {"username": "upduser", "full_name": "Updated", "password": "newp", "role": "s"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.full_name, "Updated")

    def test_delete_user(self):
        user = make_user(username="deluser")
        url = reverse("user-detail", args=[user.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(username="deluser").exists())

    def test_staff_users_excluded(self):
        make_user(username="staffonly", is_staff=True)
        resp = self.client.get(self.list_url)
        usernames = [u["username"] for u in resp.data]
        self.assertNotIn("staffonly", usernames)

    def test_create_duplicate_username_returns_400(self):
        make_user(username="dupuser")
        data = {"username": "dupuser", "full_name": "Dup", "password": "pass", "role": "s"}
        resp = self.client.post(self.list_url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class UserStatsViewTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="statsview")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("user_stats")

    def test_stats_authenticated(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("total_users", resp.data)
        self.assertIn("total_salers", resp.data)
        self.assertIn("total_admins", resp.data)

    def test_stats_unauthenticated_returns_401(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stats_counts_are_non_negative(self):
        resp = self.client.get(self.url)
        self.assertGreaterEqual(resp.data["total_users"], 0)
        self.assertGreaterEqual(resp.data["total_salers"], 0)
        self.assertGreaterEqual(resp.data["total_admins"], 0)
