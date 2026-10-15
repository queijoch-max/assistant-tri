"""Évalue la phrase que l'IA écrit au milieu des brouillons de réponse.

Contrôles automatiques sur les 40 messages du jeu d'évaluation, plus un fichier
Markdown à noter à la main (la qualité d'un texte ne se mesure pas qu'en code).
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.services.ai_client import AIProvider, get_provider
from app.services.brouillons import (
    MOTS_ACCROCHE_MAX,
    PROMESSES_A_VERIFIER,
    nettoyer_accroche,
)
from app.services.triage import masquer_cartes, normaliser
from scripts.evaluate import CHEMIN_MESSAGES, charger_messages

DOSSIER_RESULTATS = Path("data/eval/brouillons")
MOTS_CONSIGNE = 40  # limite demandée dans le prompt

# Sujets que l'IA ne doit pas évoquer si le client n'en parle pas (racines sans
# accents). On y met aussi les sujets des exemples du prompt, pour repérer
# quand l'IA les recopie.
SUJETS = (
    "factur", "rembours", "batter", "frein", "command", "livr", "garant",
    "repar", "pneu", "moteur", "paiement", "prix", "stock", "sacoche",
    "antivol", "derailleur", "casque", "ecran",
)  # fmt: skip

# Formule attendue selon la catégorie annotée (les autres catégories sont libres).
FORMULES_ATTENDUES = {
    "reclamation": ("desole", "excus", "regrett"),
    "avant_achat": ("merci",),
}

HORS_CONSIGNE = ("bonjour", "cordialement", "sav cycles mistral")

# L'IA doit seulement montrer qu'elle a compris : la suite (qui rappelle, quand)
# est écrite par le code. Ces racines signalent un engagement ou un conseil.
ENGAGEMENTS = (
    "allons", "vais ", "pouvons", "pourrez", "accueill", "transmet", "recontact",
    "rappel", "organis", "propos", "envoy", "verifier", "aider", "rassur",
)  # fmt: skip
CONSEILS = ("veillez", "ne pas ", "evitez", "debranch", "rebranch", "n'utilisez")

def controler_accroche(brute: str, message: str, categorie: str) -> list[str]:
    """Liste les défauts de la phrase de l'IA. Liste vide = phrase conforme."""
    defauts = []
    accroche = nettoyer_accroche(brute)
    phrase = normaliser(accroche)
    client = normaliser(message)
    nb_mots = len(accroche.split())

    if not accroche:
        defauts.append("vide")
    if nb_mots > MOTS_ACCROCHE_MAX:
        defauts.append(f"écartée ({nb_mots} mots)")
    elif nb_mots > MOTS_CONSIGNE:
        defauts.append(f"trop longue ({nb_mots} mots)")
    if re.search(r"[*#]|\n\s*(-|\d+\.)", brute):
        defauts.append("mise en forme")
    if any(mot in phrase for mot in HORS_CONSIGNE):
        defauts.append("salutation ou signature")

    ajoutes = [s for s in SUJETS if s in phrase and s not in client]
    if ajoutes:
        defauts.append(f"sujet ajouté : {', '.join(ajoutes)}")

    nombres = set(re.findall(r"\d+", phrase)) - set(re.findall(r"\d+", client))
    if "€" in accroche or nombres or re.match(r"(oui|non)\b", phrase):
        defauts.append("information donnée")

    if re.search(r"\bje\b", phrase):
        defauts.append("parle en « je »")
    engagements = [m for m in ENGAGEMENTS + PROMESSES_A_VERIFIER if m in phrase]
    if engagements:
        defauts.append(f"engagement pris : {', '.join(engagements)}")
    if any(m in phrase for m in CONSEILS):
        defauts.append("conseil donné")


    attendues = FORMULES_ATTENDUES.get(categorie)
    if attendues and not any(mot in phrase for mot in attendues):
        defauts.append(f"formule inadaptée à « {categorie} »")
    return defauts


def evaluer(provider: AIProvider, messages: list[dict]) -> list[dict]:
    resultats = []
    for i, msg in enumerate(messages, start=1):
        print(f"[{i}/{len(messages)}] message {msg['id']}...", end="", flush=True)
        debut = time.perf_counter()
        try:
            brute = provider.rediger_accroche(masquer_cartes(msg["message"]))
            defauts = controler_accroche(brute, msg["message"], msg["categorie"])
        # Volontairement large : une panne ne doit pas arrêter l'évaluation.
        except Exception as exc:  # noqa: BLE001
            brute = ""
            defauts = [f"erreur IA ({type(exc).__name__})"]
        duree = time.perf_counter() - debut
        print(f" {duree:.1f} s")
        resultats.append(
            {
                "id": msg["id"],
                "categorie": msg["categorie"],
                "message": msg["message"],
                "accroche": nettoyer_accroche(brute),
                "defauts": defauts,
                "duree": duree,
            }
        )
    return resultats


def calculer_metriques(resultats: list[dict]) -> dict:
    total = len(resultats)
    compteur: dict[str, int] = {}
    for r in resultats:
        for defaut in r["defauts"]:
            type_defaut = defaut.split(" (")[0].split(" :")[0]
            compteur[type_defaut] = compteur.get(type_defaut, 0) + 1
    return {
        "total": total,
        "conformes": sum(1 for r in resultats if not r["defauts"]),
        "defauts_par_type": dict(sorted(compteur.items(), key=lambda kv: -kv[1])),
        "mots_moyen": sum(len(r["accroche"].split()) for r in resultats) / total,
        "duree_moyenne": sum(r["duree"] for r in resultats) / total,
    }


def afficher_rapport(m: dict, resultats: list[dict], modele: str) -> None:
    print("\n" + "=" * 60)
    print(f"ÉVALUATION DES BROUILLONS — {m['total']} messages — {modele}")
    print("=" * 60)
    print(
        f"Phrases conformes : {m['conformes']}/{m['total']} ({m['conformes'] / m['total']:.0%})"
    )
    print(f"Longueur moyenne  : {m['mots_moyen']:.0f} mots")
    print(f"Temps moyen       : {m['duree_moyenne']:.1f} s")
    print("\nDÉFAUTS PAR TYPE :")
    for type_defaut, nombre in m["defauts_par_type"].items():
        print(f"   {nombre:>3}  {type_defaut}")
    print("\nPHRASES AVEC DÉFAUTS :")
    for r in resultats:
        if r["defauts"]:
            print(f"\n#{r['id']} [{r['categorie']}] {r['message'][:60]}")
            print(f"   IA : {r['accroche']}")
            print(f"   ⚠️  {' | '.join(r['defauts'])}")


def sauvegarder(m: dict, resultats: list[dict], modele: str) -> Path:
    """Enregistre le rapport JSON et une grille Markdown à noter à la main."""
    DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)
    base = f"{datetime.now():%Y-%m-%d_%H%M}_{modele.replace(':', '-')}"
    contenu = {"modele": modele, "metriques": m, "resultats": resultats}
    (DOSSIER_RESULTATS / f"{base}.json").write_text(
        json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lignes = [
        f"# Notation manuelle des brouillons — {modele}",
        "",
        "Note de 1 à 3 : 1 = à réécrire, 2 = à retoucher, 3 = envoyable tel quel.",
        "",
        "| # | Catégorie | Message du client | Phrase de l'IA | Défauts auto | Note |",
        "|---|---|---|---|---|---|",
    ]
    for r in resultats:
        cellules = [r["message"], r["accroche"], ", ".join(r["defauts"]) or "—"]
        message, accroche, defauts = (c.replace("|", "/") for c in cellules)
        lignes.append(
            f"| {r['id']} | {r['categorie']} | {message} | {accroche} | {defauts} |  |"
        )
    chemin = DOSSIER_RESULTATS / f"{base}_notation.md"
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


def main() -> None:
    if settings.ai_provider == "fake":
        modele = "fake"
    else:
        modele = settings.ollama_model_brouillon or settings.ollama_model
    messages = charger_messages(CHEMIN_MESSAGES)
    resultats = evaluer(get_provider(), messages)
    metriques = calculer_metriques(resultats)
    afficher_rapport(metriques, resultats, modele)
    chemin = sauvegarder(metriques, resultats, modele)
    print(f"\nGrille à noter à la main : {chemin}")


if __name__ == "__main__":
    main()
