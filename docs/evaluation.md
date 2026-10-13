# Journal d'évaluation de l'IA

Jeu de test : 40 messages annotés (`data/eval/messages.jsonl`) — 6 critiques, 8 hautes, 16 normales, 10 basses.
Commande : `uv run python -m scripts.evaluate` · Rapports détaillés : `data/eval/resultats/`

## Historique des scores

| # | Date | Modèle | Changement | Catégorie | Urgence | Atelier | Rappel critiques | Sous-estimées | Temps moyen |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-10-13 | qwen2.5:3b | Baseline : prompt v2 | 77,5 % | 60,0 % | 77,5 % | 66,7 % (4/6) | 6 | 5,9 s |

**Cibles du cahier des charges :** catégorie ≥ 85 % · rappel critiques = 100 %.

## Analyse de la baseline

| Problème observé | Messages | Piste |
|---|---|---|
| Critiques ratées quand le ton est calme ou l'orthographe mauvaise | #1, #4 | Mots-clés d'alerte en code |
| « basse » jamais utilisée (0/10) : tout devient « normale » | #31 à #40 | Prompt : définition et exemple de « basse » |
| | `lyon1` mis par l'IA quand aucun atelier n'est cité : sans conséquence pour le client (la règle 3 envoie au siège), mais ce n'est pas le rôle de l'IA | #2, 7, 10, 11, 13, 16, 29, 30 | Routage en code : l'IA détecte, le code décide |
| Atelier inventé à partir d'un lieu hors réseau (vraie erreur de destination) | #40 | Idem |
| Confusions batterie / panne et avant_achat / autre | #11, 17, 32, 36 | Prompt, ou modèle plus gros |
| Un remerciement classé « réclamation » | #38 | Prompt |