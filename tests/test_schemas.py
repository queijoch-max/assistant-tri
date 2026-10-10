import pytest
from pydantic import ValidationError

from app.schemas import AnalyseIA, DemandeCreate

# Une analyse correcte, réutilisée par tous les tests.
ANALYSE_VALIDE = {
    "resume": "La batterie du client dégage de la fumée pendant la charge.",
    "justification": "Mention de fumée : risque d'incendie.",
    "categorie": "batterie",
    "urgence": "critique",
    "atelier_suggere": None,
    "confiance": 0.9,
}


def test_analyse_valide():
    analyse = AnalyseIA(**ANALYSE_VALIDE)
    assert analyse.urgence == "critique"


def test_categorie_inconnue_refusee():
    with pytest.raises(ValidationError):
        AnalyseIA(**{**ANALYSE_VALIDE, "categorie": "vélo"})


def test_confiance_hors_limites():
    with pytest.raises(ValidationError):
        AnalyseIA(**{**ANALYSE_VALIDE, "confiance": 1.5})


def test_message_trop_long_refuse():
    with pytest.raises(ValidationError):
        DemandeCreate(
            nom="Jean Dupont",
            email="jean@dupont.fr",
            message="a" * 6000,
        )
