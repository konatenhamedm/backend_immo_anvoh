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
