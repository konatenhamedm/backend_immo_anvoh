"""Mot de passe oublié et connexion par code : réponses identiques que le compte existe ou non, codes à usage unique."""

import re

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.infrastructure.models import User, UserRole

NEW = "Nouveau-Mot2Passe-Solide"


class AccountAccessTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="awa@test.ci",
            password="Ancien-Mot2Passe",
            first_name="Awa",
            last_name="K",
            phone_number="0700000000",
            role=UserRole.PARTICULIER,
        )
        self.c = APIClient()

    def post(self, path, data):
        return self.c.post(f"/api/v1/auth/{path}", data, format="json")

    def test_forgot_is_silent_for_unknown_accounts(self):
        known = self.post("password/forgot/", {"email": "awa@test.ci"})
        unknown = self.post("password/forgot/", {"email": "nobody@test.ci"})
        assert known.status_code == unknown.status_code == 200 and known.json() == unknown.json()
        assert len(mail.outbox) == 1

    def test_reset_link_works_once(self):
        self.post("password/forgot/", {"email": "awa@test.ci"})
        m = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[0].body)
        body = {"uid": m[1], "token": m[2], "new_password": NEW}
        assert self.post("password/reset/", body).status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password(NEW)
        assert self.post("password/reset/", {**body, "new_password": "Autre-Mot2Passe-Solide"}).status_code == 400

    def test_reset_rejects_forged_link(self):
        assert self.post("password/reset/", {"uid": "MQ", "token": "x", "new_password": NEW}).status_code == 400

    def test_code_login(self):
        self.post("code/request/", {"email": "awa@test.ci"})
        code = re.search(r"\b(\d{6})\b", mail.outbox[0].subject)[1]
        wrong = "000000" if code != "000000" else "111111"
        assert self.post("code/verify/", {"email": "awa@test.ci", "code": wrong}).status_code == 400
        r = self.post("code/verify/", {"email": "awa@test.ci", "code": code})
        assert r.status_code == 200 and r.json()["user"]["email"] == "awa@test.ci"
        assert self.post("code/verify/", {"email": "awa@test.ci", "code": code}).status_code == 400  # usage unique

    def test_code_locks_after_five_wrong_attempts(self):
        self.post("code/request/", {"email": "awa@test.ci"})
        code = re.search(r"\b(\d{6})\b", mail.outbox[0].subject)[1]
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(5):
            self.post("code/verify/", {"email": "awa@test.ci", "code": wrong})
        assert self.post("code/verify/", {"email": "awa@test.ci", "code": code}).status_code == 400

    def test_suspended_account_gets_nothing(self):
        self.user.is_active = False
        self.user.save()
        self.post("code/request/", {"email": "awa@test.ci"})
        self.post("password/forgot/", {"email": "awa@test.ci"})
        assert mail.outbox == []


class GoogleLoginTests(TestCase):
    URL = "/api/v1/auth/google/"

    def setUp(self):
        self.c = APIClient()

    def claims(self, **kw):
        return {"email": "nouvelle@test.ci", "email_verified": True, "given_name": "Nina", "family_name": "Koné", **kw}

    def test_disabled_without_client_id(self):
        with self.settings(GOOGLE_CLIENT_ID=""):
            assert self.c.post(self.URL, {"credential": "x"}, format="json").status_code == 501

    def test_invalid_token_is_refused(self):
        with self.settings(GOOGLE_CLIENT_ID="cid"):
            assert self.c.post(self.URL, {"credential": "pas-un-jeton"}, format="json").status_code == 400

    def test_creates_then_reuses_account(self):
        from unittest import mock

        with (
            self.settings(GOOGLE_CLIENT_ID="cid"),
            mock.patch("apps.users.application.google_login.verify", return_value=self.claims()),
        ):
            r = self.c.post(self.URL, {"credential": "ok"}, format="json")
            assert r.status_code == 200 and r.json()["user"]["role"] == "PARTICULIER"
            again = self.c.post(self.URL, {"credential": "ok"}, format="json")
            assert again.json()["user"]["id"] == r.json()["user"]["id"]
        assert User.objects.filter(email="nouvelle@test.ci").count() == 1
        assert not User.objects.get(email="nouvelle@test.ci").has_usable_password()

    def test_staff_accounts_cannot_use_google(self):
        from unittest import mock

        User.objects.create_user(
            email="boss@test.ci",
            password="Un-Mot2Passe-Solide",
            first_name="B",
            last_name="B",
            phone_number="0700000000",
            role=UserRole.ADMIN,
        )
        with (
            self.settings(GOOGLE_CLIENT_ID="cid"),
            mock.patch("apps.users.application.google_login.verify", return_value=self.claims(email="boss@test.ci")),
        ):
            assert self.c.post(self.URL, {"credential": "ok"}, format="json").status_code == 400

    def test_listed_staff_account_can_use_google(self):
        from unittest import mock

        User.objects.create_user(
            email="boss@test.ci",
            password="Un-Mot2Passe-Solide",
            first_name="B",
            last_name="B",
            phone_number="0700000000",
            role=UserRole.ADMIN,
        )
        claims = self.claims(email="boss@test.ci")
        with (
            self.settings(GOOGLE_CLIENT_ID="cid", GOOGLE_STAFF_EMAILS=["boss@test.ci"]),
            mock.patch("apps.users.application.google_login.verify", return_value=claims),
        ):
            r = self.c.post(self.URL, {"credential": "ok"}, format="json")
        assert r.status_code == 200 and r.json()["user"]["role"] == "ADMIN"


class CompleteProfileTests(TestCase):
    URL = "/api/v1/auth/profile/complete/"

    def user(self, role):
        return User.objects.create_user(
            email=f"{role.lower()}@test.ci",
            password="Un-Mot2Passe-Solide",
            first_name="A",
            last_name="B",
            phone_number="",
            role=role,
        )

    def post(self, user, data):
        c = APIClient()
        c.force_authenticate(user)
        return c.post(self.URL, data, format="json")

    def test_google_user_completes_profile(self):
        u = self.user(UserRole.PARTICULIER)
        r = self.post(
            u, {"role": "PROPRIETAIRE", "phone_number": "+33 6 12 34 56 78", "country_of_residence": "France"}
        )
        assert r.status_code == 200
        u.refresh_from_db()
        assert (u.role, u.phone_number, u.is_diaspora) == ("PROPRIETAIRE", "+33 6 12 34 56 78", True)

    def test_phone_is_required(self):
        assert self.post(self.user(UserRole.PARTICULIER), {"role": "INVESTISSEUR"}).status_code == 400

    def test_staff_cannot_change_role_here(self):
        u = self.user(UserRole.ADMIN)
        assert self.post(u, {"role": "PARTICULIER", "phone_number": "0700000000"}).status_code == 403
        u.refresh_from_db()
        assert u.role == UserRole.ADMIN

    def test_cannot_become_staff(self):
        assert (
            self.post(self.user(UserRole.PARTICULIER), {"role": "ADMIN", "phone_number": "0700000000"}).status_code
            == 400
        )
