# Fiche projet — Assistant IA de tri des demandes clients

*9 oct. 2026 · @Charlotte Queijo*

## Sommaire

1. [Contexte client](#1-contexte-client)
2. [Objectifs et périmètre](#2-objectifs-et-périmètre)
3. [Fonctionnalités attendues](#3-fonctionnalités-attendues)
4. [Stack technique et architecture](#4-stack-technique-et-architecture)
5. [Intégration IA](#5-intégration-ia)
6. [Modèle de données](#6-modèle-de-données)
7. [Charte graphique du front](#7-charte-graphique-du-front)
8. [Planning, livrables et recette](#8-planning-livrables-et-recette)
9. [Décisions métier](#9-décisions-métier)

---

## 1. Contexte client

Le client Cycles Mistral veut une application web qui trie automatiquement ses demandes clients grâce à l'IA.

### Qui est le client

Cycles Mistral est un réseau de 6 ateliers de réparation et de vente de vélos électriques, basé à Lyon.
Interlocutrice : **Mme Sofia Benali**, responsable du service après-vente (SAV).

### Son problème

Le SAV reçoit environ **250 messages par semaine** (formulaire du site + e-mails). Deux personnes passent près de **12 heures par semaine** à les lire, les classer et les transférer au bon atelier. Les demandes urgentes (vélo en panne, batterie qui chauffe) se perdent parfois au milieu des questions simples.

### Ce qu'elle a demandé, avec ses mots

> « Je veux ouvrir un écran le matin et voir tout de suite ce qui est urgent, de quoi parle chaque message, et avoir un brouillon de réponse prêt à relire. »

### Contrainte majeure

**Budget 0 €.** Ce projet est destiné à mon portfolio. Le client est fictif, et chaque outil, service ou modèle utilisé doit être gratuit et, autant que possible, open source. Aucune carte bancaire ne doit être demandée à l'installation.

---

## 2. Objectifs et périmètre

**Objectif chiffré :** faire passer le temps de tri du SAV de **12 h à moins de 3 h par semaine**, sans qu'**aucune demande urgente ne reste plus de 2 h sans être vue**.

| ✅ Dans le périmètre | ❌ Hors périmètre |
|---|---|
| Saisie des demandes par un formulaire web public | Lecture automatique de la boîte e-mail (phase 2) |
| Analyse IA de chaque demande : catégorie, urgence, résumé, atelier | Envoi automatique des réponses au client |
| Tableau de bord du SAV avec filtres et tri | Application mobile |
| Brouillon de réponse généré par l'IA, modifiable | Paiement, facturation, prise de rendez-vous |
| Connexion des agents SAV (comptes simples) | Gestion fine des droits par atelier |
| Statistiques simples de la semaine | Entraînement d'un modèle d'IA maison |

> **Règle d'or :** l'IA propose, l'humain décide.
> Aucune réponse ne part au client sans validation d'un agent.

---

## 3. Fonctionnalités attendues

Les priorités suivent la méthode **MoSCoW** : **M** = obligatoire pour la livraison, **S** = devrait y être, **C** = bonus si le temps le permet.

| N° | User story | Priorité |
|---|---|:---:|
| F1 | En tant que client, je remplis un formulaire (nom, e-mail, atelier si connu, n° de commande optionnel, message) et je reçois un numéro de suivi. | M |
| F2 | En tant que système, j'analyse chaque nouvelle demande avec l'IA dès sa réception et j'enregistre le résultat. | M |
| F3 | En tant qu'agent SAV, je me connecte avec e-mail + mot de passe. | M |
| F4 | En tant qu'agent, je vois la liste des demandes triée par urgence puis par date, avec des badges de couleur. | M |
| F5 | En tant qu'agent, je filtre par catégorie, atelier, statut et urgence, et je cherche par mot-clé. | M |
| F6 | En tant qu'agent, j'ouvre une demande et je vois le message, le résumé IA, la catégorie, l'urgence et la justification. | M |
| F7 | En tant qu'agent, je corrige la catégorie ou l'urgence proposée par l'IA ; la correction est enregistrée. | M |
| F8 | En tant qu'agent, je génère un brouillon de réponse, je le modifie et je le marque « envoyé ». | S |
| F9 | En tant qu'agent, je change le statut : Nouveau → En cours → Traité. | S |
| F10 | En tant que responsable, je vois les statistiques de la semaine : volume par catégorie, par urgence, taux de correction de l'IA. | S |
| F11 | En tant qu'agent, le brouillon s'appuie sur la FAQ officielle de Cycles Mistral (10 questions fournies). | C |
| F12 | En tant qu'agent, j'exporte la liste filtrée en CSV. | C |

### Catégories fixées avec le client

Panne / réparation · Batterie · Garantie · Commande / livraison · Question avant achat · Réclamation · Autre

### Niveaux d'urgence

| Niveau | Définition |
|---|---|
| **Critique** | Sécurité : batterie qui chauffe, freins |
| **Haute** | Vélo inutilisable |
| **Normale** | Gêne réelle mais vélo utilisable |
| **Basse** | Simple information, aucun problème en cours |

Définitions détaillées et mots-clés d'alerte : voir la [section 9](#9-décisions-métier).

---

## 4. Stack technique et architecture

Tout est en Python, front compris : pas de framework JavaScript, on rend le HTML côté serveur et **HTMX** gère l'interactivité.

| Couche | Outil imposé (gratuit) | Pourquoi |
|---|---|---|
| Langage | Python 3.13 | Standard de l'équipe |
| Gestion du projet | uv + ruff (lint/format) | Installation rapide, code propre |
| API et serveur web | FastAPI | Typage, validation, doc auto sur `/docs` |
| Validation des données | Pydantic v2 | Schémas partagés entre API et IA |
| Pages HTML | Jinja2 + HTMX | Front en Python, mises à jour partielles sans recharger |
| Base de données | SQLite + SQLAlchemy 2 + Alembic | Aucun serveur à payer, migration vers PostgreSQL possible |
| IA | Ollama (modèles open source en local) + bibliothèque Python `ollama` | Gratuit, sans clé d'API, données qui ne quittent pas la machine |
| Mots de passe | pwdlib (Argon2) + session par cookie | Sécurité correcte sans complexité |
| Tests | pytest + httpx | Tests des routes et des services |
| Déploiement | Docker + docker-compose (app + Ollama) | Le recruteur lance tout avec une seule commande |
| Code et démo | GitHub (dépôt public) + README avec captures et GIF | Vitrine du portfolio |

### Organisation du code attendue

```text
mistral_sav/
  app/
    main.py          # création de l'app FastAPI
    config.py        # variables d'environnement (pydantic-settings)
    db.py            # moteur et session SQLAlchemy
    models.py        # tables
    schemas.py       # schémas Pydantic
    routers/         # public.py, agent.py, stats.py, auth.py
    services/        # ai_client.py, triage.py, drafts.py
    templates/       # pages Jinja2
    static/          # css/, img/
  tests/
  alembic/
  Dockerfile
  docker-compose.yml
  pyproject.toml
  .env.example
```

Les réglages (modèle IA, adresse d'Ollama, secret de session) vivent dans `.env`, **jamais dans le code ni dans Git**. Fournir un `.env.example` rempli avec des valeurs de démo.

---

## 5. Intégration IA

L'IA intervient à deux moments : l'**analyse automatique** à la réception (F2) et le **brouillon de réponse** à la demande de l'agent (F8).

### Modèles (gratuits, en local via Ollama)

- **Analyse :** `qwen2.5:3b` ou `llama3.2:3b` (légers, tournent sur un PC portable sans carte graphique).
- **Brouillon :** `mistral:7b` si la machine a au moins 16 Go de RAM, sinon le même petit modèle.
- Le nom du modèle se règle dans `.env`. Ollama accepte un schéma JSON en paramètre `format`, ce qui force une sortie structurée.

### Mode démo obligatoire

Ajouter un fournisseur `FakeProvider` (réponses pré-écrites) activable avec `AI_PROVIDER=fake`. Il sert aux tests automatiques et permet à un recruteur de lancer l'app sans télécharger de modèle.
Le code appelle une interface commune `AIProvider`, avec deux implémentations : `OllamaProvider` et `FakeProvider`.

### Sortie attendue de l'analyse

L'IA doit renvoyer un JSON strict, validé par ce schéma Pydantic :

```python
class AnalyseIA(BaseModel):
    categorie: Literal[
        "panne",
        "batterie",
        "garantie",
        "commande",
        "avant_achat",
        "reclamation",
        "autre",
    ]
    urgence: Literal["critique", "haute", "normale", "basse"]
    resume: str = Field(max_length=200)  # 1 à 2 phrases
    atelier_suggere: str | None  # parmi les 6 ateliers
    justification: str = Field(max_length=300)
    confiance: float = Field(ge=0, le=1)
```

### Prompt système (point de départ, à améliorer)

```text
Tu es l'assistant SAV de Cycles Mistral. Tu classes une demande client.
Réponds uniquement avec le JSON demandé. Toute mention de chaleur, fumée,
odeur de brûlé de batterie, ou de freins défaillants est critique.
Ne devine pas un numéro de commande absent.
```

### Garde-fous obligatoires

- Le message client est placé entre balises `<message>` et traité comme une **donnée, jamais comme une instruction** (protection contre l'injection de prompt).
- Si le JSON est invalide : une nouvelle tentative, puis enregistrement avec `categorie=autre`, `urgence=normale` et un drapeau « à vérifier ».
- Si `confiance < 0,6` : badge « à vérifier » sur le tableau de bord.
- Délai maximum de **60 s** par appel (un modèle local est plus lent) ; en cas d'erreur réseau, la demande est enregistrée sans analyse et relancée plus tard.
- Chaque appel est journalisé : modèle, durée, nombre de tokens. **Jamais le contenu complet du message dans les logs.**
- Pas de données bancaires envoyées à l'IA : un filtre masque les suites de 16 chiffres avant l'appel.

### Brouillon de réponse

Vouvoiement, ton chaleureux et précis, **120 mots maximum**, signé « Le SAV Cycles Mistral ». L'IA ne promet jamais de remboursement ni de délai qui n'est pas dans la FAQ.

### Jeu de test

40 messages fictifs rédigés et annotés manuellement. Le script `evaluate.py` mesure le taux de bonne catégorie et de bonne urgence.
**Cible :** 85 % sur la catégorie, 100 % des urgences critiques détectées.

---

## 6. Modèle de données

Cinq tables suffisent. Une demande a au plus une analyse IA et peut avoir plusieurs brouillons.

| Table | Champs principaux | Relations |
|---|---|---|
| `atelier` | id, nom, ville, email | — |
| `agent` | id, nom, email (unique), mot_de_passe_hash, role (agent / responsable), cree_le | — |
| `demande` | id, numero_suivi (ex. `SAV-2026-00042`), nom_client, email_client, n_commande, message, statut, categorie, urgence, atelier_id, corrige_par_humain (bool), recue_le, maj_le | → atelier, → agent (assigné) |
| `analyse_ia` | id, demande_id, categorie, urgence, resume, justification, confiance, modele, duree_ms, tokens_entree, tokens_sortie, cree_le | → demande (1–1) |
| `brouillon` | id, demande_id, agent_id, texte_ia, texte_final, envoye (bool), cree_le | → demande, → agent |

> **Important :** `demande.categorie` et `demande.urgence` sont les valeurs **retenues** (IA ou corrigées). `analyse_ia` garde toujours la **proposition d'origine**, ce qui permet de calculer le taux de correction (F10).

---

## 7. Charte graphique du front

L'identité « Cycles Mistral » est sobre et rassurante : un bleu profond pour la confiance, un vert pour l'action, et des couleurs d'urgence qui se lisent d'un coup d'œil. Tout est gratuit : polices Google Fonts (licence OFL), icônes Lucide (licence ISC), pas de bibliothèque CSS payante.

### Palette

| Rôle | Nom | Hex | Usage |
|---|---|---|---|
| Primaire | Bleu Mistral | `#1F4E79` | En-tête, liens, boutons principaux |
| Primaire survol | Bleu nuit | `#163A5B` | Survol et état actif des boutons |
| Accent | Vert vélo | `#1E7A50` | Bouton « Valider », statut « Traité » |
| Fond de page | Brume | `#F6F8FA` | Arrière-plan général |
| Surface | Blanc | `#FFFFFF` | Cartes, tableaux, formulaires |
| Bordure | Gris clair | `#D9E0E7` | Séparateurs, contours des champs |
| Texte | Encre | `#1A1F24` | Texte principal |
| Texte secondaire | Ardoise | `#5B6773` | Dates, aides, libellés |

### Badges d'urgence

Chaque badge = texte foncé sur fond clair de la même teinte, pour un contraste d'au moins 4,5:1 (norme WCAG AA).

| Urgence | Texte | Fond | Icône Lucide |
|---|---|---|---|
| Critique | `#B71C1C` | `#FDECEC` | `alert-octagon` |
| Haute | `#A35400` | `#FFF3E0` | `alert-triangle` |
| Normale | `#1A5A94` | `#E8F1FA` | `info` |
| Basse | `#4A5560` | `#EEF1F4` | `minus-circle` |

La couleur n'est jamais seule : le badge affiche toujours **le mot et l'icône**.

### Typographie

- **Inter** (Google Fonts) pour toute l'interface : 400 normal, 600 titres et boutons.
- **JetBrains Mono** (Google Fonts) pour les numéros de suivi et les extraits techniques.
- Échelle : 12 px (mentions), 14 px (tableaux), 16 px (texte), 20 px (titre de carte), 24 px (titre de page), 32 px (accueil du formulaire public).
- Interlignage : 1,5 pour le texte, 1,2 pour les titres.

### Formes et espacements

- Grille de 4 px : espacements de 4, 8, 12, 16, 24, 32, 48.
- Coins arrondis : 8 px (cartes, boutons, champs), 999 px (badges).
- Ombre unique, discrète, réservée aux cartes : `0 1px 3px rgba(26, 31, 36, 0.08)`.
- Focus clavier visible partout : contour 2 px Bleu Mistral, décalé de 2 px.

### Composants

- **Bouton principal :** fond Bleu Mistral, texte blanc, hauteur 40 px.
- **Bouton secondaire :** fond blanc, bordure Gris clair, texte Bleu Mistral.
- **Bouton de validation :** fond Vert vélo, texte blanc.
- **Champ de formulaire :** hauteur 40 px, bordure Gris clair, bordure Bleu Mistral au focus, message d'erreur en `#B71C1C` sous le champ.
- **Carte « Analyse IA » :** bordure gauche de 4 px Bleu Mistral, petite étiquette « Proposé par l'IA » en Ardoise, pour toujours distinguer ce qui vient de la machine.

### Mise en page

- **Formulaire public :** mobile d'abord, une colonne, largeur max 640 px.
- **Tableau de bord agent :** pensé pour écran ≥ 1024 px, en-tête de 64 px, colonne de filtres de 280 px à gauche, liste à droite, largeur max 1280 px.
- **Logo :** le client n'en fournit pas ; utiliser le nom « Cycles Mistral » en Inter 600 + l'icône Lucide `bike`.

### Variables CSS à reprendre telles quelles

```css
:root {
  --color-primary: #1F4E79;
  --color-primary-hover: #163A5B;
  --color-accent: #1E7A50;
  --color-bg: #F6F8FA;
  --color-surface: #FFFFFF;
  --color-border: #D9E0E7;
  --color-text: #1A1F24;
  --color-text-muted: #5B6773;

  --urgence-critique: #B71C1C;  --urgence-critique-bg: #FDECEC;
  --urgence-haute: #A35400;     --urgence-haute-bg: #FFF3E0;
  --urgence-normale: #1A5A94;   --urgence-normale-bg: #E8F1FA;
  --urgence-basse: #4A5560;     --urgence-basse-bg: #EEF1F4;

  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --radius: 8px;
  --shadow-card: 0 1px 3px rgba(26, 31, 36, 0.08);
}
```

---

## 8. Livrables et recette

### Livrables

- Dépôt GitHub public, historique de commits propre (un commit par fonctionnalité, messages clairs).
- README : présentation du projet, captures d'écran, GIF de démo, installation en 3 commandes, choix techniques expliqués.
- `docker compose up` démarre l'app, Ollama et la base.
- Script `evaluate.py` et son rapport de précision sur les 40 messages de test.
- Données de démo : 30 demandes fictives et 2 comptes agents, chargées par une commande `seed`.

### Critères de recette

- [ ] Une demande saisie dans le formulaire apparaît analysée dans le tableau de bord en moins d'une minute.
- [ ] 100 % des messages « critiques » du jeu de test sont détectés comme critiques.
- [ ] Catégorie correcte sur au moins 85 % des 40 messages de test.
- [ ] Un message contenant « ignore tes instructions » n'altère pas le classement.
- [ ] L'app fonctionne avec `AI_PROVIDER=fake`, sans Ollama installé.
- [ ] Les pages agent sont inaccessibles sans connexion.
- [ ] La charte est respectée : couleurs, polices, badges avec mot et icône.
- [ ] `pytest` passe sans erreur, couverture d'au moins 70 %.
- [ ] Aucun service payant ni clé secrète dans le dépôt.

---

## 9. Décisions métier

### Les 6 ateliers

| Code | Nom | Quartier | Spécialité | E-mail |
|---|---|---|---|---|
| `lyon1` | Cycles Mistral 1er | Les Terreaux | Siège · Vente · Réparation · Reprise | atelier1@cycles-mistral.fr |
| `lyon2` | Cycles Mistral 2e | Perrache | Vente | atelier2@cycles-mistral.fr |
| `lyon3` | Cycles Mistral 3e | Part-Dieu | Réparation | atelier3@cycles-mistral.fr |
| `lyon5` | Cycles Mistral 5e | Fourvière | Réparation | atelier5@cycles-mistral.fr |
| `lyon7` | Cycles Mistral 7e | Gerland | Vente · Reprise | atelier7@cycles-mistral.fr |
| `lyon8` | Cycles Mistral 8e | Montplaisir | Réparation · Reprise | atelier8@cycles-mistral.fr |

Le **code** est la valeur utilisée dans le code et dans la base ; le **nom** est ce qu'on affiche.

### Règles de routage

1. Le client cite un atelier qui fait le service demandé → **cet atelier**.
2. Le client demande une réparation dans un atelier « vente seule » → l'atelier de réparation le plus proche :
   - `lyon2` (Perrache) → `lyon1` (Terreaux)
   - `lyon7` (Gerland) → `lyon8` (Montplaisir)
3. Le client ne cite aucun atelier → **`lyon1`** (le siège), qui redistribue.

### Définition de chaque catégorie

| Catégorie | Définition | Exemples |
|---|---|---|
| `reclamation` | Le client exprime un **mécontentement** sur un service déjà rendu : réparation ratée, délai non tenu, accueil, facture contestée. | « Troisième fois que je reviens pour le même problème », « inadmissible » |
| `garantie` | Le client demande une **prise en charge gratuite** d'un défaut, ou cite explicitement la garantie. | « Est-ce couvert par la garantie ? », « acheté il y a 3 mois, déjà cassé » |
| `batterie` | Tout problème lié à la **batterie ou à la charge** : ne charge plus, autonomie en baisse, chauffe, fume, gonflée. | « Ma batterie ne tient plus que 10 km » |
| `panne` | Problème **mécanique ou électrique hors batterie** : freins, transmission, moteur, crevaison, écran, bruit anormal. | « Mon dérailleur saute », « le moteur ne m'assiste plus » |
| `commande` | Suivi d'une **commande ou livraison** : retard, modification, annulation, colis. | « Où en est ma commande n°123456 ? » |
| `avant_achat` | **Prospect** qui se renseigne avant d'acheter : prix, modèles, essai, reprise de l'ancien vélo, financement. | « Proposez-vous des essais ? » |
| `autre` | **Catégorie de secours** : tout ce qui n'entre dans aucune autre (horaires, recrutement, partenariat, message vide…). | « Êtes-vous ouverts le dimanche ? » |

### Règle de départage

Si un message correspond à plusieurs catégories, on retient **la première** dans cet ordre :

**`reclamation` > `garantie` > `batterie` > `panne` > `commande` > `avant_achat` > `autre`**

*Pourquoi la réclamation en premier :* un client mécontent risque d'être perdu ; Mme Benali doit le voir comme tel, même si son message parle aussi d'une panne.

> La catégorie et l'urgence sont **indépendantes** : une batterie qui fume sous garantie est `garantie` + `critique`. Le danger est porté par l'urgence, pas par la catégorie.

### Niveaux d'urgence

| Niveau | Délai de prise en charge | Définition | Exemples |
|---|---|---|---|
| **Critique** | < 2 h | **Risque pour la sécurité** d'une personne ou d'un bien. | Batterie qui fume ou chauffe, freins qui lâchent, accident, blessure |
| **Haute** | Dans la journée | Le client est **immobilisé** (vélo inutilisable), ou une échéance tombe aujourd'hui, ou réclamation forte. | Vélo qui ne démarre plus, rendez-vous ce matin, menace d'avis négatif |
| **Normale** | Sous 48 h | **Gêne réelle mais vélo utilisable**, ou demande qui attend une action du SAV. | Bruit au pédalage, autonomie en baisse, suivi de commande |
| **Basse** | Sous 1 semaine | **Simple information**, aucun problème en cours. | Horaires, prix, questions avant achat |

> En cas de doute entre deux niveaux, on choisit **le plus élevé** : rater une urgence coûte plus cher qu'une fausse alerte.

### Mots-clés d'alerte (urgence critique forcée)

Ces mots déclenchent l'urgence **critique** quoi que dise l'IA (filet de sécurité). Ils décrivent un **danger**, jamais un simple sujet : « batterie », « moteur » ou « garantie » ne sont **pas** des mots d'alerte.

| Danger | Mots-clés et variantes |
|---|---|
| Feu / chaleur | fumée, fume, fumait, brûlé, brûle, odeur de brûlé, chauffe, surchauffe, brûlant, étincelle, flamme, feu, incendie, fondu |
| Batterie dangereuse | batterie gonflée, batterie déformée, court-circuit, explosé, explosion |
| Freins | plus de frein, freins lâchent, freine plus, freins ne répondent, freins HS |
| Accident | accident, chute, tombé, blessé, blessure, hôpital, urgences |

*En code :* le texte sera mis en minuscules et débarrassé de ses accents avant la recherche, pour que « FUMÉE », « fumee » et « Fumée » soient tous détectés.
