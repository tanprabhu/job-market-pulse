from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time, shutil
import pandas as pd, uuid
from datetime import datetime, timezone
from pathlib import Path
from selenium.webdriver.chrome.options import Options

URL = "https://remoteok.com/?search=engineer"
SCROLL_TIMES = 3
SCROLL_PAUSE = 3

SCRAPE_TIME = datetime.now(timezone.utc).isoformat()

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR.parent / "data" / "raw" / "remote_jobs.csv"
SCRAPE_RUNS_PATH = BASE_DIR.parent / "data" / "meta" / "scrape_runs.csv"

chrome_path = shutil.which("google-chrome") or \
              shutil.which("chrome") or \
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def scrape(run_id:str, headless: bool = True):
    options = Options()
    options.binary_location = chrome_path
    
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(URL)

        last_height = driver.execute_script("return document.body.scrollHeight")

        for _ in range(SCROLL_TIMES):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.find_all("tr", attrs={"data-slug": True})

        print(f"[DEBUG] Parsed {len(rows)} job rows from page")

        job_list = []

        for row in rows:
            company = row.get("data-company")
            job_id = row.get("data-id")

            company_zone = row.find("td", class_="company position company_and_position")
            location_div = (
                company_zone.find("div", class_="location tooltip")
                if company_zone else None
            )
            location = location_div.get("title") if location_div else "Remote"

            tags_td = row.find("td", class_="tags")
            tags = [
                h3.get_text(strip=True)
                for h3 in tags_td.find_all("h3")
            ] if tags_td else []

            title_tag = row.find("h2")
            title = title_tag.get_text(strip=True) if title_tag else None

            job_list.append({
                "run_id": run_id,
                "job_id": job_id,
                "company": company,
                "title": title,
                "location": location,
                "tags": tags,
                "url": f"https://remoteok.com{row.get('data-href')}",
                "scraped_at": SCRAPE_TIME,
            })

        return pd.DataFrame(job_list)

    finally:
        driver.quit()


def save(df: pd.DataFrame):
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)

    if RAW_PATH.exists():
        existing = pd.read_csv(RAW_PATH)
        df = pd.concat([existing, df], ignore_index=True)
        

    df.to_csv(RAW_PATH, index=False)

#  Scrape run logs
def start_scrape_run(source: str) -> dict:
    return {
        "run_id": str(uuid.uuid4()),
        "source": source,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "jobs_scraped": 0,
        "status": "running",
    }

def finalize_scrape_run(run: dict, jobs_scraped: int, status: str):
    run["completed_at"] = datetime.now(timezone.utc).isoformat()
    run["jobs_scraped"] = jobs_scraped
    run["status"] = status

    SCRAPE_RUNS_PATH.parent.mkdir(parents=True, exist_ok=True)

    run_df = pd.DataFrame([run])

    if SCRAPE_RUNS_PATH.exists():
        existing = pd.read_csv(SCRAPE_RUNS_PATH)
        run_df = pd.concat([existing, run_df], ignore_index=True)

    run_df.to_csv(SCRAPE_RUNS_PATH, index=False)


if __name__ == "__main__":
    run = start_scrape_run(source="remoteok")

    try:
        df = scrape(run_id=run["run_id"], headless=True)
        save(df)

        finalize_scrape_run(
            run=run,
            jobs_scraped=len(df),
            status="success"
        )

        print(f"Run {run['run_id']} saved {len(df)} jobs → {RAW_PATH}")

    except Exception as e:
        finalize_scrape_run(
            run=run,
            jobs_scraped=0,
            status="failed"
        )
        raise
