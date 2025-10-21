# Rapport de validation — Accès direct & fidélité

- **Format** : `overflow`
- **n** : 300000
- **Échantillons get()** : 100000
- **Verdict** : **OK ✅**

## Résultats
- Mismatches `get(i)` : **0** / 100000
- Mismatches `decompress` : **0** / 300000

## Tailles
- Taille brute (bits) : 9600000
- Taille compressée (bits) : 3006240
- **Ratio** (comp/brut) : **0.3131**

## Temps (ns)
- `T_comp` médian (1 run) : 540185900
- `T_decomp` (1 run) : 185580200
- `T_get` moyen (ns/accès) : 801.3

## Interprétation
- L’accès direct `get(i)` restitue exactement les valeurs d’origine (0 erreur sur l’échantillon).
- La décompression retrouve le tableau complet à l’identique (0 erreur).
- Conclusion : **aucune perte d’accès ni de fidélité introduite par la compression**.
