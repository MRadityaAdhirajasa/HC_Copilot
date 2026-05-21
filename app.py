import pandas as pd
import streamlit as st

from backend import (
    JOB_DESCRIPTION,
    OFFICE_CULTURE,
    SUPABASE_AVAILABLE,
    bulk_insert_candidates,
    evaluate_candidate_with_llm,
    load_raw_csv,
    parse_uploaded_csv,
    supabase_fetch_candidates,
    update_candidate_evaluation,
)

st.set_page_config(
    page_title="HC Talent Analytics",
    page_icon="📋",
    layout="wide",
)


def get_local_candidates() -> list[dict]:
    return st.session_state.get("local_candidates", [])


def set_local_candidates(records: list[dict]) -> None:
    st.session_state["local_candidates"] = records


def load_candidates() -> tuple[list[dict], str | None]:
    if SUPABASE_AVAILABLE:
        try:
            candidates = supabase_fetch_candidates()
            if candidates:
                return candidates, None
        except Exception as exc:
            local_candidates = get_local_candidates()
            return local_candidates, str(exc)

    local_candidates = get_local_candidates()
    return local_candidates, None


def insert_local_candidates(records: list[dict]) -> None:
    existing = get_local_candidates()
    existing_emails = {item["email"] for item in existing}
    unique_records = [rec for rec in records if rec["email"] not in existing_emails]
    set_local_candidates(existing + unique_records)


def seed_candidates(records: list[dict]) -> None:
    if SUPABASE_AVAILABLE:
        try:
            bulk_insert_candidates(pd.DataFrame(records))
            st.success("Data kandidat berhasil dimasukkan ke Supabase.")
            return
        except Exception as exc:
            st.error(f"Gagal memasukkan data ke Supabase: {exc}")
            insert_local_candidates(records)
            st.info("Data kandidat disimpan lokal sementara di sesi ini.")
            return

    insert_local_candidates(records)
    st.success("Data kandidat berhasil disimpan lokal sementara di sesi ini.")


def update_candidate(candidate: dict, evaluation: dict) -> None:
    candidate.update(evaluation)
    if SUPABASE_AVAILABLE and candidate.get("id") is not None:
        try:
            update_candidate_evaluation(candidate["id"], evaluation)
        except Exception as exc:
            st.error(f"Gagal memperbarui kandidat ke Supabase: {exc}")
    else:
        local_candidates = get_local_candidates()
        for index, record in enumerate(local_candidates):
            if record.get("email") == candidate.get("email"):
                local_candidates[index].update(candidate)
                break
        set_local_candidates(local_candidates)


def candidate_dataframe(candidates: list[dict]) -> pd.DataFrame:
    if not candidates:
        return pd.DataFrame()
    df = pd.DataFrame(candidates)
    df = df["id full_name email github_url technical_score culture_score status summary_reason".split() if "id" in df.columns else "full_name email github_url technical_score culture_score status summary_reason".split()]
    return df


def main() -> None:
    st.sidebar.markdown("# HC Talent Analytics")
    st.sidebar.write("Dashboard untuk upload, scoring AI, dan monitoring status kandidat.")

    if not SUPABASE_AVAILABLE:
        st.sidebar.warning(
            "Supabase tidak dikonfigurasi. Data akan disimpan secara lokal hanya selama sesi browser ini. "
            "Tambahkan `supabase_url` dan `supabase_key` ke `streamlit.secrets` untuk koneksi live."
        )

    uploaded_file = st.sidebar.file_uploader("Unggah file CSV kandidat", type=["csv"])
    use_sample = st.sidebar.button("Load sample data dari data/pelamar.csv")
    if use_sample and not uploaded_file:
        uploaded_file = open("data/pelamar.csv", "rb")

    with st.sidebar.expander("Job Description & Office Culture", expanded=True):
        st.markdown("**Job Description**")
        st.write(JOB_DESCRIPTION)
        st.markdown("**Office Culture**")
        st.write(OFFICE_CULTURE)

    if uploaded_file is not None:
        try:
            raw_df = load_raw_csv(uploaded_file)
            with st.sidebar.expander("Preview CSV Asli", expanded=True):
                st.dataframe(raw_df, use_container_width=True)

            parsed_df = parse_uploaded_csv(uploaded_file)
            with st.sidebar.expander("Preview Kandidat untuk Seed", expanded=False):
                st.dataframe(
                    parsed_df[["full_name", "email", "github_url", "skills_summary", "status"]],
                    use_container_width=True,
                )

            if st.sidebar.button("Seed Database"):
                seed_candidates(parsed_df.to_dict(orient="records"))
        except Exception as exc:
            st.sidebar.error(f"Tidak dapat membaca CSV: {exc}")

    candidates, supabase_error = load_candidates()
    if supabase_error:
        st.sidebar.warning(
            f"Gagal mengambil data Supabase: {supabase_error}. Menampilkan data lokal jika tersedia."
        )

    total_count = len(candidates)
    scored_count = len([item for item in candidates if item.get("status") and item.get("status") != "Pending"])
    pending_count = len([item for item in candidates if item.get("status") == "Pending"])

    st.markdown("# Candidate Interview Feedback Tracker")
    st.markdown("Aplikasi demo untuk menilai dan memvisualisasikan hasil screening awal pelamar.")

    metric_cols = st.columns(3)
    metric_cols[0].metric("Total Pelamar", total_count)
    metric_cols[1].metric("Sudah Dinilai", scored_count)
    metric_cols[2].metric("Pending", pending_count)

    tab1, tab2 = st.tabs(["📊 Evaluation Dashboard", "📥 Pending Screening & Action"])

    with tab1:
        st.subheader("Evaluation Dashboard")
        if candidates:
            df = candidate_dataframe(candidates)
            st.dataframe(df, use_container_width=True)

            selected_email = st.selectbox(
                "Pilih kandidat untuk lihat detail",
                options=[item["email"] for item in candidates],
                format_func=lambda email: next((item["full_name"] for item in candidates if item["email"] == email), email),
            )
            selected = next((item for item in candidates if item["email"] == selected_email), None)
            if selected:
                st.markdown("### Detail Kandidat")
                st.write(f"**Nama:** {selected.get('full_name')}")
                st.write(f"**Email:** {selected.get('email')}")
                st.write(f"**Portfolio / Link:** {selected.get('github_url')}")
                st.write(f"**Status:** {selected.get('status')}")
                st.write(f"**Technical Score:** {selected.get('technical_score')}")
                st.write(f"**Culture Score:** {selected.get('culture_score')}")
                st.markdown("**Alasan Ringkas AI / Heuristik:**")
                st.write(selected.get("summary_reason"))
        else:
            st.info("Tidak ada data kandidat. Unggah CSV atau load sample data terlebih dahulu.")

    with tab2:
        st.subheader("Pending Screening & Action")
        pending_candidates = [item for item in candidates if item.get("status") == "Pending"]
        if pending_candidates:
            st.write(f"Ada {len(pending_candidates)} kandidat pending siap diproses.")
            if st.button("Run AI Assessment Engine"):
                with st.spinner("Menjalankan penilaian AI untuk kandidat pending..."):
                    for candidate in pending_candidates:
                        evaluation = evaluate_candidate_with_llm(candidate)
                        update_candidate(candidate, evaluation)
                st.success("Semua kandidat pending telah diproses.")
                if hasattr(st, "rerun"):
                    st.rerun()
                elif hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
            st.dataframe(pd.DataFrame(pending_candidates), use_container_width=True)
        else:
            st.info("Tidak ada kandidat pending saat ini.")

    st.markdown("---")
    st.markdown("#### Catatan Implementasi")
    st.markdown(
        "Jika Anda ingin mengaktifkan koneksi Supabase live, tambahkan kredensial di `streamlit.secrets`. "
        "Jika Anda ingin menambahkan Gemini API, sesuaikan fungsi `analyze_candidate_with_llm`."
    )


if __name__ == "__main__":
    if "local_candidates" not in st.session_state:
        set_local_candidates([])
    main()
