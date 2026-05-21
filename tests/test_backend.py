import json
from io import StringIO

import pytest

from backend import (
    BackendError,
    extract_json_payload,
    validate_evaluation_payload,
    dedupe_records,
    parse_uploaded_csv,
    supabase_headers,
)


def test_extract_json_payload_valid_json_only():
    text = '{"technical_score": 85, "culture_score": 75, "summary_reason": "Good fit.", "status": "Hire"}'
    payload = extract_json_payload(text)
    assert payload["technical_score"] == 85
    assert payload["culture_score"] == 75
    assert payload["status"] == "Hire"


def test_extract_json_payload_with_extra_text():
    text = "Some response text before {\"technical_score\": 90, \"culture_score\": 95, \"summary_reason\": \"Strong technical fit.\", \"status\": \"Strong Hire\"} some trailing text"
    payload = extract_json_payload(text)
    assert payload["status"] == "Strong Hire"


def test_extract_json_payload_invalid_json_raises():
    invalid_text = "No json here"
    with pytest.raises(BackendError):
        extract_json_payload(invalid_text)


def test_validate_evaluation_payload_success():
    payload = {
        "technical_score": 80,
        "culture_score": 70,
        "summary_reason": "Solid candidate.",
        "status": "Hire",
    }
    validated = validate_evaluation_payload(payload)
    assert validated["technical_score"] == 80
    assert validated["culture_score"] == 70
    assert validated["summary_reason"] == "Solid candidate."


def test_validate_evaluation_payload_invalid_status_raises():
    payload = {
        "technical_score": 80,
        "culture_score": 70,
        "summary_reason": "Solid candidate.",
        "status": "Maybe",
    }
    with pytest.raises(BackendError):
        validate_evaluation_payload(payload)


def test_validate_evaluation_payload_invalid_score_raises():
    payload = {
        "technical_score": 120,
        "culture_score": 70,
        "summary_reason": "Solid candidate.",
        "status": "Hire",
    }
    with pytest.raises(BackendError):
        validate_evaluation_payload(payload)


def test_dedupe_records_removes_duplicates():
    records = [
        {"email": "a@example.com", "full_name": "A"},
        {"email": "b@example.com", "full_name": "B"},
        {"email": "a@example.com", "full_name": "A duplicate"},
    ]
    unique = dedupe_records(records)
    assert len(unique) == 2
    assert unique[0]["email"] == "a@example.com"
    assert unique[1]["email"] == "b@example.com"


def test_supabase_headers_custom_prefer():
    headers = supabase_headers("resolution=ignore-duplicates,return=minimal")
    assert headers["Prefer"] == "resolution=ignore-duplicates,return=minimal"


def test_parse_uploaded_csv_accepts_alternate_headers():
    csv_data = StringIO(
        '"Nama lengkap","Link CV atau Portfolio (GitHub, LinkedIn, Google Drive, dll)","Sebutkan skill teknis utama Anda (bahasa pemrograman, framework, tools)","Deskripsikan 1-2 pengalaman kerja atau proyek paling relevan yang pernah Anda kerjakan","Mengapa Anda tertarik melamar posisi ini? Apa yang ingin Anda capai di sini?"\n'
        'Andi Pratama,https://github.com/andipratama,Python,Developed backend services,Want to grow in a product startup.\n'
    )
    df = parse_uploaded_csv(csv_data)
    assert df.iloc[0]["full_name"] == "Andi Pratama"
    assert df.iloc[0]["github_url"] == "https://github.com/andipratama"
    assert "Python" in df.iloc[0]["skills_summary"]


def test_parse_uploaded_csv_normalizes_empty_cells():
    csv_data = StringIO(
        '"Nama lengkap","Link CV atau Portfolio (GitHub, LinkedIn, Google Drive, dll)","Sebutkan skill teknis utama Anda (bahasa pemrograman, framework, tools)","Deskripsikan 1-2 pengalaman kerja atau proyek paling relevan yang pernah Anda kerjakan","Mengapa Anda tertarik melamar posisi ini? Apa yang ingin Anda capai di sini?"\n'
        'Andi Pratama,https://github.com/andipratama,,,\n'
    )
    df = parse_uploaded_csv(csv_data)
    assert df.iloc[0]["skills_summary"] == ""
    assert df.iloc[0]["full_name"] == "Andi Pratama"


def test_parse_uploaded_csv_missing_required_header_raises():
    csv_data = StringIO(
        'Nama lengkap,Link CV atau Portfolio (GitHub, LinkedIn, Google Drive, dll),Sebutkan skill teknis utama Anda (bahasa pemrograman, framework, tools),Mengapa Anda tertarik melamar posisi ini? Apa yang ingin Anda capai di sini?\n'
        'Andi Pratama,https://github.com/andipratama,Python,Want to grow in a product startup.\n'
    )
    with pytest.raises(BackendError):
        parse_uploaded_csv(csv_data)
