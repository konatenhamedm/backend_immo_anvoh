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
    """

    @staticmethod
    def calculate_score(
        has_confirmed_budget: bool,
        has_confirmed_down_payment: bool,
        timeframe_under_3_months: bool,
        has_identified_property: bool,
        has_visit_request: bool,
        has_recent_interaction: bool = True
    ) -> Tuple[int, str]:
        score = 0
        if has_confirmed_budget:
            score += 20
        if has_confirmed_down_payment:
            score += 20
        if timeframe_under_3_months:
            score += 20
        if has_identified_property:
            score += 15
        if has_visit_request:
            score += 15
        if has_recent_interaction:
            score += 10

        # Plafond à 100
        score = min(score, 100)

        # Détermination de la température commerciale
        if score >= 90:
            temperature = "TRES_CHAUD" # 90-100 : Très chaud
        elif score >= 70:
            temperature = "CHAUD"      # 70-89 : Chaud
        elif score >= 40:
            temperature = "TIEDE"      # 40-69 : Tiède
        else:
            temperature = "FROID"      # 0-39 : Froid

        return score, temperature
