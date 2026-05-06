from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MLRUNS_DIR = BASE_DIR / "mlruns"
MODEL_REGISTRY_DIR = BASE_DIR / "model_registry"
RANDOM_SEED = 42

