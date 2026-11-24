from typing import Tuple


class LeadScoringDomainService:
    """
    Règles métier pures de scoring automatique pour THIEBBRO IMMO (Écran 27).
    Pondérations :
    - Budget confirmé : +20
    - Apport confirmé : +20
    - Délai < 3 mois : +20
    - Bien identifié : +15
    - Demande de visite : +15
    - Réponse / interaction récente : +10
    Ces valeurs sont les défauts ; l'administrateur les modifie (CRMSettings) et `calculate_score(..., rules=)` les reçoit.
    """

    DEFAULT_RULES = {
        "budget": 20,
        "down_payment": 20,
        "timeframe": 20,
        "property": 15,
        "visit": 15,
        "interaction": 10,
        "tiede": 40,
        "chaud": 70,
        "tres_chaud": 90,
    }

    @staticmethod
    def calculate_score(
        has_confirmed_budget: bool,
        has_confirmed_down_payment: bool,
        timeframe_under_3_months: bool,
        has_identified_property: bool,
        has_visit_request: bool,
        has_recent_interaction: bool = True,
        rules: dict | None = None,
    ) -> Tuple[int, str]:
        r = {**LeadScoringDomainService.DEFAULT_RULES, **(rules or {})}
        score = 0
        if has_confirmed_budget:
            score += r["budget"]
        if has_confirmed_down_payment:
            score += r["down_payment"]
        if timeframe_under_3_months:
            score += r["timeframe"]
        if has_identified_property:
            score += r["property"]
        if has_visit_request:
            score += r["visit"]
        if has_recent_interaction:
            score += r["interaction"]

        # Plafond à 100
        score = min(score, 100)

        # Détermination de la température commerciale
        if score >= r["tres_chaud"]:
            temperature = "TRES_CHAUD"  # 90-100 : Très chaud
        elif score >= r["chaud"]:
            temperature = "CHAUD"  # 70-89 : Chaud
        elif score >= r["tiede"]:
            temperature = "TIEDE"  # 40-69 : Tiède
        else:
            temperature = "FROID"  # 0-39 : Froid

        return score, temperature
