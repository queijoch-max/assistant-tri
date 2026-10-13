import pytest

from app.schemas import Categorie, CodeAtelier
from app.services.triage import detecter_alerte, masquer_cartes, normaliser, router


def test_normaliser_retire_accents_et_majuscules():
    assert normaliser("FUMÉE Brûlée") == "fumee brulee"


@pytest.mark.parametrize(
    "message",
    [
        "Bonjour, une odeur de plastique brûlé près de la batterie.",
        "ma batri fume kan je la charge",
        "Mes freins ne répondent plus !",
        "Je suis tombée à cause du guidon.",
        "La batterie CHAUFFE énormément.",
    ],
)
def test_alerte_detectee(message):
    assert detecter_alerte(message) is not None


@pytest.mark.parametrize(
    "message",
    [
        "Quels sont vos horaires le samedi ?",
        "Mon feu arrière ne s'allume plus.",  # "feu" = éclairage, pas incendie
        "Le vélo sent bon, il est parfumé !",  # "fume" dans "parfumé"
        "Mon vélo tombe souvent en panne.",  # "tombe" sans chute
    ],
)
def test_pas_de_fausse_alerte(message):
    assert detecter_alerte(message) is None


def test_carte_masquee():
    texte = masquer_cartes("Voici ma carte : 4970 1234 5678 9012, merci.")
    assert "4970" not in texte
    assert "[CARTE MASQUÉE]" in texte


def test_numero_de_commande_non_masque():
    assert masquer_cartes("Ma commande n°62341") == "Ma commande n°62341"


def test_routage_sans_atelier_va_au_siege():
    assert router(None, Categorie.AUTRE) == CodeAtelier.LYON1


def test_routage_reparation_dans_atelier_vente_seule():
    assert router(CodeAtelier.LYON2, Categorie.PANNE) == CodeAtelier.LYON1
    assert router(CodeAtelier.LYON7, Categorie.BATTERIE) == CodeAtelier.LYON8


def test_routage_achat_dans_atelier_vente_reste_sur_place():
    assert router(CodeAtelier.LYON2, Categorie.AVANT_ACHAT) == CodeAtelier.LYON2