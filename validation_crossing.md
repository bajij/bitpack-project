# Rapport de validation — Accès direct & fidélité

- **Format** : `crossing`
- **n** : 200000
- **Échantillons get()** : 10000
- **Verdict** : **OK ✅**

## Résultats
- Mismatches `get(i)` : **0** / 10000
- Mismatches `decompress` : **0** / 200000

## Tailles
- Taille brute (bits) : 6400000
- Taille compressée (bits) : 2400416
- **Ratio** (comp/brut) : **0.3751**

## Temps (ns)
- `T_comp` médian (1 run) : 85897800
- `T_decomp` (1 run) : 81176100
- `T_get` moyen (ns/accès) : 697.2

## Interprétation
- L’accès direct `get(i)` restitue exactement les valeurs d’origine (0 erreur sur l’échantillon).
- La décompression retrouve le tableau complet à l’identique (0 erreur).
- Conclusion : **aucune perte d’accès ni de fidélité introduite par la compression**.
