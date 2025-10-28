Aurélien JANTROY-BUZENAC

Implémentation Python de Bit Packing pour compresser des tableaux d’entiers sans perdre l’accès direct au i-ème élément.

Variantes :

crossing — densité maximale, chevauchement possible sur 2 mots de 32 bits

aligned — aucun chevauchement (plus simple/rapide, un peu moins compact)

overflow — petites valeurs inlines + zone de débordement pour outliers

## Installation (Windows / PowerShell)
# 1 créer l’environnement virtuel
py -3 -m venv .venv

# 2 autoriser l’activation pour cette session (si nécessaire)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3 activer l’environnement
.\.venv\Scripts\Activate.ps1

# 4 outils utiles
python -m pip install --upgrade pip
python -m pip install pytest ruff

## Générer un petit jeu de test (6 entiers)
python make_tiny.py

# COMPRESSION
python -m bitpack.cli compress --input tiny_u32.bin --format crossing --out tiny_cross.bp

# ACCÈS DIRECT au 4e élément (index 3) → attendu : 4095
python -m bitpack.cli get --file tiny_cross.bp --format crossing --index 3

# DÉCOMPRESSION
python -m bitpack.cli decompress --file tiny_cross.bp --format crossing --out tiny_cross_out.bin

## Générer un dataset plus gros (200k valeurs)

python make_data.py

Toutes les commandes s’exécutent ainsi :
python -m bitpack.cli <commande> [options...]

compress
python -m bitpack.cli compress --input data.bin --format crossing|aligned|overflow --out data.bp

get
python -m bitpack.cli get --file data.bp --format crossing|aligned|overflow --index 123

decompress
python -m bitpack.cli decompress --file data.bp --format crossing|aligned|overflow --out data_out.bin


## Benchmarks (performance + rentabilité)

La commande bench :

génère les données (ou lit un fichier),

mesure T_comp, T_decomp, T_get,

calcule T_no (sans compression) vs T_yes (avec compression) selon latence/bande passante,

affiche un résumé et peut écrire un CSV.

Exemples
# crossing + uniforme (k=12, n=200k)
python -m bitpack.cli bench --format crossing --scenario uniform --n 200000 --k 12 --warmups 3 --repeats 7 --get-samples 100000 --latency-ms 30 --bandwidth-mbps 10 --csv bench_crossing_uniform_k12.csv

# aligned + uniforme (k=12, n=200k)
python -m bitpack.cli bench --format aligned --scenario uniform --n 200000 --k 12 --warmups 3 --repeats 7 --get-samples 100000 --latency-ms 30 --bandwidth-mbps 10 --csv bench_aligned_uniform_k12.csv

# overflow + skewed (0.1% grosses valeurs)
python -m bitpack.cli bench --format overflow --scenario skewed --n 300000 --k-small 6 --k-large 20 --ratio-large 0.001 --warmups 3 --repeats 7 --get-samples 100000 --latency-ms 50 --bandwidth-mbps 5 --csv bench_overflow_skewed.csv


Sortie attendue : tailles brutes/comp., ratio, temps, Gain (positif = compression bénéfique).

## Validation (preuve d’accès direct & fidélité)

La commande validate exécute :

1 compression,

M accès aléatoires get(i) et compte les erreurs (doit être 0),

1 décompression totale et compare au tableau d’origine (erreurs = 0),

écrit un rapport Markdown.

# crossing + uniform
python -m bitpack.cli validate --format crossing --scenario uniform --n 200000 --k 12 --samples 10000 --report validation_crossing.md

# aligned + uniform
python -m bitpack.cli validate --format aligned --scenario uniform --n 200000 --k 12 --samples 10000 --report validation_aligned_uniform.md

# overflow + skewed
python -m bitpack.cli validate --format overflow --scenario skewed --n 300000 --k-small 6 --k-large 20 --ratio-large 0.001 --samples 100000 --report validation_overflow_skewed.md


Le .md contient : mismatches get/decompress = 0, tailles, ratio, temps → preuve que l’accès direct est conservé et que la décompression est fidèle.

## Tests unitaires

Les tests sont dans tests/ :

test_core.py : primitives bit à bit

test_crossing.py, test_aligned.py, test_overflow.py : API par variante

test_serialization.py : sérialisation binaire (entête, reconstruction)

Exécuter tous les tests :

pytest -q


Sortie typique : ........... [100%]

## Fichiers CSV de benchmarks

Chaque exécution de la commande `bench` produit un fichier `.csv` contenant les mesures détaillées :

- `bench_crossing_uniform_k12.csv`
- `bench_aligned_uniform_k12.csv`
- `bench_overflow_skewed.csv`

Chaque CSV comprend :
- la taille brute et compressée (bits),
- le ratio de compression,
- les temps `T_comp`, `T_decomp`, `T_get`,
- la latence, la bande passante et le gain total (en millisecondes).

## Cartographie des fichiers (bitpack/)

base.py — Contrat d’interface.
Définit le Protocol BitPacking (méthodes compress, decompress, get) pour garantir une API uniforme entre crossing, aligned et overflow.

core.py — Primitives bit à bit.
Constantes (WORD_BITS=32, U32_MASK), utilitaires (mask, ceil_div, bits_needed_unsigned) et E/S bas niveau sur flux de bits (read_bits, write_bits) en ordre LSB-first sur mots 32 bits. C’est la “boîte à outils” commune des formats.

header.py — Sérialisation auto-descriptive.
La dataclass PackedData contient les mots compressés et les méta‐données (n, k, cap, k′, p, k_over, tailles…). to_bytes()/from_bytes() sérialisent un en-tête fixe de 13×u32 (52 octets) suivi du corps (mots 32 bits, little-endian). Définit aussi KIND_CROSSING/ALIGNED/OVERFLOW.

factory.py — Fabrique de compresseurs.
create(kind) retourne l’implémentation adaptée (BitPackingCrossing, BitPackingAligned, BitPackingOverflow) à partir d’une chaîne ("crossing" | "aligned" | "overflow").

crossing.py — Bit packing avec chevauchement.
Compacte au maximum : chaque valeur sur k bits est posée à la suite dans le flux, et peut déborder sur deux mots consécutifs (écritures/lectures via write_bits/read_bits). get(i) recalcule l’offset global i*k.

aligned.py — Bit packing sans chevauchement.
Plus simple et rapide : les valeurs sont alignées par mots, avec une capacité cap = 32//k valeurs par mot. get(i) accède au mot i//cap puis décale de (i%cap)*k. À privilégier quand la vitesse prime sur le ratio.

overflow.py — Slots compacts + zone de débordement.
Choisit un k′ pour encoder en ligne la majorité (slot de taille s = 1 + max(k′, p) où 1 bit = flag), et envoie les rares outliers vers une zone overflow encodée sur k_over bits. Les tailles main_bits et over_bits sont stockées pour un accès direct aux valeurs externalisées. Idéal si la distribution est très asymétrique.

scenarios.py — Générateurs de jeux de données.
uniform_u32(n,k) (valeurs sur k bits) et skewed(n,k_small,k_large,ratio) (majorité petites, rares grandes). Utilisé par les commandes bench et validate.

timing.py — Bancs de mesure & modèles de temps.
bench_pack mesure T_comp, T_decomp, T_get (médiane, moyenne, σ) avec warm-ups. Fournit aussi total_time_without_compression, total_time_with_compression, compression_ratio, ns_to_s. Sert à calculer T_no vs T_yes et le Gain.

validate.py — Preuve d’accès direct & fidélité.
validate_access compresse, échantillonne get(i) (comptage d’erreurs), décompresse et compare end-to-end. render_markdown_report produit un rapport .md (mismatches, tailles, ratios, temps) à archiver dans le dépôt.

cli.py — Interface en ligne de commande.
Sous-commandes :
compress (fichier u32 → .bp), get (lecture directe), decompress (.bp → fichier u32), bench (mesures + CSV), validate (rapport .md). Prend en charge données depuis fichier ou générées (uniform/skewed).


Auteur : Aurelien JANTROY BUZENAC
