from app.schemas import AnalyseIA, Categorie, CodeAtelier, Urgence
from app.services.ai_client import FakeProvider
from app.services.triage import trier


class IAQuiEchoue:
    """Faux fournisseur qui plante toujours (Ollama éteint, JSON invalide...)."""

    def __init__(self) -> None:
        self.appels = 0

    def analyser(self, message: str) -> AnalyseIA:
        self.appels += 1
        raise ConnectionError("Ollama injoignable")


class IAQuiNote:
    """Faux fournisseur qui renvoie une réponse fixée et mémorise ce qu'il reçoit."""

    def __init__(self, urgence: Urgence) -> None:
        self.urgence = urgence
        self.message_recu = ""

    def analyser(self, message: str) -> AnalyseIA:
        self.message_recu = message
        return AnalyseIA(
            resume="Résumé.",
            justification="Justification.",
            categorie=Categorie.PANNE,
            urgence=self.urgence,
            atelier_suggere=None,
            confiance=0.9,
        )


def test_mot_cle_force_critique_meme_si_ia_dit_basse():
    resultat = trier("Mes freins ne répondent plus", IAQuiNote(Urgence.BASSE))
    assert resultat.urgence == Urgence.CRITIQUE
    assert resultat.alerte == "freins ne repondent"


def test_carte_masquee_avant_envoi_a_l_ia():
    ia = IAQuiNote(Urgence.NORMALE)
    trier("Remboursez-moi sur la carte 4970 1234 5678 9012", ia)
    assert "4970" not in ia.message_recu


def test_ia_en_panne_mode_degrade_avec_une_nouvelle_tentative():
    ia = IAQuiEchoue()
    resultat = trier("Bonjour, quels sont vos horaires ?", ia)
    assert ia.appels == 2  # une tentative + une nouvelle tentative
    assert resultat.analyse is None
    assert resultat.a_verifier is True
    assert resultat.erreur_ia is not None
    assert resultat.atelier_destination == CodeAtelier.LYON1


def test_ia_en_panne_mais_alerte_detectee_reste_critique():
    resultat = trier("Ma batterie fume !", IAQuiEchoue())
    assert resultat.urgence == Urgence.CRITIQUE


def test_confiance_faible_a_verifier():
    resultat = trier("Bonjour, une question.", FakeProvider())  # confiance 0.5
    assert resultat.a_verifier is True
