from scripts.evaluate import calculer_metriques


def _resultat(attendu: str, obtenu: str | None) -> dict:
    """Fabrique un faux résultat ne portant que sur l'urgence."""
    reponse = None
    if obtenu is not None:
        reponse = {"categorie": "panne", "urgence": obtenu, "atelier": None}
    return {
        "attendu": {"categorie": "panne", "urgence": attendu, "atelier": None},
        "obtenu": reponse,
        "duree": 1.0,
    }


def test_haute_classee_normale_est_sous_estimee():
    m = calculer_metriques([_resultat("haute", "normale")])
    assert m["sous_estimees"] == 1
    assert m["sur_estimees"] == 0


def test_basse_classee_normale_est_surestimee():
    m = calculer_metriques([_resultat("basse", "normale")])
    assert m["sur_estimees"] == 1


def test_critique_en_erreur_compte_comme_ratee():
    m = calculer_metriques([_resultat("critique", None)])
    assert m["rappel_critique"] == 0.0
    assert m["erreurs"] == 1