# Journal d'évaluation de l'IA

Jeu de test : 40 messages annotés (`data/eval/messages.jsonl`) — 6 critiques, 8 hautes, 16 normales, 10 basses.
Commande : `uv run python -m scripts.evaluate` · Rapports détaillés : `data/eval/resultats/`

## Historique des scores

| # | Date | Modèle | Changement | Catégorie | Urgence | Atelier | Rappel critiques | Sous-estimées | Temps moyen |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-10-13 | qwen2.5:3b | Baseline : prompt v2 | 77,5 % | 60,0 % | 77,5 % | 66,7 % (4/6) | 6 | 5,9 s |
| 1 | 2026-10-13 | qwen2.5:3b | + garde-fous en code (mots-clés d'alerte, masquage carte, routage, 2 tentatives) | 77,5 % | 65,0 % | 77,5 % | 100 % (6/6) | 4 | 5,6 s |

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


## Run 1 : effet des garde-fous

- **Rappel critiques : 66,7 % → 100 %.** Les mots-clés ont rattrapé #1 (« brûlé ») et #4 (« fume », écrit en style SMS).
- **Bonne destination : 97,5 %** grâce au routage en code. Seule erreur : #40, où l'IA invente `lyon8` pour « Villeurbanne ».
- Aucun mot-clé n'a été ajouté pour s'adapter au jeu de test (pas de surapprentissage) : le #2 (« ne freinent presque plus ») reste détecté par l'IA seule.
- Reste à traiter : l'IA met « normale » à presque tout (4 « haute » sous-estimées, 10 « basse » surestimées). Piste : le prompt.


## Brouillons de réponse (phrase écrite par l'IA)

Évaluation : `uv run python -m scripts.evaluate_brouillons` sur les 40 messages · contrôles automatiques + relecture manuelle (`data/eval/brouillons/*_notation.md`).

| # | Date | Modèle | Changement | Conformes (auto) | Vraiment bonnes (relecture) | Temps moyen |
|---|---|---|---|---|---|---|
| B0 | 2026-10-15 | qwen2.5:3b | Prompt v2 (avec exemples) | 9/40 (22 %) | ≈ 5/40 | 2,2 s |
| B1 | 2026-10-15 | qwen2.5:3b | Prompt v3 : « nous », début de phrase imposé, sans exemples | 27/40 (68 %) | ≈ 15/40 | 2,5 s |
| B2 | 2026-10-15 | qwen2.5:7b | Prompt v3 | 33/40 (82 %) | ≈ 24/40 | 6,1 s |

**Enseignements**
- Les premiers contrôles automatiques annonçaient 85 % de phrases conformes alors que la relecture en trouvait très peu de bonnes : une métrique doit être confrontée à une lecture humaine.
- Les exemples du prompt étaient recopiés par le petit modèle (« facture », « signalé ») : les supprimer et imposer le début de phrase a été plus efficace.
- Le 7B est plus fluide mais **invente des faits** (atelier « fermé aujourd'hui », « pièce disponible », « sous garantie ») : prochain chantier.

**Prochaines pistes**
- Contrôles à renforcer : affirmations factuelles (« est fermé », « disponible », « sous garantie »), « veuillez », « sera », « recevrez ».
- Corriger le faux positif « sujet ajouté » quand le client écrit en style SMS (« batri »).