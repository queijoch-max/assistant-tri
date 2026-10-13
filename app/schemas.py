from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# 1. LES VALEURS AUTORISEES (Enums)
# ============================================================================
class Categorie(StrEnum):
    RECLAMATION = "reclamation"
    GARANTIE = "garantie"
    BATTERIE = "batterie"
    PANNE = "panne"
    COMMANDE = "commande"
    AVANT_ACHAT = "avant_achat"
    AUTRE = "autre"


class Urgence(StrEnum):
    CRITIQUE = "critique"
    HAUTE = "haute"
    NORMALE = "normale"
    BASSE = "basse"


class CodeAtelier(StrEnum):
    LYON1 = "lyon1"
    LYON2 = "lyon2"
    LYON3 = "lyon3"
    LYON5 = "lyon5"
    LYON7 = "lyon7"
    LYON8 = "lyon8"


# ============================================================================
# 2. CE QU'UN CLIENT ENVOIE (FORMULAIRE F1)
# ============================================================================
class DemandeCreate(BaseModel):
    """Données saisies par le client. La date, l'id et le numéro de suivi sont ajoutés par le serveur, jamais par le client."""

    nom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    atelier: CodeAtelier | None = None
    n_commande: str | None = Field(default=None, max_length=30)
    message: str = Field(min_length=10, max_length=5000)


# ============================================================================
# 3. CE QUE L'IA DOIT RENVOYER (l'analyse)
# ============================================================================
# Les descriptions ci-dessous sont envoyées au LLM avec le schéma JSON :
# elles font partie du prompt.
class AnalyseIA(BaseModel):
    resume: str = Field(
        max_length=200,
        description="Résumé neutre de la demande en 1 à 2 phrases.",
    )
    justification: str = Field(
        max_length=300,
        description="Pourquoi cette catégorie et cette urgence, en citant les éléments du message qui ont décidé.",
    )
    categorie: Categorie = Field(
        description="Sujet principal. Si plusieurs sujets, prendre le premier dans cet ordre : reclamation > garantie > batterie > panne > commande > avant_achat > autre.",
    )
    urgence: Urgence = Field(
        description="critique = risque pour la sécurité (fumée, chaleur, freins, accident) ; haute = vélo inutilisable ou échéance aujourd'hui ; normale = gêne mais vélo utilisable ; basse = simple information. En cas de doute, choisir le niveau le plus élevé.",
    )
    atelier_suggere: CodeAtelier | None = Field(
        description="Atelier cité par le client, sinon null.",
    )
    confiance: float = Field(
        ge=0,
        le=1,
        description="Confiance dans la classification, entre 0 et 1",
    )


# ============================================================================
# 4. LE RÉSULTAT DU TRIAGE (IA + garde-fous)
# ============================================================================
class ResultatTriage(BaseModel):
    """Décision finale : la proposition de l'IA corrigée par les règles métier."""

    analyse: AnalyseIA | None  # proposition brute de l'IA (None si l'IA a échoué)
    categorie: Categorie
    urgence: Urgence
    atelier_destination: CodeAtelier
    alerte: str | None  # mot-clé de danger trouvé, s'il y en a un
    a_verifier: bool  # True si un humain doit vérifier en priorité
    erreur_ia: str | None = None
