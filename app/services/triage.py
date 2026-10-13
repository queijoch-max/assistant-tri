import re
import unicodedata

from app.schemas import Categorie, CodeAtelier

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