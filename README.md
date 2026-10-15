# Assistant IA de tri SAV — Cycles Mistral

> **Projet en cours de développement**
> Ce README est mis à jour à chaque étape terminée (voir la [feuille de route](#feuille-de-route)).

Application web qui **trie automatiquement les demandes clients** d'un service après-vente grâce à une IA **100 % locale et gratuite**, puis propose un **brouillon de réponse** que l'agent relit avant envoi.

**Projet portfolio** réalisé dans le cadre de ma recherche d'alternance en développement Python / IA.

---

## Le problème métier

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
- **Brouillon de réponse** construit par le code autour d'une phrase personnalisée écrite par l'IA, modifiable avant envoi
- **Évaluation chiffrée** de l'IA sur un jeu de 40 messages annotés à la main

---

## Stack technique

| Couche | Outil | Pourquoi |
|---|---|---|
| Langage | Python 3.13 | |
| Projet | uv + ruff | Dépendances verrouillées, code formaté et vérifié |
| API web | FastAPI | Typage, validation, documentation automatique |
| Données | Pydantic v2 | Contrats de données partagés entre l'API et l'IA |
| IA | Ollama : `qwen2.5:3b` (classement) et `qwen2.5:7b` (rédaction) | Gratuit, local : **les données clients ne quittent pas la machine** (RGPD) |
| Tests | pytest | |
| *À venir* | SQLite + SQLAlchemy, Jinja2 + HTMX, Docker | |

### Architecture de l'IA

```
                      ┌─► detecter_alerte()   mot de danger → urgence critique forcée
message client ──► trier() ──► masquer_cartes() ──► AIProvider.analyser()
                      └─► router()             atelier de destination (règles métier)

brouillon ──► Bonjour + [phrase écrite par l'IA] + consigne de sécurité + suivi + signature
               └── écrit par le code ──┘                └────── écrit par le code ──────┘
```

- Le reste de l'application dépend d'une **interface** (`AIProvider`), jamais d'un modèle précis : tests en quelques millisecondes avec un `FakeProvider`, démo sans télécharger de modèle, changement d'IA en écrivant une seule classe.
- **L'IA ne fait que ce que le code ne sait pas faire** (comprendre le sens d'un message, reformuler avec empathie). Tout ce qui est certain (sécurité, routage, structure de la réponse) est écrit en Python, donc impossible à contourner par une injection de prompt.
- **Aucune demande n'est perdue** : si l'IA échoue deux fois, la demande passe en mode dégradé et un agent la vérifie.

---

## Feuille de route

- [x] **Cadrage** : cahier des charges, règles métier, critères de recette
- [x] **Mise en place** : uv, FastAPI, ruff, Git
- [x] **Contrats de données** : schémas Pydantic et tests
- [x] **Configuration** par variables d'environnement (`pydantic-settings`)
- [x] **Interface IA** `AIProvider` et `FakeProvider`
- [x] **Appel au LLM local** (`OllamaProvider`) : sortie JSON structurée, délai maximum
- [x] **Jeu de test** (40 messages annotés) et script d'évaluation `evaluate.py`
- [x] **Garde-fous métier** : mots-clés d'alerte, masquage des données bancaires, routage
- [x] **Robustesse** : nouvelle tentative et mode dégradé si l'IA échoue
- [x] **Brouillons de réponse** : gabarit + phrase IA, contrôles, évaluation dédiée
- [ ] Contrôles contre les faits inventés dans les brouillons *(en cours)*
- [ ] Base de données SQLite
- [ ] Formulaire client et tableau de bord SAV (Jinja2 + HTMX)
- [ ] Authentification des agents
- [ ] Statistiques de la semaine
- [ ] Docker : lancement en une commande
- [ ] Captures d'écran et démo GIF

---

## Résultats de l'IA

Historique complet et analyse des erreurs : [`docs/evaluation.md`](docs/evaluation.md).

### Classement des demandes

Évaluation sur 40 messages annotés à la main (`uv run python -m scripts.evaluate`).

| Indicateur | IA seule (qwen2.5:3b) | IA + garde-fous | Cible |
|---|---|---|---|
| Bonne catégorie | 77,5 % | 77,5 % | ≥ 85 % |
| Bonne urgence | 60,0 % | 65,0 % | — |
| **Urgences critiques détectées** | 66,7 % (4/6) | **100 % (6/6)** | **100 %** |
| Urgences sous-estimées | 6 | 4 | 0 |
| Bonne destination (atelier) | — | 97,5 % | — |
| Temps moyen par message | 5,9 s | 5,6 s (CPU, sans GPU) | — |

Les garde-fous en code garantissent la détection des urgences critiques, y compris face à une tentative d'injection de prompt.

### Brouillons de réponse

Évaluation de la phrase écrite par l'IA sur les mêmes 40 messages (`uv run python -m scripts.evaluate_brouillons`) : contrôles automatiques **et** relecture humaine.

| Version | Conformes (contrôles auto) | Vraiment bonnes (relecture) | Temps moyen |
|---|---|---|---|
| qwen2.5:3b, prompt v2 | 22 % | ≈ 5/40 | 2,2 s |
| qwen2.5:3b, prompt v3 | 68 % | ≈ 15/40 | 2,5 s |
| **qwen2.5:7b, prompt v3** | **82 %** | **≈ 24/40** | 6,1 s |

Un enseignement clé : une première version des contrôles automatiques annonçait 85 % de phrases conformes alors que la relecture en trouvait très peu de bonnes. **Une métrique doit toujours être confrontée à une lecture humaine.** Prochaine étape : détecter les faits inventés (« atelier fermé aujourd'hui », « pièce disponible »…).

---

## Lancer le projet (état actuel)

**Prérequis :** [Python 3.13](https://www.python.org/), [uv](https://docs.astral.sh/uv/) et, en option, [Ollama](https://ollama.com/).

```bash
# 1. Installer les dépendances
uv sync

# 2. Créer la configuration locale
cp .env.example .env        # Windows : copy .env.example .env

# 3. (Optionnel) Télécharger les modèles d'IA locaux
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b

# 4. Lancer l'API
uv run fastapi dev app/main.py
```

Puis ouvrir http://127.0.0.1:8000/docs pour la documentation interactive.

Sans Ollama, mettre `AI_PROVIDER=fake` dans `.env` : l'application fonctionne avec des réponses simulées.

**Lancer les tests et les évaluations :**

```bash
uv run pytest -v
uv run python -m scripts.evaluate              # classement des 40 messages
uv run python -m scripts.evaluate_brouillons   # qualité des brouillons
```

---

## Structure

```
assistant-tri/
├── app/
│   ├── main.py                  # application FastAPI
│   ├── config.py                # réglages lus depuis .env
│   ├── schemas.py               # contrats de données (Pydantic)
│   └── services/
│       ├── ai_client.py         # AIProvider, FakeProvider, OllamaProvider, prompts
│       ├── triage.py            # IA + garde-fous : alertes, masquage, routage
│       └── brouillons.py        # brouillons de réponse et leurs contrôles
├── data/eval/
│   ├── messages.jsonl           # 40 messages de test annotés
│   ├── resultats/               # rapports d'évaluation du classement
│   └── brouillons/              # rapports et grilles de notation des brouillons
├── scripts/
│   ├── essai_ollama.py          # essai rapide du classement
│   ├── essai_brouillon.py       # essai rapide des brouillons
│   ├── evaluate.py              # évaluation du classement
│   └── evaluate_brouillons.py   # évaluation des brouillons
├── tests/                       # tests pytest
├── docs/
│   ├── cadrage.md               # cahier des charges
│   └── evaluation.md            # journal des scores de l'IA
├── .env.example                 # modèle de configuration
└── pyproject.toml
```

---

**Charlotte Queijo**
