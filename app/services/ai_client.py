from typing import Protocol

from app.schemas import AnalyseIA, Categorie, Urgence


class AIProvider(Protocol):
    def analyser(self, message: str) -> AnalyseIA: ...


class FakeProvider:
    """Fournisseur factice : aucune IA, réponses instantanées.
    Sert aux tests et à la démo sans Ollama (AI_PROVIDER=fake)."""

    def analyser(self, message: str) -> AnalyseIA:
        texte = message.lower()

        if "fum" in texte:
            urgence = Urgence.CRITIQUE
            categorie = Categorie.BATTERIE
        else:
            urgence = Urgence.NORMALE
            categorie = Categorie.AUTRE

        return AnalyseIA(
            resume=message[:100],
            justification="Analyse simulée (mode fake).",
            categorie=categorie,
            urgence=urgence,
            atelier_suggere=None,
            confiance=0.5,
        )