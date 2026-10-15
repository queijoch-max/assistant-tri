from app.schemas import AnalyseIA, Categorie, CodeAtelier, ResultatTriage, Urgence
from app.services.brouillons import (
    ACCROCHE_DE_SECOURS,
    CONSIGNE_SECURITE,
    SIGNATURE,
    generer_brouillon,
    nettoyer_accroche,
    verifier_brouillon,
)

ACCROCHE = "Nous comprenons votre inquiétude au sujet de votre batterie."


def _triage(
    urgence: Urgence, atelier: CodeAtelier = CodeAtelier.LYON1
) -> ResultatTriage:
    return ResultatTriage(
        analyse=None,
        categorie=Categorie.BATTERIE,
        urgence=urgence,
        atelier_destination=atelier,
        alerte=None,
        a_verifier=False,
    )


class IARedactrice:
    """Faux fournisseur qui renvoie une phrase fixée et mémorise le message reçu."""

    def __init__(self, phrase: str = ACCROCHE) -> None:
        self.phrase = phrase
        self.message_recu = ""

    def analyser(self, message: str) -> AnalyseIA:
        raise NotImplementedError

    def rediger_accroche(self, message: str) -> str:
        self.message_recu = message
        return self.phrase


class IAEnPanne:
    def analyser(self, message: str) -> AnalyseIA:
        raise ConnectionError("Ollama injoignable")

    def rediger_accroche(self, message: str) -> str:
        raise ConnectionError("Ollama injoignable")


# --- Nettoyage de la phrase de l'IA -------------------------------------------


def test_nettoyage_retire_gras_prefixe_et_guillemets():
    assert nettoyer_accroche("**Réponse :** « Merci. »") == "Merci."


def test_nettoyage_met_sur_une_seule_ligne():
    assert (
        nettoyer_accroche("Merci.\n\nNous   comprenons.") == "Merci. Nous comprenons."
    )


# --- Vérifications -----------------------------------------------------------


def test_signature_doit_terminer_le_brouillon():
    texte = "Bonjour,\n\nLe SAV Cycles Mistral n'est pas en mesure de vous aider."
    assert any("signature" in a for a in verifier_brouillon(texte))


def test_promesse_de_remboursement_signalee():
    alertes = verifier_brouillon(f"Nous allons vous REMBOURSER.\n\n{SIGNATURE}")
    assert any("rembours" in a for a in alertes)


# --- Brouillon complet -------------------------------------------------------


def test_brouillon_structure_garantie():
    brouillon = generer_brouillon(
        "Une question", _triage(Urgence.NORMALE), IARedactrice()
    )
    assert brouillon.texte.startswith("Bonjour,")
    assert brouillon.texte.endswith(SIGNATURE)
    assert ACCROCHE in brouillon.texte
    assert brouillon.alertes == []


def test_consigne_securite_seulement_si_critique():
    critique = generer_brouillon("x", _triage(Urgence.CRITIQUE), IARedactrice())
    normale = generer_brouillon("x", _triage(Urgence.NORMALE), IARedactrice())
    assert CONSIGNE_SECURITE in critique.texte
    assert CONSIGNE_SECURITE not in normale.texte


def test_atelier_de_destination_cite():
    triage = _triage(Urgence.NORMALE, CodeAtelier.LYON8)
    brouillon = generer_brouillon("x", triage, IARedactrice())
    assert "Montplaisir" in brouillon.texte


def test_phrase_trop_longue_remplacee():
    bavarde = IARedactrice("bla " * 80)
    brouillon = generer_brouillon("x", _triage(Urgence.NORMALE), bavarde)
    assert ACCROCHE_DE_SECOURS in brouillon.texte
    assert any("écartée" in a for a in brouillon.alertes)


def test_carte_masquee_avant_envoi_a_l_ia():
    ia = IARedactrice()
    generer_brouillon("Ma carte 4970 1234 5678 9012", _triage(Urgence.NORMALE), ia)
    assert "4970" not in ia.message_recu


def test_ia_en_panne_brouillon_complet_quand_meme():
    brouillon = generer_brouillon("Bonjour", _triage(Urgence.NORMALE), IAEnPanne())
    assert ACCROCHE_DE_SECOURS in brouillon.texte
    assert brouillon.texte.endswith(SIGNATURE)
    assert any("IA indisponible" in a for a in brouillon.alertes)


def test_consigne_securite_apres_la_phrase_de_l_ia():
    texte = generer_brouillon("x", _triage(Urgence.CRITIQUE), IARedactrice()).texte
    assert texte.index(ACCROCHE) < texte.index(CONSIGNE_SECURITE)
