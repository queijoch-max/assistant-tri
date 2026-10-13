# Assistant IA de tri SAV — Cycles Mistral

> **Projet en cours de développement** 
> Ce README est mis à jour à chaque étape terminée (voir la [feuille de route](#feuille-de-route)).

Application web qui **trie automatiquement les demandes clients** d'un service après-vente grâce à une IA **100 % locale et gratuite**, puis propose un **brouillon de réponse** que l'agent relit avant envoi.

**Projet portfolio** réalisé dans le cadre de ma recherche d'alternance en développement Python / IA.

---

##  Le problème métier

*Cycles Mistral* est un réseau fictif de **6 ateliers de vélos électriques à Lyon**.

| Situation actuelle | Objectif |
|---|---|
| ~250 messages par semaine (formulaire + e-mails) | Tri automatique dès la réception |
| 2 personnes, **12 h par semaine** à lire, classer et transférer | **Moins de 3 h par semaine** |
| Des urgences (batterie qui chauffe, freins…) noyées parmi les questions simples | **Aucune urgence non vue plus de 2 h** |

> **Règle d'or :** l'IA propose, l'humain décide. Aucune réponse ne part au client sans validation d'un agent.

Le cahier des charges complet (périmètre, user stories MoSCoW, règles métier, charte graphique, critères de recette) est dans [`docs/cadrage.md`](docs/cadrage.md).

---

## Fonctionnalités visées

- **Formulaire client** avec numéro de suivi
- **Analyse IA** de chaque demande : catégorie, urgence (4 niveaux), résumé, atelier concerné, justification et score de confiance
- **Garde-fous** : mots-clés de sécurité qui forcent l'urgence critique, masquage des numéros de carte avant l'appel à l'IA, protection contre l'injection de prompt
- **Tableau de bord SAV** trié par urgence, avec filtres, recherche et badges de couleur
- **Correction humaine** des propositions de l'IA, avec mesure du taux de correction
- **Brouillon de réponse** généré par l'IA, modifiable avant envoi
- **Évaluation chiffrée** de l'IA sur un jeu de 40 messages annotés à la main

---

## Stack technique

| Couche | Outil | Pourquoi |
|---|---|---|
| Langage | Python 3.13 | |
| Projet | uv + ruff | Dépendances verrouillées, code formaté et vérifié |
| API web | FastAPI | Typage, validation, documentation automatique |
| Données | Pydantic v2 | Contrats de données partagés entre l'API et l'IA |
| IA | Ollama + `qwen2.5:3b` | Gratuit, local : **les données clients ne quittent pas la machine** (RGPD) |
| Tests | pytest | |
| *À venir* | SQLite + SQLAlchemy, Jinja2 + HTMX, Docker | |

### Architecture de l'IA

```
message client ──► triage (garde-fous) ──► AIProvider ──┬──► OllamaProvider  (vrai LLM local)
                                                        └──► FakeProvider    (tests et démo, sans IA)
```

Le reste de l'application dépend d'une **interface** (`AIProvider`), jamais d'un modèle précis. On peut donc lancer les tests en quelques millisecondes, faire une démo sans télécharger de modèle, ou changer d'IA en écrivant une seule classe.

---

## Feuille de route

## Feuille de route

- [x] **Cadrage** : cahier des charges, règles métier, critères de recette
- [x] **Mise en place** : uv, FastAPI, ruff, Git
- [x] **Contrats de données** : schémas Pydantic et tests
- [x] **Configuration** par variables d'environnement (`pydantic-settings`)
- [x] **Interface IA** `AIProvider` et `FakeProvider`
- [x] **Appel au LLM local** (`OllamaProvider`) : sortie JSON structurée, délai maximum
- [x] **Jeu de test** (40 messages annotés) et script d'évaluation `evaluate.py`
- [ ] Garde-fous métier : mots-clés d'alerte, masquage des données bancaires, routage *(en cours)*
- [ ] Robustesse : nouvelle tentative et mode dégradé si l'IA échoue
- [ ] Génération des brouillons de réponse
- [ ] Base de données SQLite
- [ ] Formulaire client et tableau de bord SAV (Jinja2 + HTMX)
- [ ] Authentification des agents
- [ ] Statistiques de la semaine
- [ ] Docker : lancement en une commande
- [ ] Captures d'écran et démo GIF

---

## Résultats de l'IA

Évaluation sur 40 messages annotés à la main (`uv run python -m scripts.evaluate`).
Historique complet et analyse des erreurs : [`docs/evaluation.md`](docs/evaluation.md).

| Indicateur | Baseline (qwen2.5:3b) | Cible |
|---|---|---|
| Bonne catégorie | 77,5 % | ≥ 85 % |
| Bonne urgence | 60,0 % | — |
| **Urgences critiques détectées** | **66,7 %** (4/6) | **100 %** |
| Urgences sous-estimées | 6 | 0 |
| Temps moyen par message | 5,9 s (CPU, sans GPU) | — |

Prochaine étape : des garde-fous en code (mots-clés d'alerte, routage) pour atteindre 100 % de détection des urgences critiques.

---

## Lancer le projet (état actuel)

**Prérequis :** [Python 3.13](https://www.python.org/), [uv](https://docs.astral.sh/uv/) et, en option, [Ollama](https://ollama.com/).

```bash
# 1. Installer les dépendances
uv sync

# 2. Créer la configuration locale
cp .env.example .env        # Windows : copy .env.example .env

# 3. Lancer l'API
uv run fastapi dev app/main.py
```

Puis ouvrir http://127.0.0.1:8000/docs pour la documentation interactive.

**Lancer les tests :**

```bash
uv run pytest -v
```

---

## Structure

```
assistant-tri/
├── app/
│ ├── main.py # application FastAPI
│ ├── config.py # réglages lus depuis .env
│ ├── schemas.py # contrats de données (Pydantic)
│ └── services/
│ └── ai_client.py # interface AIProvider, FakeProvider, OllamaProvider
├── data/eval/
│ ├── messages.jsonl # 40 messages de test annotés
│ └── resultats/ # rapports d’évaluation horodatés
├── scripts/
│ ├── essai_ollama.py # essai rapide sur quelques messages
│ └── evaluate.py # évaluation complète de l’IA
├── tests/ # tests pytest
├── docs/
│ ├── cadrage.md # cahier des charges
│ └── evaluation.md # journal des scores de l’IA
├── .env.example # modèle de configuration
└── pyproject.toml
```

---

**Charlotte Queijo** 

<!-- Ajouter ici : lien LinkedIn, e-mail ou portfolio -->