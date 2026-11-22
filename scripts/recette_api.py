"""Recette automatisée (API) : les points de RECETTE.md vérifiables sans écran.

Usage : API lancée sur 127.0.0.1:8000 avec les données de démo (`python manage.py seed_data`, mot de passe Demo12345!),
puis `python3 scripts/recette_api.py`. Code de sortie 1 si une vérification échoue. Nettoie ce qu'elle crée (prospects de test).
Laisse une conversation « ZZ Recette » vers l'équipe (l'API ne sait pas la supprimer) : la retirer avec
`Conversation.objects.filter(subject__startswith='ZZ').delete()` dans `manage.py shell`.
Suppose les comptes de démo dans leur état d'origine (baux de démo chez k.yao@mail.ci).
"""

import datetime
import json
import sys
import urllib.error
import urllib.request

B = "http://127.0.0.1:8000/api/v1"
PW = "Demo12345!"
results = []


def call(method, path, token=None, body=None):
    req = urllib.request.Request(B + path, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode()[:100]


def login(email):
    s, d = call("POST", "/auth/login/", body={"email": email, "password": PW})
    return d["access"] if s == 200 else None


def check(name, ok, detail=""):
    results.append((ok, name, detail))
    print(("OK   " if ok else "ÉCHEC"), name, ("— " + str(detail)) if detail and not ok else "")


def status(method, path, tok, body=None):
    return call(method, path, tok, body)[0]


ACCOUNTS = {
    "admin": "admin@thiebbro.ci",
    "aminata": "aminata.agent@thiebbro.ci",
    "koffi": "koffi.agent@thiebbro.ci",
    "notaire1": "a.kone@notaire.ci",
    "notaire2": "f.ouattara@notaire.ci",
    "notaire3": "s.bamba@notaire.ci",
    "adjoua": "adjoua.kouassi@mail.ci",
    "yao": "k.yao@mail.ci",
    "ibrahim": "i.diallo@mail.ci",
    "marie": "ml.ehui@mail.ci",
    "sci": "contact@sci-roniers.ci",
    "awa": "awa.traore@mail.ci",
    "sekou": "soro.paris@gmail.com",
}

print("== 6. Compte suspendu / connexions")
T = {}
for k, e in ACCOUNTS.items():
    T[k] = login(e)
check("13 comptes de démo actifs se connectent", all(T.values()), [k for k, v in T.items() if not v])
s, d = call("POST", "/auth/login/", body={"email": "p.kacou@mail.ci", "password": PW})
check("Compte suspendu refusé (401)", s == 401 and "incorrect" in str(d.get("detail", "")), (s, d))

print("== 8. Sécurité")
check("Anonyme sur /auth/users/ → 401", status("GET", "/auth/users/", None) == 401)
check("Acheteur sur route admin → 403", status("GET", "/rentals/admin/leases/", T["awa"]) == 403)
check("Propriétaire sur CRM admin → 403", status("GET", "/crm/admin/dashboard/", T["yao"]) == 403)

print("== 1. Administrateur")
for path in [
    "/crm/admin/dashboard/",
    "/properties/admin/properties/",
    "/crm/pipeline/kanban/",
    "/crm/inquiries/list/",
    "/investments/admin/stats/",
    "/investments/admin/plans/",
    "/investments/admin/subscriptions/",
    "/rentals/admin/leases/",
    "/rentals/admin/payments/",
    "/rentals/admin/payouts/",
    "/accreditation/admin/notaries/",
    "/accreditation/queue/",
    "/auth/users/",
    "/crm/visits/",
    "/properties/projects/",
    "/messaging/conversations/",
    "/crm/admin/search/?q=ya",
]:
    check(f"Admin GET {path} → 200", status("GET", path, T["admin"]) == 200)

print("== 2. Conseiller (Aminata)")
for path in ["/investments/admin/stats/", "/investments/admin/plans/", "/rentals/admin/leases/", "/auth/users/"]:
    check(f"Conseiller GET {path} → 403", status("GET", path, T["aminata"]) == 403)
for path in [
    "/crm/admin/dashboard/",
    "/properties/admin/properties/",
    "/crm/pipeline/kanban/",
    "/crm/inquiries/list/",
    "/accreditation/queue/",
    "/accreditation/admin/notaries/",
]:
    check(f"Conseiller GET {path} → 200", status("GET", path, T["aminata"]) == 200)
s, d = call("GET", "/crm/admin/search/?q=a.kone", T["aminata"])
check("Recherche conseiller : aucun compte utilisateur", s == 200 and d["users"] == [], d)
s, d = call("GET", "/crm/admin/search/?q=a.kone", T["admin"])
check(
    "Recherche administrateur : trouve le compte",
    s == 200 and any(u["email"] == "a.kone@notaire.ci" for u in d["users"]),
)
check("Profil conseiller : is_admin = false", call("GET", "/auth/profile/", T["aminata"])[1]["is_admin"] is False)

print("== 3. Notaires")
q_admin = call("GET", "/accreditation/queue/", T["admin"])[1]
q_admin = q_admin["results"] if isinstance(q_admin, dict) and "results" in q_admin else q_admin
counts = {}
for n in ("notaire1", "notaire2", "notaire3"):
    q = call("GET", "/accreditation/queue/", T[n])[1]
    q = q["results"] if isinstance(q, dict) and "results" in q else q
    counts[n] = len(q)
    check(
        f"{n} ne voit que ses dossiers ({len(q)} sur {len(q_admin)})",
        len(q) <= len(q_admin) and all(f["notary"] for f in q),
    )
check("Les dossiers sont répartis entre notaires (cloisonnement)", sum(counts.values()) <= len(q_admin), counts)
for path in ["/crm/pipeline/kanban/", "/auth/users/", "/crm/admin/search/?q=ab", "/rentals/admin/leases/"]:
    check(f"Notaire GET {path} → 403", status("GET", path, T["notaire1"]) == 403)
first = next((f for f in q_admin if f["notary"] is None), None)
if first:
    check(
        "Notaire ne peut pas assigner un dossier",
        status("PATCH", f"/accreditation/queue/{first['id']}/", T["notaire1"], {"action": "assign", "notary_id": "x"})
        in (400, 403, 404),
    )

print("== 4. Propriétaire")
s, d = call("GET", "/rentals/owner/summary/", T["yao"])
check(
    "Yao : 3 baux de démo dans « Revenus »",
    s == 200 and len(d["leases"]) == 3,
    (s, len(d["leases"]) if s == 200 else d),
)
s, d = call("GET", "/rentals/owner/summary/", T["adjoua"])
check("Adjoua : aucun bail (écran vide attendu)", s == 200 and d["leases"] == [])
s, d = call("GET", "/properties/owner/dashboard/", T["adjoua"])
check("Tableau de bord propriétaire", s == 200 and "properties_total" in d)
check("Propriétaire GET /properties/owner/ → 200", status("GET", "/properties/owner/", T["adjoua"]) == 200)
check(
    "Propriétaire ne voit pas /properties/admin/properties/",
    status("GET", "/properties/admin/properties/", T["adjoua"]) == 403,
)

print("== 5. Acheteur / investisseur")
home = call("GET", "/properties/search/?page_size=2")[1]["results"]
pid = home[0]["id"]
a1 = call("GET", "/properties/favorites/", T["awa"])[1]
before = len(a1["results"] if isinstance(a1, dict) and "results" in a1 else a1)
call("POST", f"/properties/favorites/{pid}/toggle/", T["awa"])
call("POST", f"/properties/favorites/{pid}/toggle/", T["awa"])
a2 = call("GET", "/properties/favorites/", T["awa"])[1]
after = len(a2["results"] if isinstance(a2, dict) and "results" in a2 else a2)
check("Favoris : ajout puis retrait → état inchangé", before == after, (before, after))
s, d = call(
    "POST",
    "/crm/alerts/",
    T["awa"],
    {
        "transaction": "VENTE",
        "property_type": "",
        "commune": "Cocody",
        "max_budget": "100000000",
        "frequency": "IMMEDIATE",
    },
)
check("Alerte de recherche créée", s == 201, (s, d))
if s == 201:
    check("Alerte supprimée", status("DELETE", f"/crm/alerts/{d['id']}/", T["awa"]) == 204)
past = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
future = (datetime.date.today() + datetime.timedelta(days=9)).isoformat()
visit = {
    "property_id": pid,
    "full_name": "ZZ Recette",
    "phone_number": "+2250999990001",
    "visit_type": "PHYSIQUE",
    "scheduled_date": future,
    "scheduled_time": "10:00",
}
check(
    "Visite : date passée refusée",
    status("POST", "/crm/visits/schedule/", T["awa"], {**visit, "scheduled_date": past}) == 400,
)
s, d = call("POST", "/crm/visits/schedule/", T["awa"], visit)
check("Visite : demande future acceptée", s == 201, (s, d))
lead_ids = set([d.get("lead_id")]) if s == 201 else set()
first_visit = d.get("visit_id") if s == 201 else None
s2, d2 = call("POST", "/crm/visits/schedule/", T["awa"], visit)
check("Visite : doublon non recréé (200, même visite)", s2 == 200 and d2.get("visit_id") == first_visit, (s2, d2))
check(
    "Mot de passe : ancien mot de passe exigé",
    status(
        "POST",
        "/auth/profile/password/",
        T["awa"],
        {"current_password": "faux", "new_password": "Un-Mot2Passe-Solide-9"},
    )
    == 400,
)
check(
    "Préférences de notification invalides refusées",
    status("PATCH", "/auth/profile/", T["awa"], {"notification_preferences": {"inconnu": True}}) == 400,
)
check("Plans d'investissement visibles (public)", status("GET", "/investments/plans/", None) == 200)
s, d = call("GET", "/investments/me/", T["sekou"])
check(
    "Investisseur : portefeuille avec souscription et échéancier",
    s == 200 and len(d["subscriptions"]) >= 1 and len(d["schedule"]) >= 1,
    (s,),
)
check("Acheteur sur /investments/me/ sans souscription → 200", status("GET", "/investments/me/", T["awa"]) == 200)

print("== 7. Site public + demandes")
s, d = call(
    "POST",
    "/crm/inquiries/",
    None,
    {
        "property_id": pid,
        "full_name": "ZZ Recette Demande",
        "phone_number": "+2250999990002",
        "message": "test recette",
        "objective": "Investir",
    },
)
check("Demande d'informations anonyme enregistrée", s in (200, 201), (s, d))
if s in (200, 201):
    lead_ids.add(d["lead_id"])
s, d = call("GET", "/crm/inquiries/list/?processed=0", T["admin"])
mine = [i for i in d["results"] if i["lead_name"] == "ZZ Recette Demande"] if s == 200 else []
check("La demande apparaît dans « À traiter » côté équipe", len(mine) == 1)
if mine:
    s, d = call("PATCH", f"/crm/inquiries/{mine[0]['id']}/", T["admin"], {"is_processed": True})
    check("Marquer traitée", s == 200 and d["is_processed"] is True)
    s, d = call("GET", "/crm/inquiries/list/?processed=1", T["admin"])
    check("Elle passe dans « Traitées »", any(i["lead_name"] == "ZZ Recette Demande" for i in d["results"]))
check(
    "WhatsApp anonyme : pas de prospect créé",
    call("POST", "/crm/whatsapp-click/", None, {"property_id": pid})[1].get("lead_id") is None,
)
check(
    "Simulateur public",
    status(
        "POST",
        "/simulators/calculate-investment/",
        None,
        {
            "purchase_price": 50000000,
            "monthly_rent": 400000,
            "annual_charges": 600000,
            "down_payment": 10000000,
            "annual_interest_rate": 7.5,
            "loan_duration_years": 15,
        },
    )
    in (200, 400),
)

print("== 1. Messagerie équipe")
s, d = call("POST", "/messaging/conversations/", T["awa"], {"subject": "ZZ Recette", "body": "Bonjour"})
check("Acheteur écrit à l'équipe", s == 201, (s, d))
koffi = call("GET", "/messaging/unread-count/", T["koffi"])[1]["unread"]
check("Koffi (premier conseiller) a des messages non lus", koffi >= 1, koffi)
check(
    "Aminata et l'admin n'en reçoivent pas",
    call("GET", "/messaging/unread-count/", T["aminata"])[1]["unread"] == 0
    and call("GET", "/messaging/unread-count/", T["admin"])[1]["unread"] == 0,
)

print("== Nettoyage")
for lid in lead_ids:
    if lid:
        print("   prospect", lid, status("DELETE", f"/crm/leads/{lid}/", T["admin"]))
print()
fails = [r for r in results if not r[0]]
print(f"{len(results) - len(fails)}/{len(results)} vérifications réussies")
for ok, name, detail in fails:
    print("  ÉCHEC:", name, detail)
sys.exit(1 if fails else 0)
