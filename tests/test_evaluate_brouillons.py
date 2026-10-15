from scripts.evaluate_brouillons import calculer_metriques, controler_accroche


def test_phrase_conforme():
    defauts = controler_accroche(
        "Nous comprenons votre inquiétude au sujet de votre batterie qui chauffe.",
        "Ma batterie chauffe pendant la charge.",
        "batterie",
    )
    assert defauts == []


def test_sujet_ajoute_et_formule_inadaptee():
    # Cas réel : l'IA a parlé de « facture » à un client qui n'en parlait pas.
    defauts = controler_accroche(
        "Nous comprenons votre inquiétude concernant votre facture.",
        "Remboursez-moi immédiatement sur ma carte [CARTE MASQUÉE].",
        "reclamation",
    )
    assert any("sujet ajouté" in d and "factur" in d for d in defauts)
    assert any("formule inadaptée" in d for d in defauts)


def test_information_donnee():
    defauts = controler_accroche(
        "Oui, nous avons des sacoches à 30 €.",
        "Vendez-vous des sacoches ?",
        "avant_achat",
    )
    assert "information donnée" in defauts


def test_mise_en_forme_detectee():
    defauts = controler_accroche(
        "**Merci** pour votre question.", "Question ?", "autre"
    )
    assert "mise en forme" in defauts


def test_metriques_comptent_les_conformes():
    resultats = [
        {"accroche": "Merci.", "defauts": [], "duree": 1.0},
        {"accroche": "x", "defauts": ["sujet ajouté : factur"], "duree": 1.0},
    ]
    m = calculer_metriques(resultats)
    assert m["conformes"] == 1
    assert m["defauts_par_type"] == {"sujet ajouté": 1}


def test_engagement_et_je_detectes():
    # Cas réel (#27) : l'IA promet un remboursement et parle en « je ».
    defauts = controler_accroche(
        "Je comprends votre gêne, nous allons vérifier et vous rembourser le doublon.",
        "J'ai été prélevé deux fois pour ma commande.",
        "commande",
    )
    assert "parle en « je »" in defauts
    assert any("engagement pris" in d for d in defauts)
