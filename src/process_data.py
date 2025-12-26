from pathlib import Path
import pandas as pd
import ast
from sklearn.cluster import KMeans

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_PATH = BASE_DIR /"data" /"raw"/"remote_jobs.csv"
OUT_PATH = BASE_DIR /"data" / "processed" / "data_clean.csv"
RUN_DELTA_PATH = BASE_DIR / "data" / "processed" / "run_job_info.csv"

def load_raw(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")
    return pd.read_csv(path)

# cleaning
def dedupe_latest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the most recent record per job URL.
    """
    df = df.sort_values("scraped_at")
    return df.drop_duplicates(subset=["url"], keep="last")



def normalize_location(df: pd.DataFrame) -> pd.DataFrame:
    df["location"] = df["location"].fillna("Remote")
    df.loc[
        df["location"].str.contains("Remote", case=False, na=False),
        "location"
    ] = "Remote"
    return df

def parse_tags(df: pd.DataFrame) -> pd.DataFrame:
    df["tags_list"] = df["tags"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )
    return df

#  Feature engineering
def assign_job_family(df: pd.DataFrame, n_clusters: int = 8) -> pd.DataFrame:
    """
    Cluster jobs into families using tag frequency vectors.
    """
    exploded = df.explode("tags_list")
    tag_matrix = (
        exploded
        .groupby(["url", "tags_list"])
        .size()
        .unstack(fill_value=0)
    )

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    clusters = kmeans.fit_predict(tag_matrix)

    cluster_df = pd.DataFrame({
        "url": tag_matrix.index,
        "cluster_id": clusters
    })

    cluster_map = {
        0: "Data & AI",
        1: "Full Stack",
        2: "Backend/Core",
        3: "Product",
        4: "DevOps",
        5: "Growth/Ops",
        6: "Research/Specialized",
        7: "Security",
    }

    cluster_df["job_family"] = cluster_df["cluster_id"].map(cluster_map)

    return df.merge(cluster_df[["url", "job_family"]], on="url", how="left")

# Validation
def validate(df: pd.DataFrame):
    required = {
        "title", "company", "location",
        "tags", "tags_list", "job_family", "url",
        "scraped_at"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if len(df) == 0:
        raise ValueError("Processed dataset is empty")
    
# Pipeline
def process_pipeline() -> pd.DataFrame:
    df = load_raw(RAW_PATH)
    df = parse_tags(df)
    df = normalize_location(df)
    df = dedupe_latest(df)
    df = assign_job_family(df)
    validate(df)
    return df

# Save
def save(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


#  Run job information
def compute_run_job_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each scrape run, compute how many jobs are new vs previously seen.
    """
    # Ensure correct ordering
    df = df.sort_values("scraped_at")

    seen_urls = set()
    records = []

    for run_id, run_df in df.groupby("run_id", sort=False):
        urls = set(run_df["url"])
        new_jobs = urls - seen_urls
        existing_jobs = urls & seen_urls

        records.append({
            "run_id": run_id,
            "scraped_at": run_df["scraped_at"].iloc[0],
            "total_jobs": len(urls),
            "new_jobs": len(new_jobs),
            "existing_jobs": len(existing_jobs),
        })

        seen_urls |= urls

    return pd.DataFrame(records)

def save_processed(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

if __name__ == "__main__":
    raw_df = load_raw(RAW_PATH)

    # Existing pipeline
    df = process_pipeline()
    save(df, OUT_PATH)
    print(f"Processed {len(df)} jobs -> {OUT_PATH}")

    # New run-delta artifact
    run_deltas = compute_run_job_deltas(raw_df)
    save_processed(run_deltas, RUN_DELTA_PATH)
    print(f"Saved run deltas -> {RUN_DELTA_PATH}")



