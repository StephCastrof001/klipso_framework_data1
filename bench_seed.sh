#!/bin/bash
# ============================================================================
# bench_seed.sh — Llena bench_queue/ con datasets curados + answer keys
# ============================================================================
# Baja CSVs de GitHub raw, los convierte a utf-8, y escribe
# el answer key (ground truth) de cada uno. Corre una vez; agrega más datasets
# editando la lista DATASETS.
# ============================================================================
set -uo pipefail

# Ensure we are running from the project root
cd "$(dirname "$0")" || exit 1
QUEUE="./bench_queue"
mkdir -p "$QUEUE"

fetch() {  # $1=name $2=url
    local name="$1" url="$2" tmp="$QUEUE/$1.raw"
    echo "→ fetch $name"
    curl -sL -o "$tmp" "$url" || { echo "  fallo $name"; return; }
    
    # Check if the file is empty or not downloaded correctly
    if [ ! -s "$tmp" ]; then
        echo "  fallo $name (archivo vacio)"
        rm -f "$tmp"
        return
    fi
    
    # normalizar encoding a utf-8 (datasets vienen en latin-1 a veces)
    iconv -f UTF-8 -t UTF-8 "$tmp" >/dev/null 2>&1 \
        && mv "$tmp" "$QUEUE/$name.csv" \
        || { iconv -f LATIN1 -t UTF-8 "$tmp" > "$QUEUE/$name.csv" && rm -f "$tmp"; }
    echo "  ok: $(wc -l < "$QUEUE/$name.csv") filas"
}

# --- Lista Maestra de Datasets (15 datasets diversos) ---
DATASETS=(
  # Base 3
  "iris|https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
  "titanic|https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv"
  
  # Nuevos 12
  "mpg|https://raw.githubusercontent.com/mwaskom/seaborn-data/master/mpg.csv"
  "tips|https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv"
  "penguins|https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv"
  "planets|https://raw.githubusercontent.com/mwaskom/seaborn-data/master/planets.csv"
  "winequality_red|https://raw.githubusercontent.com/jbrownlee/Datasets/master/winequality-red.csv"
  "insurance|https://raw.githubusercontent.com/dsrscientist/dataset1/master/medical_insurance.csv"
  "caschools|https://vincentarelbundock.github.io/Rdatasets/csv/AER/CASchools.csv"
  "prestige|https://vincentarelbundock.github.io/Rdatasets/csv/carData/Prestige.csv"
  "gapminder|https://vincentarelbundock.github.io/Rdatasets/csv/causaldata/gapminder.csv"
  "student_perf|https://raw.githubusercontent.com/dsrscientist/dataset1/master/StudentsPerformance.csv"
  "affairs|https://vincentarelbundock.github.io/Rdatasets/csv/AER/Affairs.csv"
  "climate_temp|https://raw.githubusercontent.com/jbrownlee/Datasets/master/monthly-mean-temp.csv"
  "credit_risk|https://raw.githubusercontent.com/jbrownlee/Datasets/master/german.csv"
)

for ds in "${DATASETS[@]}"; do
    IFS="|" read -r name url <<< "$ds"
    fetch "$name" "$url"
done

# --- Answer keys para los nuevos (Ground Truth) ---
cat > "$QUEUE/mpg.key.md" << 'KEY'
1. weight y mpg tienen correlacion NEGATIVA fuerte (r~-0.83)
2. horsepower correlaciona negativo con mpg (r~-0.78)
3. Regresion continua, automoviles.
KEY

cat > "$QUEUE/tips.key.md" << 'KEY'
1. total_bill y tip tienen correlacion POSITIVA (r~0.68)
2. size influye positivamente en tip.
KEY

cat > "$QUEUE/penguins.key.md" << 'KEY'
1. flipper_length y body_mass correlacion POSITIVA fuerte (r~0.87)
2. species separa clusters claramente.
KEY

cat > "$QUEUE/planets.key.md" << 'KEY'
1. orbital_period correlaciona POSITIVO con distance (Tercera Ley de Kepler)
2. Astronomia, datos fisicos reales.
KEY

cat > "$QUEUE/winequality_red.key.md" << 'KEY'
1. alcohol y quality correlacion POSITIVA
2. volatile_acidity correlaciona NEGATIVA
3. Nota: el separador original es punto y coma (;)
KEY

cat > "$QUEUE/insurance.key.md" << 'KEY'
1. smoker domina la prediccion de charges (gastos medicos)
2. age y bmi tienen correlaciones positivas con charges.
KEY

cat > "$QUEUE/caschools.key.md" << 'KEY'
1. lunch (% pobreza) correlacion NEGATIVA fuerte con math scores.
2. student-teacher ratio correlacion NEGATIVA con scores.
KEY

cat > "$QUEUE/prestige.key.md" << 'KEY'
1. education y prestige correlacion POSITIVA fuerte (r~0.85)
2. income tambien influye positivamente.
KEY

cat > "$QUEUE/gapminder.key.md" << 'KEY'
1. gdpPercap (log) correlaciona POSITIVA con lifeExp.
2. year correlaciona POSITIVA con lifeExp (tendencia temporal).
KEY

cat > "$QUEUE/student_perf.key.md" << 'KEY'
1. reading_score correlaciona POSITIVA muy fuerte con math_score (r~0.82)
KEY

cat > "$QUEUE/affairs.key.md" << 'KEY'
1. rating (satisfaccion) correlaciona NEGATIVA fuerte con affairs.
KEY

cat > "$QUEUE/climate_temp.key.md" << 'KEY'
1. Tendencia temporal positiva (calentamiento global medible).
KEY

cat > "$QUEUE/credit_risk.key.md" << 'KEY'
1. duration correlaciona POSITIVA con el riesgo (malo).
2. age correlaciona INVERSAMENTE con riesgo.
KEY

echo "=== bench_queue actualizado con 14 datasets ==="
ls -la "$QUEUE"
