from app.schemas import Categorie, Urgence
from app.services.ai_client import FakeProvider


def test_fake_message_normal():
    analyse = FakeProvider().analyser("Bonjour, quels sont vos horaires ?")
    assert analyse.urgence == Urgence.NORMALE
    assert analyse.categorie == Categorie.AUTRE


def test_fake_fumee_critique():
    analyse = FakeProvider().analyser("Ma batterie FUME depuis ce matin !")
    assert analyse.urgence == Urgence.CRITIQUE
    assert analyse.categorie == Categorie.BATTERIE


def test_fake_resume_tronque_a_100_caracteres():
    analyse = FakeProvider().analyser("a" * 300)
    assert len(analyse.resume) == 100