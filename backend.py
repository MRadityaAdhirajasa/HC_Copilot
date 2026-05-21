import json
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SUPABASE_AVAILABLE = bool(SUPABASE_URL and SUPABASE_KEY)

CANDIDATE_TABLE = "candidates"
MODEL_NAME = "gemini-1.5-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta2/models/{MODEL_NAME}:generateText"

JOB_DESCRIPTION = (
    "Junior/Mid Backend Software Engineer berfokus pada Python/Node.js, pemahaman SQL/PostgreSQL, "
    "RESTful API, dan Git workflow. Kandidat harus mampu membaca requirement, menulis kode yang dapat diuji, "
    "dan berkolaborasi dalam tim."
)

OFFICE_CULTURE = (
    "Budaya tim yang proaktif, kolaboratif, cepat belajar, dan menghargai komunikasi terbuka. "
    "Kandidat ideal bersikap growth mindset, adaptif terhadap perubahan, serta siap untuk berkontribusi dalam lingkungan fast-paced."
)


class BackendError(Exception):
    pass




def normalize_supabase_base(url: str) -> str:
    """
    Normalize Supabase URL so callers can safely append /rest/v1 paths.
    Removes any trailing '/rest' or '/rest/v1' and trailing slashes.
    """
    if not url:
        return url
    # remove protocol-relative whitespace
    base = url.strip()
    # remove trailing slash
    base = re.sub(r"/+$", "", base)
    # remove any trailing /rest or /rest/v1
    base = re.sub(r"(/rest/v1|/rest)(?:/)?$", "", base)
    return base


SUPABASE_BASE = normalize_supabase_base(SUPABASE_URL)


def supabase_headers(prefer: str = "return=minimal") -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _normalize_csv_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_raw_csv(uploaded_file: Any) -> pd.DataFrame:
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    raw_df = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False, na_values=[None])
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    return raw_df


def parse_uploaded_csv(uploaded_file: Any) -> pd.DataFrame:
    raw_df = load_raw_csv(uploaded_file)
    uploaded_cols = {col.strip(): col for col in raw_df.columns}
    normalized_cols = {
        re.sub(r"\s+", " ", col.strip().lower()): col
        for col in uploaded_cols
    }

    def find_column(candidates: list[str]) -> Optional[str]:
        for candidate in candidates:
            for normalized, original in normalized_cols.items():
                if candidate in normalized:
                    return original
        return None

    full_name_col = find_column(["nama lengkap", "full name", "nama"])
    skills_col = find_column([
        "sebutkan skill teknis utama",
        "skill teknis utama",
        "skills",
        "skill",
    ])
    experience_col = find_column([
        "deskripsikan 1-2 pengalaman kerja",
        "pengalaman kerja",
        "experience",
        "project",
    ])
    motivation_col = find_column([
        "mengapa anda tertarik",
        "apa yang ingin anda capai",
        "motivation",
        "why",
    ])
    portfolio_col = find_column([
        "link cv atau portfolio",
        "github",
        "linkedin",
        "portfolio",
    ])
    email_col = find_column(["email"])

    if not full_name_col or not skills_col or not experience_col or not motivation_col:
        available = ", ".join(sorted(uploaded_cols.keys()))
        raise BackendError(
            "CSV tidak memiliki kolom yang diharapkan. "
            "Kolom yang tersedia: "
            f"{available}."
        )

    records = []
    for idx, row in raw_df.iterrows():
        name = _normalize_csv_value(row.get(full_name_col, "")) or f"Candidate {idx + 1}"
        portfolio = _normalize_csv_value(row.get(portfolio_col, "")) if portfolio_col else ""
        skills = _normalize_csv_value(row.get(skills_col, ""))
        experience = _normalize_csv_value(row.get(experience_col, ""))
        motivation = _normalize_csv_value(row.get(motivation_col, ""))

        summary_text = " ".join(filter(None, [skills, experience, motivation]))
        email_value = _normalize_csv_value(row.get(email_col, "")) if email_col else ""
        email = email_value or normalize_email(name, idx + 1)

        records.append(
            {
                "full_name": name,
                "email": email,
                "github_url": portfolio,
                "skills_summary": summary_text,
                "technical_score": 0,
                "culture_score": 0,
                "summary_reason": "",
                "status": "Pending",
            }
        )

    return pd.DataFrame(records)


def slugify(text: Any) -> str:
    normalized = str(text or "").lower()
    sanitized = re.sub(r"[^a-z0-9]+", ".", normalized)
    return sanitized.strip(".") or "candidate"


def normalize_email(name: str, suffix: int) -> str:
    return f"{slugify(name)}.{suffix}@example.com"


def dedupe_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for record in records:
        key = record.get("email") or record.get("full_name")
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique


def bulk_insert_candidates(df_pandas: pd.DataFrame) -> bool:
    if not SUPABASE_AVAILABLE:
        raise BackendError("Supabase tidak dikonfigurasi. Tolong isi SUPABASE_URL dan SUPABASE_KEY di .env.")

    records = df_pandas.to_dict(orient="records")
    records = dedupe_records(records)
    if not records:
        return False

    url = f"{SUPABASE_BASE}/rest/v1/{CANDIDATE_TABLE}?on_conflict=email"
    headers = supabase_headers("resolution=ignore-duplicates,return=minimal")
    response = requests.post(url, headers=headers, json=records)
    if response.status_code not in (200, 201, 204):
        raise BackendError(
            f"Gagal insert candidate: {response.status_code} - {response.text} - url={url}"
        )

    return True


def fetch_candidate(candidate_id: Any) -> Optional[Dict[str, Any]]:
    if not SUPABASE_AVAILABLE:
        return None

    url = f"{SUPABASE_BASE}/rest/v1/{CANDIDATE_TABLE}?select=*&id=eq.{candidate_id}"
    response = requests.get(url, headers=supabase_headers())
    if response.status_code != 200:
        raise BackendError(
            f"Gagal fetch candidate id={candidate_id}: {response.status_code} - {response.text}"
        )
    results = response.json()
    return results[0] if results else None


def supabase_fetch_candidates() -> List[Dict[str, Any]]:
    if not SUPABASE_AVAILABLE:
        return []

    url = f"{SUPABASE_BASE}/rest/v1/{CANDIDATE_TABLE}?select=*"
    response = requests.get(url, headers=supabase_headers())
    if response.status_code != 200:
        raise BackendError(
            f"Gagal fetch candidates: {response.status_code} - {response.text} - url={url}"
        )
    return response.json()


def update_candidate_evaluation(candidate_id: Any, evaluation_json: Dict[str, Any]) -> bool:
    if not SUPABASE_AVAILABLE:
        raise BackendError("Supabase tidak dikonfigurasi. Tidak dapat memperbarui candidate.")

    url = f"{SUPABASE_BASE}/rest/v1/{CANDIDATE_TABLE}?id=eq.{candidate_id}"
    headers = supabase_headers()
    headers["Prefer"] = "return=representation"
    response = requests.patch(url, headers=headers, json=evaluation_json)
    if response.status_code not in (200, 201, 204):
        raise BackendError(
            f"Gagal update candidate id={candidate_id}: {response.status_code} - {response.text} - url={url}"
        )
    return True


def build_prompt(candidate: Dict[str, Any]) -> str:
    return (
        "You are an expert Human Capital Screener specializing in Tech Recruitment.\n"
        "Your job is to evaluate a candidate based on the provided Job Description (JD) and Office Culture.\n\n"
        "Compare this Candidate Data:\n"
        f"Name: {candidate.get('full_name', '')}\n"
        f"Skills & Summary: {candidate.get('skills_summary', '')}\n\n"
        "Against these criteria:\n"
        f"Job Description: {JOB_DESCRIPTION}\n"
        f"Office Culture: {OFFICE_CULTURE}\n\n"
        "Provide an objective assessment in JSON format with exactly these keys:\n"
        "{\n"
        "  \"technical_score\": <integer 1-100 based on skill fit>,\n"
        "  \"culture_score\": <integer 1-100 based on value fit>,\n"
        "  \"summary_reason\": \"<2-3 sentences explaining why you gave those scores and why they got that status>\",\n"
        "  \"status\": \"<Strictly choose only one: 'Strong Hire' (scores > 80), 'Hire' (scores 60-80), 'No Go' (scores < 60)>\"\n"
        "}\n"
        "Make sure response contains ONLY valid JSON. Do not include markdown code block syntax."
    )


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        raise BackendError("Response Gemini tidak berisi JSON yang valid.")

    depth = 0
    end = None
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index
                break

    if end is None:
        raise BackendError("Response Gemini tidak berisi JSON yang valid.")

    return text[start : end + 1]


def extract_json_payload(response_text: str) -> Dict[str, Any]:
    payload_text = _extract_first_json_object(response_text)
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise BackendError(f"Gagal mengurai JSON dari response Gemini: {exc}")
    return payload


def validate_evaluation_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_keys = {"technical_score", "culture_score", "summary_reason", "status"}
    if not required_keys.issubset(payload.keys()):
        missing = required_keys - set(payload.keys())
        raise BackendError(f"Payload Gemini tidak lengkap: missing {', '.join(sorted(missing))}")

    technical_score = payload["technical_score"]
    culture_score = payload["culture_score"]
    summary_reason = payload["summary_reason"]
    status = payload["status"]

    if not isinstance(technical_score, int) or not 1 <= technical_score <= 100:
        raise BackendError("technical_score harus integer antara 1 sampai 100.")
    if not isinstance(culture_score, int) or not 1 <= culture_score <= 100:
        raise BackendError("culture_score harus integer antara 1 sampai 100.")
    if not isinstance(summary_reason, str) or not summary_reason.strip():
        raise BackendError("summary_reason harus teks non-kosong.")
    if status not in {"Strong Hire", "Hire", "No Go"}:
        raise BackendError(
            "status harus salah satu dari: 'Strong Hire', 'Hire', atau 'No Go'."
        )

    return {
        "technical_score": technical_score,
        "culture_score": culture_score,
        "summary_reason": summary_reason.strip(),
        "status": status,
    }


def call_gemini_api(candidate: Dict[str, Any]) -> Dict[str, Any]:
    if not GOOGLE_API_KEY:
        raise BackendError("GOOGLE_API_KEY tidak dikonfigurasi di .env.")

    prompt = build_prompt(candidate)
    payload = {
        "prompt": {"text": prompt},
        "temperature": 0.2,
        "maxOutputTokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {GOOGLE_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise BackendError(
            f"Gemini API error {response.status_code}: {response.text}"
        )

    result = response.json()
    candidate_text = ""
    if isinstance(result, dict):
        candidates = result.get("candidates") or []
        if candidates and isinstance(candidates[0], dict):
            contents = candidates[0].get("content") or []
            if contents and isinstance(contents[0], dict):
                candidate_text = contents[0].get("text", "")
        candidate_text = candidate_text or result.get("output", {}).get("text", "")

    if not candidate_text:
        raise BackendError("Gemini API merespons tanpa teks yang dapat diambil.")

    payload = extract_json_payload(candidate_text)
    return validate_evaluation_payload(payload)


def evaluate_candidate_with_llm(candidate: Dict[str, Any]) -> Dict[str, Any]:
    if GOOGLE_API_KEY:
        try:
            return call_gemini_api(candidate)
        except BackendError:
            pass

    return heuristic_evaluate(candidate)


def normalize_score(score: int) -> int:
    return max(1, min(100, score))


def determine_status(technical_score: int, culture_score: int) -> str:
    average = (technical_score + culture_score) / 2
    if average > 80:
        return "Strong Hire"
    if average >= 60:
        return "Hire"
    return "No Go"


def heuristic_evaluate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    text = candidate.get("skills_summary", "").lower()
    technical_score = 50
    culture_score = 50

    tech_keywords = {
        "python": 12,
        "django": 10,
        "fastapi": 10,
        "postgresql": 10,
        "sql": 8,
        "rest api": 10,
        "kubernetes": 8,
        "docker": 8,
        "node.js": 8,
        "go": 8,
    }
    culture_keywords = {
        "kolaboratif": 12,
        "mentor": 10,
        "bekerja sama": 10,
        "growth mindset": 12,
        "belajar cepat": 10,
        "adaptif": 10,
        "inisiatif": 8,
    }

    for keyword, points in tech_keywords.items():
        if keyword in text:
            technical_score += points

    for keyword, points in culture_keywords.items():
        if keyword in text:
            culture_score += points

    if "team" in text or "tim" in text:
        culture_score += 6
    if "startup" in text or "start" in text:
        technical_score += 4
    if "fresh graduate" in text or "freshgraduate" in text:
        technical_score -= 5

    technical_score = normalize_score(technical_score)
    culture_score = normalize_score(culture_score)
    status = determine_status(technical_score, culture_score)

    reason = (
        f"Candidate menunjukkan kekuatan teknis pada {', '.join([k for k in tech_keywords if k in text][:3]) or 'skill engineering relevan'} "
        f"dengan skor teknis {technical_score}. "
        f"Skor budaya tim {culture_score} mencerminkan {('kecocokan tinggi' if culture_score > 70 else 'potensi budaya yang baik' if culture_score >= 60 else 'beberapa area yang perlu ditingkatkan')}. "
        f"Status akhir ditetapkan sebagai {status}."
    )

    return {
        "technical_score": technical_score,
        "culture_score": culture_score,
        "summary_reason": reason,
        "status": status,
    }
