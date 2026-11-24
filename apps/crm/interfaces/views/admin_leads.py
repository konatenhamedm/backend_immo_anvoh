"""Back-office : prospects (kanban, fiche, notes, création).

═══════════════════════════════════════════════════════════════════════════════════════════════════
GUIDE DE LECTURE — ce fichier est le modèle de référence pour comprendre tous les contrôleurs.
═══════════════════════════════════════════════════════════════════════════════════════════════════

1. LE CHEMIN D'UNE REQUÊTE (comparé à Symfony)
   ------------------------------------------------------------------------------------------------
   urls.py                 → routes.yaml / attributs #[Route]        (quelle URL appelle quelle vue)
   cette vue (View)        → Controller                              (reçoit la requête, orchestre)
   Serializer              → DTO + Validator + Normalizer            (valide l'entrée, formate la sortie)
   Model (infrastructure/) → Entity Doctrine                         (une table SQL)
   domain/*.py             → Service métier / Domain service         (règles métier pures, sans HTTP)
   permission_classes      → #[IsGranted] / Voter                    (qui a le droit d'appeler)

2. D'OÙ VIENNENT LES FONCTIONS UTILISÉES ICI ?
   ------------------------------------------------------------------------------------------------
   NATIF DRF (Django REST Framework — la librairie d'API) :
     APIView                           contrôleur de base : on écrit get(), post()… à la main
     generics.RetrieveUpdateDestroyAPIView
                                       contrôleur « tout fait » : GET + PUT/PATCH + DELETE sur UNE ressource
                                       (≈ opérations Item d'API Platform). On ne code que ce qui change.
     Response, status                  ≈ JsonResponse + codes HTTP (201 Created, 400 Bad Request…)
     serializer.is_valid(raise_exception=True)
                                       valide l'entrée ; si invalide, renvoie tout seul une réponse 400
     serializer.validated_data         les données validées et nettoyées (≈ le DTO rempli)
     serializer.save()                 ENREGISTRE : appelle create() ou update() du serializer, qui écrit en base
     perform_update(serializer)        « crochet » appelé par RetrieveUpdate… juste avant d'enregistrer
     get_serializer_class()            permet de choisir le serializer selon la requête
     request.data / request.query_params / request.user
                                       corps JSON / paramètres ?a=b de l'URL / utilisateur connecté (JWT)

   NATIF DJANGO (l'ORM — ≈ Doctrine) :
     Lead.objects                      le « repository » du modèle Lead
     .filter(...) .order_by(...)       WHERE / ORDER BY ; chaînables ; ne s'exécutent qu'à la lecture (lazy)
     .select_related("x")              JOIN + charge la relation x dans la même requête (évite le « N+1 »)
     .prefetch_related("y")            une 2e requête groupée pour les relations « à plusieurs » (y)
     .values("stage").annotate(n=Count("id"))
                                       GROUP BY stage + COUNT(id)  (≈ QueryBuilder groupBy)
     .first()                          le premier résultat ou None  (≈ findOneBy)
     get_object_or_404(Lead, id=id)    retrouve OU renvoie une 404 (≈ throw NotFoundHttpException)
     Lead.objects.create(...)          INSERT immédiat (≈ new Entity + persist + flush)
     lead.save()                       INSERT ou UPDATE de TOUTES les colonnes (≈ persist + flush)
     lead.save(update_fields=[...])    UPDATE seulement des colonnes listées (plus rapide, plus sûr)
     get_xxx_display()                 Django génère get_stage_display() : renvoie le LIBELLÉ d'un champ à choix
     PipelineStage.choices             liste (code, libellé) de l'énumération (≈ un enum PHP avec labels)

   SPÉCIFIQUE À CE PROJET (à lire dans apps/…) :
     IsStaffOrAgent                    apps/users/interfaces/permissions.py — administrateurs et conseillers
     find_or_create_lead / advance_stage / rescore
                                       apps/crm/domain/lead_service.py — règles métier des prospects
     LeadKanbanItemSerializer…         apps/crm/interfaces/serializers.py — formats d'entrée / sortie
     KanbanSchema                      apps/crm/interfaces/schemas.py — décrit la réponse dans la doc OpenAPI

3. À RETENIR SUR « ENREGISTRER »
   ------------------------------------------------------------------------------------------------
   Il y a TROIS façons d'écrire en base dans ce fichier :
     serializer.save()               quand une requête MODIFIE un objet (DRF applique les champs reçus)
     Model.objects.create(...)       pour INSÉRER une ligne directement (historique d'interactions)
     lead.save() / lead.save(update_fields=[...])
                                     après avoir modifié l'objet en mémoire (score, étape, conseiller…)
   Modifier un attribut (lead.stage = "RDV") ne touche PAS la base : c'est save() qui écrit.

4. À RETENIR SUR LES COMMENTAIRES
   ------------------------------------------------------------------------------------------------
   Volontairement en `#` et non en docstring : drf-spectacular recopie les docstrings des vues dans la
   documentation OpenAPI publique (/api/docs/).
"""

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import advance_stage, find_or_create_lead, rescore
from apps.crm.infrastructure.models import (
    CRMInteraction,
    Lead,
    PipelineStage,
)
from apps.properties.infrastructure.models import Property
from apps.users.interfaces.permissions import IsStaffOrAgent

from ..schemas import KanbanSchema
from ..serializers import (
    CRMInteractionSerializer,
    LeadCreateSerializer,
    LeadDetailSerializer,
    LeadKanbanItemSerializer,
    LeadNoteSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────────────────────────
# 1) KANBAN — GET /api/v1/crm/pipeline/kanban/            (lecture seule, tout le pipeline en 1 appel)
# ─────────────────────────────────────────────────────────────────────────────────────────────────
# @extend_schema : annotation OpenAPI (≈ #[OA\Get(...)]). Elle ne change rien à l'exécution : elle
#   décrit l'endpoint dans /api/docs/ (tag, résumé, forme de la réponse).
@extend_schema(
    tags=["Back-office CRM"],
    summary="Écran 26 : Pipeline Kanban (?agent=me, 50 leads par colonne)",
    responses={200: KanbanSchema},
)
class PipelineKanbanView(APIView):
    # Seuls les administrateurs et conseillers passent ; les autres reçoivent 403 avant même d'entrer dans get().
    permission_classes = [IsStaffOrAgent]

    # APIView : une méthode par verbe HTTP. Ici seul GET existe → POST/PUT/DELETE renvoient 405.
    def get(self, request):
        # Requête de base (rien n'est exécuté ici, c'est une requête « en préparation »).
        # select_related : charge le bien consulté et le conseiller avec le prospect (1 JOIN, pas 1 requête/prospect).
        base = Lead.objects.select_related("consulted_property", "assigned_agent")
        # ?agent=me dans l'URL → ne garder que les prospects assignés à l'utilisateur connecté.
        if request.query_params.get("agent") == "me":
            base = base.filter(assigned_agent=request.user)
        # Deux agrégats SQL (GROUP BY stage) pour avoir le TOTAL réel de chaque colonne, même au-delà de 50 cartes.
        #   {"NOUVEAU": 2, "CONTACTE": 1, …}   et   {"NOUVEAU": Decimal("65000000"), …}
        counts = dict(base.values("stage").annotate(n=Count("id")).values_list("stage", "n"))
        budgets = dict(base.values("stage").annotate(t=Sum("budget")).values_list("stage", "t"))
        kanban = {}
        # PipelineStage.choices = [("NOUVEAU", "Nouveau"), ("CONTACTE", "Contacté"), …] dans l'ordre du pipeline.
        for key, label in PipelineStage.choices:
            # Les 50 prospects les plus « chauds » de l'étape : score décroissant, puis activité la plus récente.
            # ("-score" = ORDER BY score DESC ; [:50] = LIMIT 50)
            leads = base.filter(stage=key).order_by("-score", "-last_interaction_at")[:50]
            kanban[key] = {
                "label": label,
                "count": counts.get(key, 0),
                "budget_total": budgets.get(key) or 0,
                # many=True : le serializer transforme une LISTE d'objets en liste de dictionnaires (JSON-able).
                # .data = le résultat prêt pour Response (≈ $serializer->normalize()).
                "leads": LeadKanbanItemSerializer(leads, many=True).data,
            }
        return Response(kanban)


# ─────────────────────────────────────────────────────────────────────────────────────────────────
# 2) FICHE PROSPECT — GET / PUT / PATCH / DELETE /api/v1/crm/leads/<uuid>/
#    C'est le CRUD « complet » : presque tout est fait par la classe parente de DRF.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
@extend_schema(tags=["Back-office CRM"], summary="Fiche prospect : consulter, changer d'étape, assigner, noter")
class LeadDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    # RetrieveUpdateDestroyAPIView fournit, sans une ligne de code :
    #   GET    → retrouve le prospect (get_object) puis le sérialise            (Read)
    #   PUT    → remplace tous les champs     |  PATCH → modifie seulement ceux reçus   (Update)
    #   DELETE → supprime le prospect (et, en cascade, son historique, ses visites…)    (Delete)
    # Ici on ne configure que : qui peut appeler, quelle requête de base, et quel serializer.
    permission_classes = [IsStaffOrAgent]

    # Requête de base utilisée pour retrouver l'objet. Les « …related » chargent d'avance tout ce que la fiche
    # affiche (historique, visites, demandes + leurs biens et photos) : quelques requêtes au lieu de dizaines.
    queryset = Lead.objects.select_related("consulted_property", "assigned_agent").prefetch_related(
        "interactions", "visits__property__images", "inquiries__property__images"
    )
    # Nom du paramètre d'URL qui identifie l'objet (<uuid:id> dans urls.py). Par défaut DRF attend « pk ».
    lookup_field = "id"

    # Choix du serializer selon le verbe : lecture riche (avec historique) / écriture plus légère.
    def get_serializer_class(self):
        return LeadDetailSerializer if self.request.method == "GET" else LeadKanbanItemSerializer

    # CROCHET (hook) appelé par PUT/PATCH APRÈS validation des données reçues et AVANT la réponse.
    # Par défaut il ne fait que « serializer.save() ». On l'étend pour ajouter notre logique métier.
    def perform_update(self, serializer):
        # À ce stade l'objet est encore dans son état D'AVANT : on mémorise l'ancienne étape.
        before = serializer.instance.stage
        # ENREGISTRE les champs reçus en base (UPDATE) et renvoie l'objet à jour.
        lead = serializer.save()
        # Si l'étape a changé, on trace le changement dans l'historique du prospect (INSERT d'une ligne).
        if lead.stage != before:
            CRMInteraction.objects.create(
                lead=lead,
                interaction_type="STAGE_CHANGE",
                # PipelineStage(before) : transforme le code "RDV" en élément d'énumération → .label = "RDV fixé".
                # get_stage_display() : généré par Django, libellé de l'étape actuelle.
                details=f"Étape : {PipelineStage(before).label} → {lead.get_stage_display()} (par {self.request.user.first_name or self.request.user.email})",
            )
        # Recalcule le score et la température À PARTIR des données maintenant à jour (voir lead_service.rescore).
        # Attention : rescore() modifie l'objet EN MÉMOIRE uniquement, il n'écrit rien en base.
        rescore(lead)
        # Écrit en base seulement ces 3 colonnes. « last_interaction_at » est déclaré auto_now=True dans le modèle :
        # Django ne le met à jour que s'il est cité ici → c'est ce qui « touche » la date de dernière interaction.
        lead.save(update_fields=["score", "temperature", "last_interaction_at"])


# ─────────────────────────────────────────────────────────────────────────────────────────────────
# 3) NOTE / APPEL — POST /api/v1/crm/leads/<uuid>/notes/
#    Action unique « ajouter une ligne à l'historique » : on écrit donc un APIView avec post() à la main.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
@extend_schema(
    tags=["Back-office CRM"],
    summary="Ajouter une note / un appel à l'historique du prospect",
    request=LeadNoteSerializer,
    responses={201: CRMInteractionSerializer},
)
class LeadNoteView(APIView):
    permission_classes = [IsStaffOrAgent]

    # Le paramètre « id » arrive de l'URL (<uuid:id>) : c'est l'équivalent d'un argument de route Symfony.
    def post(self, request, id):
        # Retrouve le prospect ou répond directement 404 (la fonction « lève » la réponse, le code ne continue pas).
        lead = get_object_or_404(Lead, id=id)
        # request.data = le corps JSON reçu. On le passe au serializer pour le VALIDER (types, longueurs, choix…).
        serializer = LeadNoteSerializer(data=request.data)
        # Si invalide : lève une erreur que DRF transforme en réponse 400 détaillée (champ par champ).
        serializer.is_valid(raise_exception=True)
        # validated_data = {"interaction_type": "CALL", "details": "…"} ; « ** » le déplie en arguments nommés :
        # équivaut à create(lead=lead, interaction_type="CALL", details="…"). INSERT immédiat.
        interaction = CRMInteraction.objects.create(lead=lead, **serializer.validated_data)
        # « Touche » la date de dernière interaction du prospect (auto_now, voir plus haut) sans rien modifier d'autre.
        lead.save(update_fields=["last_interaction_at"])
        # 201 Created + la ligne créée, mise en forme par le serializer de sortie.
        return Response(CRMInteractionSerializer(interaction).data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────────────────────────
# 4) CRÉATION MANUELLE — POST /api/v1/crm/leads/
#    Saisie d'un prospect par l'équipe (salon, appel, recommandation). Dédoublonnée par téléphone.
#    Illustre l'enchaînement complet : valider → retrouver/créer → faire évoluer → noter → enregistrer.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
@extend_schema(
    tags=["Back-office CRM"],
    request=LeadCreateSerializer,
    responses={201: LeadKanbanItemSerializer},
    summary="Ajouter un prospect au pipeline (dédoublonné par téléphone)",
)
class LeadCreateAdminView(APIView):
    permission_classes = [IsStaffOrAgent]

    def post(self, request):
        # 1. VALIDATION de l'entrée (LeadCreateSerializer : champs requis, formats, choix autorisés, valeurs par défaut).
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # « d » = dictionnaire des données validées et nettoyées (ex. d["stage"], d["budget"]…).
        d = serializer.validated_data
        # 2. Bien consulté (facultatif). .filter(...).first() renvoie l'objet OU None (pas d'erreur s'il n'existe pas,
        #    contrairement à .get()). L'identifiant est une UUID reçue du formulaire.
        prop = Property.objects.filter(id=d["consulted_property"]).first() if d.get("consulted_property") else None
        # 3. RETROUVER OU CRÉER le prospect (règle métier, voir lead_service.find_or_create_lead) :
        #    - le téléphone est normalisé ("07 07 07 07 07" → "+2250707070707") puis cherché en base ;
        #    - s'il existe : on le COMPLÈTE sans écraser ce que l'équipe a déjà saisi (pas de doublon) ;
        #    - sinon : on crée un nouvel objet Lead ;
        #    - dans tous les cas la fonction fait déjà un lead.save() et renvoie le prospect.
        #    « extra » = champs supplémentaires à poser seulement s'ils sont renseignés (budget, notes).
        lead = find_or_create_lead(
            phone=d["phone_number"],
            full_name=d["full_name"],
            email=d.get("email", ""),
            source=d["source"],
            prop=prop,
            extra={"budget": d.get("budget"), "commercial_notes": d.get("commercial_notes", "")},
            attribution={"channel": d["acquisition_channel"]},
        )
        # Renvoie None quand aucun téléphone exploitable n'est fourni : impossible d'identifier la personne.
        if lead is None:
            return Response({"detail": "Numéro de téléphone requis."}, status=status.HTTP_400_BAD_REQUEST)
        # 4. Les modifications ci-dessous se font EN MÉMOIRE sur l'objet ; rien n'est écrit tant qu'on n'appelle pas save().
        if d["assign_to_me"]:
            # request.user = l'utilisateur authentifié par le jeton JWT (un objet User, ≈ $this->getUser()).
            lead.assigned_agent = request.user
        # Fait avancer le prospect à l'étape demandée, jamais en arrière (sauf « Perdu ») : voir advance_stage.
        advance_stage(lead, d["stage"])
        # Recalcule score + température d'après ce que l'on sait maintenant : voir rescore.
        rescore(lead)
        # ENREGISTRE toutes les modifications en mémoire (agent, étape, score) en un seul UPDATE.
        lead.save()
        # 5. Trace d'audit dans l'historique du prospect (INSERT).
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="MANUAL_ENTRY",
            details=f"Prospect saisi par {request.user.first_name or request.user.email} ({lead.get_source_display()})",
        )
        # 6. 201 Created + le prospect au format « carte kanban ».
        return Response(LeadKanbanItemSerializer(lead).data, status=status.HTTP_201_CREATED)
