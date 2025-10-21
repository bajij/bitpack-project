# Rapport de validation — Accès direct & fidélité

- **Format** : `aligned`
- **n** : 200000
- **Échantillons get()** : 10000
- **Verdict** : **OK ✅**

## Résultats
- Mismatches `get(i)` : **0** / 10000
- Mismatches `decompress` : **0** / 200000

## Tailles
- Taille brute (bits) : 6400000
- Taille compressée (bits) : 3200416
- **Ratio** (comp/brut) : **0.5001**

## Temps (ns)
- `T_comp` médian (1 run) : 36861100
- `T_decomp` (1 run) : 54460300
- `T_get` moyen (ns/accès) : 515.1

## Interprétation
- L’accès direct `get(i)` restitue exactement les valeurs d’origine (0 erreur sur l’échantillon).
- La décompression retrouve le tableau complet à l’identique (0 erreur).
- Conclusion : **aucune perte d’accès ni de fidélité introduite par la compression**.
