import json
import time
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.schemas import Categorie, CodeAtelier
from app.services.ai_client import AIProvider, get_provider
from app.services.triage import router, trier

CHEMIN_MESSAGES = Path("data/eval/messages.jsonl")
DOSSIER_RESULTATS = Path("data/eval/resultats")
CHAMPS = ("categorie", "urgence", "atelier", "destination")
ORDRE_URGENCE = {"basse": 0, "normale": 1, "haute": 2, "critique": 3}


def charger_messages(chemin: Path) -> list[dict]:
    """Lit un fichier JSON Lines : un objet JSON par ligne non vide."""
    with chemin.open(encoding="utf-8") as fichier:
        return [json.loads(ligne) for ligne in fichier if ligne.strip()]


def destination_attendue(msg: dict) -> str:
    """Atelier de destination déduit de l'annotation, avec les mêmes règles de routage."""
    atelier = CodeAtelier(msg["atelier"]) if msg["atelier"] else None
    return router(atelier, Categorie(msg["categorie"])).value


def evaluer(provider: AIProvider, messages: list[dict]) -> list[dict]:
    """Fait trier chaque message (IA + garde-fous) et compare à l'annotation."""
    resultats = []
    for i, msg in enumerate(messages, start=1):
        print(f"[{i}/{len(messages)}] message {msg['id']}...", end="", flush=True)
        debut = time.perf_counter()
        resultat = trier(msg["message"], provider)
        duree = time.perf_counter() - debut
        print(f" {duree:.1f} s")

        atelier_cite = resultat.analyse.atelier_suggere if resultat.analyse else None
        resultats.append(
            {
                "id": msg["id"],
                "message": msg["message"],
                "attendu": {
                    "categorie": msg["categorie"],
                    "urgence": msg["urgence"],
                    "atelier": msg["atelier"],
                    "destination": destination_attendue(msg),
                },
                "obtenu": {
                    "categorie": resultat.categorie.value,
                    "urgence": resultat.urgence.value,
                    "atelier": atelier_cite.value if atelier_cite else None,
                    "destination": resultat.atelier_destination.value,
                },
                "alerte": resultat.alerte,
                "erreur": resultat.erreur_ia,
                "duree": duree,
            }
        )
    return resultats


def ecart_urgence(resultat: dict) -> int:
    """Écart de niveau : < 0 = sous-estimée, > 0 = surestimée, 0 = juste."""
    obtenu = ORDRE_URGENCE[resultat["obtenu"]["urgence"]]
    attendu = ORDRE_URGENCE[resultat["attendu"]["urgence"]]
    return obtenu - attendu


def calculer_metriques(resultats: list[dict]) -> dict:
    """Calcule les scores à partir des résultats. Ne dépend pas de l'IA."""
    total = len(resultats)
    valides = [r for r in resultats if r["obtenu"] is not None]

    def nb_corrects(champ: str) -> int:
        return sum(1 for r in valides if r["obtenu"][champ] == r["attendu"][champ])

    critiques = [r for r in resultats if r["attendu"]["urgence"] == "critique"]
    critiques_detectees = sum(
        1
        for r in critiques
        if r["obtenu"] is not None and r["obtenu"]["urgence"] == "critique"
    )

    return {
        "total": total,
        "erreurs": sum(1 for r in resultats if r.get("erreur")),
        "alertes": sum(1 for r in resultats if r.get("alerte")),
        "precision_categorie": nb_corrects("categorie") / total,
        "precision_urgence": nb_corrects("urgence") / total,
        "precision_atelier": nb_corrects("atelier") / total,
        "precision_destination": nb_corrects("destination") / total,
        "rappel_critique": critiques_detectees / len(critiques) if critiques else 1.0,
        "sous_estimees": sum(1 for r in valides if ecart_urgence(r) < 0),
        "sur_estimees": sum(1 for r in valides if ecart_urgence(r) > 0),
        "duree_moyenne": sum(r["duree"] for r in resultats) / total,
    }


def afficher_rapport(metriques: dict, resultats: list[dict], modele: str) -> None:
    m = metriques
    print("\n" + "=" * 60)
    print(f"RAPPORT D'ÉVALUATION — {m['total']} messages — {modele} + garde-fous")
    print("=" * 60)
    print(f"Précision catégorie    : {m['precision_categorie']:6.1%}   (cible ≥ 85 %)")
    print(f"Précision urgence      : {m['precision_urgence']:6.1%}")
    print(f"Atelier cité           : {m['precision_atelier']:6.1%}")
    print(f"Bonne destination      : {m['precision_destination']:6.1%}")
    print(f"Rappel critiques       : {m['rappel_critique']:6.1%}   (cible 100 %)")
    print(f"Urgences sous-estimées : {m['sous_estimees']}   (dangereux)")
    print(f"Urgences surestimées   : {m['sur_estimees']}")
    print(f"Alertes mots-clés      : {m['alertes']}")
    print(f"Erreurs de l'IA        : {m['erreurs']}   (mode dégradé)")
    print(f"Temps moyen            : {m['duree_moyenne']:.1f} s")

    print("\nDÉSACCORDS :")
    for r in resultats:
        differences = [c for c in CHAMPS if r["obtenu"][c] != r["attendu"][c]]
        if differences or r["erreur"]:
            print(f"\n#{r['id']} {r['message'][:70]}")
            if r["erreur"]:
                print(f"   ERREUR IA : {r['erreur']}")
            for champ in differences:
                attendu = str(r["attendu"][champ])
                print(
                    f"   {champ:<11}: attendu {attendu:<12} obtenu {r['obtenu'][champ]}"
                )


def sauvegarder(metriques: dict, resultats: list[dict], modele: str) -> Path:
    """Enregistre le rapport complet en JSON pour garder l'historique des scores."""
    DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H%M")
    chemin = DOSSIER_RESULTATS / f"{horodatage}_{modele.replace(':', '-')}.json"
    contenu = {"modele": modele, "metriques": metriques, "resultats": resultats}
    texte = json.dumps(contenu, ensure_ascii=False, indent=2)
    chemin.write_text(texte, encoding="utf-8")
    return chemin


def main() -> None:
    modele = "fake" if settings.ai_provider == "fake" else settings.ollama_model
    messages = charger_messages(CHEMIN_MESSAGES)
    resultats = evaluer(get_provider(), messages)
    metriques = calculer_metriques(resultats)
    afficher_rapport(metriques, resultats, modele)
    chemin = sauvegarder(metriques, resultats, modele)
    print(f"\nRapport enregistré : {chemin}")


if __name__ == "__main__":
    main()
