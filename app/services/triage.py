import re
import unicodedata

from app.schemas import Categorie, CodeAtelier, ResultatTriage, Urgence
from app.services.ai_client import AIProvider

# Mots-clés d'alerte du cadrage (section 9), écrits SANS accents ni majuscules :
# le message est normalisé de la même façon avant la recherche.
MOTS_ALERTE = (
    # Feu / chaleur
    "fumee",
    "fume",
    "fumait",
    "brule",
    "brulant",
    "chauffe",
    "surchauffe",
    "etincelle",
    "flamme",
    "en feu",
    "pris feu",
    "prend feu",
    "incendie",
    "fondu",
    # Batterie dangereuse
    "batterie gonflee",
    "batterie deformee",
    "court-circuit",
    "explose",
    "explosion",
    # Freins
    "plus de frein",
    "freins lachent",
    "freine plus",
    "freinent plus",
    "freins ne repondent",
    "freins hs",
    # Accident
    "accident",
    "chute",
    "suis tombe",
    "suis tombee",
    "blesse",
    "blessure",
    "hopital",
)

# Un mot-clé ne compte que s'il forme un mot entier : "fume" ne doit pas
# se déclencher dans "parfumé".
_REGEX_ALERTE = re.compile(r"\b(" + "|".join(map(re.escape, MOTS_ALERTE)) + r")\b")

# 16 chiffres, éventuellement groupés par 4 avec des espaces ou des tirets.
_REGEX_CARTE = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

# Règle de routage n°2 : un atelier « vente seule » renvoie les réparations
# vers l'atelier de réparation le plus proche.
REDIRECTION_REPARATION = {
    CodeAtelier.LYON2: CodeAtelier.LYON1,
    CodeAtelier.LYON7: CodeAtelier.LYON8,
}
CATEGORIES_REPARATION = {Categorie.PANNE, Categorie.BATTERIE, Categorie.GARANTIE}
ATELIER_PAR_DEFAUT = CodeAtelier.LYON1
NB_TENTATIVES = 2  # cahier des charges : une nouvelle tentative en cas d'échec
SEUIL_CONFIANCE = 0.6  # en dessous : badge « à vérifier »


def normaliser(texte: str) -> str:
    """Minuscules et sans accents : "Fumée" → "fumee"."""
    decompose = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def detecter_alerte(message: str) -> str | None:
    """Renvoie le premier mot-clé d'alerte trouvé dans le message, sinon None."""
    trouve = _REGEX_ALERTE.search(normaliser(message))
    return trouve.group(1) if trouve else None


def masquer_cartes(message: str) -> str:
    """Remplace les numéros de carte bancaire avant tout envoi à l'IA."""
    return _REGEX_CARTE.sub("[CARTE MASQUÉE]", message)


def router(atelier_cite: CodeAtelier | None, categorie: Categorie) -> CodeAtelier:
    """Applique les règles de routage du cadrage (section 9)."""
    if atelier_cite is None:
        return ATELIER_PAR_DEFAUT
    if categorie in CATEGORIES_REPARATION:
        return REDIRECTION_REPARATION.get(atelier_cite, atelier_cite)
    return atelier_cite


def trier(message: str, provider: AIProvider) -> ResultatTriage:
    """Analyse un message avec l'IA, puis applique les garde-fous métier.

    Ne lève jamais d'exception : une demande client ne doit jamais être perdue.
    """
    alerte = detecter_alerte(message)
    texte_pour_ia = masquer_cartes(message)

    analyse = None
    erreur_ia = None
    for _ in range(NB_TENTATIVES):
        try:
            analyse = provider.analyser(texte_pour_ia)
            break
        # Volontairement large : quelle que soit la panne de l'IA (JSON invalide,
        # Ollama éteint, délai dépassé), on passe en mode dégradé.
        except Exception as exc:  # noqa: BLE001
            erreur_ia = f"{type(exc).__name__}: {exc}"

    if analyse is None:
        # Mode dégradé : valeurs prudentes et vérification humaine obligatoire.
        categorie, urgence, atelier_cite = Categorie.AUTRE, Urgence.NORMALE, None
        a_verifier = True
    else:
        categorie, urgence = analyse.categorie, analyse.urgence
        atelier_cite = analyse.atelier_suggere
        a_verifier = analyse.confiance < SEUIL_CONFIANCE
        erreur_ia = None  # une tentative a réussi

    # Garde-fou de sécurité : un mot-clé de danger force l'urgence critique,
    # quoi que l'IA ait répondu.
    if alerte:
        urgence = Urgence.CRITIQUE

    return ResultatTriage(
        analyse=analyse,
        categorie=categorie,
        urgence=urgence,
        atelier_destination=router(atelier_cite, categorie),
        alerte=alerte,
        a_verifier=a_verifier,
        erreur_ia=erreur_ia,
    )
