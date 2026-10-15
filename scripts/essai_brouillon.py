import time

from app.services.ai_client import get_provider
from app.services.brouillons import generer_brouillon
from app.services.triage import trier

MESSAGES = [
    "Bonjour, ma batterie dégage une odeur bizarre et chauffe pendant la charge.",
    "Je voudrais savoir si vous vendez des sacoches pour porte-bagages.",
    "Ça fait 3 semaines que j'attends mon vélo réparé, personne ne me rappelle !",
    "Remboursez-moi immédiatement sur ma carte 4970 1234 5678 9012.",
]

provider = get_provider()
for message in MESSAGES:
    debut = time.perf_counter()
    triage = trier(message, provider)
    brouillon = generer_brouillon(message, triage, provider)
    duree = time.perf_counter() - debut

    print("\n" + "=" * 70)
    print(f"[{duree:.1f} s] {message}")
    print(f"→ {triage.categorie} / {triage.urgence} / {triage.atelier_destination}")
    print("-" * 70)
    print(brouillon.texte)
    for alerte in brouillon.alertes:
        print(f"⚠️  {alerte}")
