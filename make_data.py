"""
make_data.py — génère un fichier binaire de test 'data.bin'
dans le dossier courant, contenant 200 000 entiers non signés
sur 32 bits (u32) choisis uniformément sur k bits (ici 12).
"""

import random

# paramètres
n = 200_000   # nombre d'entiers
k = 12        # nombre de bits significatifs
random.seed(123)  # pour un résultat reproductible

with open("data.bin", "wb") as f:
    for _ in range(n):
        x = random.randrange(0, 1 << k)
        f.write((x & 0xFFFFFFFF).to_bytes(4, "little"))

print("✅  data.bin créé :", n, "valeurs (≈", n*4//1024, "Ko )")
