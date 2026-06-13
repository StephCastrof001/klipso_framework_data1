#!/bin/bash
# ============================================================================
# bench_seed.sh — Llena bench_queue/ con datasets curados + answer keys
# ============================================================================
# Baja CSVs de GitHub raw (sin Kaggle API), los convierte a utf-8, y escribe
# el answer key (ground truth) de cada uno. Corre una vez; agrega más datasets
# editando la lista DATASETS.
# ============================================================================
set -uo pipefail
QUEUE="$HOME/klipso_framework_data1/bench_queue"
mkdir -p "$QUEUE"

fetch() {  # $1=name $2=url
    local name="$1" url="$2" tmp="$QUEUE/$1.raw"
    echo "→ fetch $name"
    curl -sL -o "$tmp" "$url" || { echo "  fallo $name"; return; }
    # normalizar encoding a utf-8 (datasets vienen en latin-1 a veces)
    iconv -f UTF-8 -t UTF-8 "$tmp" >/dev/null 2>&1 \
        && mv "$tmp" "$QUEUE/$name.csv" \
        || { iconv -f LATIN1 -t UTF-8 "$tmp" > "$QUEUE/$name.csv" && rm -f "$tmp"; }
    echo "  ok: $(wc -l < "$QUEUE/$name.csv") filas"
}

# --- Datasets curados (GitHub raw, estables) ---
fetch spotify-2023 "https://raw.githubusercontent.com/draemonsi/exploratory-data-analysis-on-spotify-2023-dataset/main/spotify-2023.csv"
fetch titanic      "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
fetch iris         "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"

# --- Answer keys (ground truth documentado) ---
cat > "$QUEUE/spotify-2023.key.md" << 'KEY'
# Answer key — Spotify 2023 (ref: draemonsi EDA, 8 stars)
1. 953 filas, 24 columnas; nulls en 'key' e 'in_shazam_charts'
2. Top track: The Weeknd "Blinding Lights" 3.70B > Ed Sheeran "Shape of You" 3.56B
3. Releases pico 2022; meses pico ene + may 2023
4. CORRELACION: danceability/speechiness correlacion NEGATIVA con streams; acousticness la mas debil
5. Plataformas: Spotify playlists mas grandes/variadas; Apple mas curado
6. Tonalidad: claves menores (E minor, A minor) superan a mayores
7. Artista mas playlisteado: The Weeknd
KEY

cat > "$QUEUE/titanic.key.md" << 'KEY'
# Answer key — Titanic (canonico, textbook)
1. Sexo = predictor #1 de supervivencia (mujeres sobreviven mucho mas)
2. Clase importa: 1ra clase sobrevive mas que 3ra
3. Niños tienen mayor tasa de supervivencia
4. Tarifa (fare) correlaciona positivo con supervivencia
5. ~38% sobrevivieron del total
KEY

cat > "$QUEUE/iris.key.md" << 'KEY'
# Answer key — Iris (canonico, textbook)
1. 150 filas, 3 especies (50 c/u), 4 features numericas
2. Setosa linealmente separable de las otras dos
3. Petal length y petal width son los mejores discriminadores
4. Versicolor y virginica se solapan parcialmente
5. Petal length/width fuertemente correlacionados entre si
KEY

echo "=== bench_queue lleno ==="
ls -la "$QUEUE"
