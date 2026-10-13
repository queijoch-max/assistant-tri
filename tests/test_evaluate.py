from scripts.evaluate import calculer_metriques


def _resultat(attendu: str, obtenu: str | None) -> dict:
    """Fabrique un faux résultat ne portant que sur l'urgence."""
    autres = {"categorie": "panne", "atelier": None, "destination": "lyon1"}
    reponse = None
    if obtenu is not None:
        reponse = {**autres, "urgence": obtenu}
    return {
        "attendu": {**autres, "urgence": attendu},
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


def test_critique_sans_reponse_compte_comme_ratee():
    m = calculer_metriques([_resultat("critique", None)])
    assert m["rappel_critique"] == 0.0
