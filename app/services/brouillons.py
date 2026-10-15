import re

from app.schemas import Brouillon, CodeAtelier, ResultatTriage, Urgence
from app.services.ai_client import AIProvider
from app.services.triage import masquer_cartes, normaliser

SIGNATURE = "Le SAV Cycles Mistral"
MOTS_MAX = 120  # cahier des charges, pour le brouillon complet
MOTS_ACCROCHE_MAX = 50  # au-delà, la phrase de l'IA est écartée

# Ajoutée par le code, jamais laissée au bon vouloir de l'IA.
CONSIGNE_SECURITE = (
    "Par sécurité, n'utilisez plus votre vélo en attendant notre retour. "
    "S'il s'agit de la batterie, débranchez-la et éloignez-la de tout objet "
    "inflammable."
)

ACCROCHE_DE_SECOURS = (
    "Nous vous remercions pour votre message et avons bien pris en compte "
    "votre demande."
)

NOMS_ATELIERS = {
    CodeAtelier.LYON1: "des Terreaux",
    CodeAtelier.LYON2: "de Perrache",
    CodeAtelier.LYON3: "de la Part-Dieu",
    CodeAtelier.LYON5: "de Fourvière",
    CodeAtelier.LYON7: "de Gerland",
    CodeAtelier.LYON8: "de Montplaisir",
}

# Racines sans accents : "rembours" couvre rembourser, remboursement...
PROMESSES_A_VERIFIER = (
    "rembours",
    "geste commercial",
    "gratuit",
    "offert",
    "sous 24",
    "sous 48",
)


def nettoyer_accroche(texte: str) -> str:
    """Retire la mise en forme et le bavardage que les petits modèles ajoutent."""
    texte = re.sub(r"[*#_`]", "", texte)  # gras, titres, code
    texte = re.sub(r"^\s*(réponse|phrase)\s*:\s*", "", texte, flags=re.IGNORECASE)
    texte = " ".join(texte.split())  # une seule ligne, espaces simples
    return texte.strip(" \"'«»")


def phrase_de_suivi(triage: ResultatTriage) -> str:
    """Phrase finale écrite par le code : l'atelier vient du routage."""
    atelier = NOMS_ATELIERS[triage.atelier_destination]
    if triage.urgence == Urgence.CRITIQUE:
        return f"Un conseiller de notre atelier {atelier} vous recontacte en priorité."
    return f"Un conseiller de notre atelier {atelier} revient vers vous rapidement."


def assembler_brouillon(accroche: str, triage: ResultatTriage) -> str:
    """Construit le brouillon complet autour de la phrase de l'IA."""
    paragraphes = ["Bonjour,", accroche]
    if triage.urgence == Urgence.CRITIQUE:
        paragraphes.append(CONSIGNE_SECURITE)
    paragraphes += [phrase_de_suivi(triage), SIGNATURE]
    return "\n\n".join(paragraphes)


def verifier_brouillon(texte: str) -> list[str]:
    """Liste les points que l'agent doit vérifier avant d'envoyer le brouillon."""
    alertes = []
    nb_mots = len(texte.split())
    if nb_mots > MOTS_MAX:
        alertes.append(f"Trop long : {nb_mots} mots (maximum {MOTS_MAX})")
    if not texte.rstrip().endswith(SIGNATURE):
        alertes.append("Le brouillon ne se termine pas par la signature")
    texte_normalise = normaliser(texte)
    for promesse in PROMESSES_A_VERIFIER:
        if promesse in texte_normalise:
            alertes.append(f"Promesse à vérifier : « {promesse} »")
    return alertes


def generer_brouillon(
    message: str, triage: ResultatTriage, provider: AIProvider
) -> Brouillon:
    """Fait écrire une phrase personnalisée par l'IA et construit le brouillon.

    Ne lève jamais d'exception : en cas de problème avec l'IA, on utilise une
    phrase générique et on prévient l'agent.
    """
    alertes = []
    try:
        accroche = nettoyer_accroche(provider.rediger_accroche(masquer_cartes(message)))
    # Volontairement large : l'agent doit toujours obtenir un brouillon.
    except Exception as exc:  # noqa: BLE001
        accroche = ""
        alertes.append(f"IA indisponible ({type(exc).__name__}) : phrase générique")

    nb_mots = len(accroche.split())
    if nb_mots > MOTS_ACCROCHE_MAX:
        alertes.append(f"Phrase de l'IA écartée ({nb_mots} mots) : phrase générique")
    if not accroche or nb_mots > MOTS_ACCROCHE_MAX:
        accroche = ACCROCHE_DE_SECOURS

    texte = assembler_brouillon(accroche, triage)
    return Brouillon(texte=texte, alertes=alertes + verifier_brouillon(texte))
