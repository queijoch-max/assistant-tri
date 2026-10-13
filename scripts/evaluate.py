import json
import time
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.services.ai_client import AIProvider, get_provider

CHEMIN_MESSAGES = Path("data/eval/messages.jsonl")
DOSSIER_RESULTATS = Path("data/eval/resultats")
CHAMPS = ("categorie", "urgence", "atelier")
ORDRE_URGENCE = {"basse": 0, "normale": 1, "haute": 2, "critique": 3}


def charger_messages(chemin: Path) -> list[dict]:
    """Lit un fichier JSON Lines : un objet JSON par ligne non vide."""
    with chemin.open(encoding="utf-8") as fichier:
        return [json.loads(ligne) for ligne in fichier if ligne.strip()]


def evaluer(provider: AIProvider, messages: list[dict]) -> list[dict]:
    """Fait analyser chaque message et enregistre l'attendu et l'obtenu."""
    resultats = []
    for i, msg in enumerate(messages, start=1):
        print(f"[{i}/{len(messages)}] message {msg['id']}...", end="", flush=True)
        debut = time.perf_counter()
        try:
            analyse = provider.analyser(msg["message"])
            atelier = analyse.atelier_suggere
            obtenu = {
                "categorie": analyse.categorie.value,
                "urgence": analyse.urgence.value,
                "atelier": atelier.value if atelier else None,
            }
            erreur = None
        # Volontairement large : une réponse invalide ne doit pas arrêter l'évaluation.
        except Exception as exc:  # noqa: BLE001
            obtenu = None
            erreur = f"{type(exc).__name__}: {exc}"
        duree = time.perf_counter() - debut
        print(f" {duree:.1f} s")

        resultats.append(
            {
                "id": msg["id"],
                "message": msg["message"],
                "attendu": {champ: msg[champ] for champ in CHAMPS},
                "obtenu": obtenu,
                "erreur": erreur,
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
        "erreurs": total - len(valides),
        "precision_categorie": nb_corrects("categorie") / total,
        "precision_urgence": nb_corrects("urgence") / total,
        "precision_atelier": nb_corrects("atelier") / total,
        "rappel_critique": critiques_detectees / len(critiques) if critiques else 1.0,
        "sous_estimees": sum(1 for r in valides if ecart_urgence(r) < 0),
        "sur_estimees": sum(1 for r in valides if ecart_urgence(r) > 0),
        "duree_moyenne": sum(r["duree"] for r in resultats) / total,
    }


def afficher_rapport(metriques: dict, resultats: list[dict], modele: str) -> None:
    m = metriques
    print("\n" + "=" * 60)
    print(f"RAPPORT D'ÉVALUATION — {m['total']} messages — {modele}")
    print("=" * 60)
    print(f"Précision catégorie    : {m['precision_categorie']:6.1%}   (cible ≥ 85 %)")
    print(f"Précision urgence      : {m['precision_urgence']:6.1%}")
    print(f"Précision atelier      : {m['precision_atelier']:6.1%}")
    print(f"Rappel critiques       : {m['rappel_critique']:6.1%}   (cible 100 %)")
    print(f"Urgences sous-estimées : {m['sous_estimees']}   (dangereux)")
    print(f"Urgences surestimées   : {m['sur_estimees']}")
    print(f"Erreurs techniques     : {m['erreurs']}")
    print(f"Temps moyen            : {m['duree_moyenne']:.1f} s")

    print("\nDÉSACCORDS :")
    for r in resultats:
        if r["obtenu"] is None:
            print(f"\n#{r['id']} {r['message'][:70]}")
            print(f"   ERREUR : {r['erreur']}")
            continue
        differences = [c for c in CHAMPS if r["obtenu"][c] != r["attendu"][c]]
        if differences:
            print(f"\n#{r['id']} {r['message'][:70]}")
            for champ in differences:
                attendu = str(r["attendu"][champ])
                print(
                    f"   {champ:<10}: attendu {attendu:<12} obtenu {r['obtenu'][champ]}"
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