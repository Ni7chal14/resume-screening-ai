import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Resume Screening AI",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
# 🤖 AI-Powered Applicant Tracking System

### Smart Resume Screening • Candidate Ranking • Skill Gap Analysis

---
""")

tab1, tab2, tab3 = st.tabs([
    "📄 Resume Analysis",
    "📊 Analytics Dashboard",
    "🏆 Resume Ranking"
])

# ==================================================
# TAB 1 - RESUME ANALYSIS
# ==================================================

with tab1:

    st.markdown(
        "Upload a resume and compare it against a job description."
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"]
    )

    job_description = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste job description here..."
    )

    candidate_name = st.text_input(
        "Candidate Name (Optional)"
    )

    candidate_email = st.text_input(
        "Candidate Email (Optional)"
    )

    position_title = st.text_input(
        "Position Title (Optional)"
    )

    analyze_button = st.button(
        "Analyze Resume",
        use_container_width=True
    )

    if analyze_button:

        if uploaded_file is None:
            st.error("Please upload a PDF resume.")
            st.stop()

        if len(job_description.strip()) < 10:
            st.error("Please enter a valid job description.")
            st.stop()

        with st.spinner("🤖 Analyzing Resume..."):

            try:

                files = {
                    "resume_file": (
                        uploaded_file.name,
                        uploaded_file,
                        "application/pdf"
                    )
                }

                data = {
                    "job_description": job_description,
                    "candidate_name": candidate_name,
                    "candidate_email": candidate_email,
                    "position_title": position_title
                }

                response = requests.post(
                    f"{API_URL}/analyze",
                    files=files,
                    data=data,
                    timeout=300
                )

                if response.status_code != 200:
                    st.error(
                        f"API Error: {response.text}"
                    )
                    st.stop()

                result = response.json()
                # st.write(result)

            except Exception as e:
                st.error(str(e))
                st.stop()

        score = result["match_score"]

        if score >= 85:
            score_status = "🟢 Excellent Match"

        elif score >= 70:
            score_status = "🟡 Good Match"

        elif score >= 50:
            score_status = "🟠 Moderate Match"

        else:
            score_status = "🔴 Low Match"

        matching_skills = result["matching_skills"]
        missing_skills = result["missing_skills"]

        st.success("✅ Analysis Complete")

        # ====================================
        # SUMMARY METRICS
        # ====================================

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Match Score",
                f"{score:.2f}%"
            )

        st.caption(score_status)

        with col2:
            st.metric(
                "Matched Skills",
                len(matching_skills)
            )

        with col3:
            st.metric(
                "Missing Skills",
                len(missing_skills)
            )

        st.divider()

        # ====================================
        # ATS SCORE GAUGE
        # ====================================

        st.subheader("🎯 ATS Match Score")

        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "%"},
                title={"text": "Resume Match Score"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"thickness": 0.3},
                    "steps": [
                        {"range": [0, 40], "color": "lightcoral"},
                        {"range": [40, 70], "color": "khaki"},
                        {"range": [70, 100], "color": "lightgreen"}
                    ]
                }
            )
        )

        st.plotly_chart(
            gauge,
            use_container_width=True
        )

        st.divider()

        # ====================================
        # SKILL MATCH BREAKDOWN
        # ====================================

        matched_count = len(matching_skills)
        missing_count = len(missing_skills)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=[
                    "Matched Skills",
                    "Missing Skills"
                ],
                y=[
                    matched_count,
                    missing_count
                ],
                text=[
                    matched_count,
                    missing_count
                ],
                textposition="outside"
            )
        )

        fig.update_layout(
            title="Skill Match Breakdown",
            yaxis_title="Number of Skills"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.divider()

        # ====================================
        # SKILLS SECTION
        # ====================================

        left, right = st.columns(2)

        with left:

            st.subheader("✅ Matching Skills")

            if matching_skills:

                for skill in matching_skills:

                    if isinstance(skill, dict):

                        st.markdown(
                            f"""
                            <div style="
                                background:#d4edda;
                                color:#111111;
                                padding:15px;
                                margin-bottom:8px;
                                border-radius:12px;
                                border-left:5px solid #28a745;
                                font-weight:500;
                            ">
                                ✅ <b>{skill['skill']}</b><br>
                                Similarity: {skill['similarity_score']:.2f}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            else:
                st.warning(
                    "No matching skills found."
                )

        with right:

            st.subheader("❌ Missing Skills")

            if missing_skills:

                for skill in missing_skills:

                    if isinstance(skill, dict):

                        st.markdown(
                            f"""
                            <div style="
                                background:#f8d7da;
                                color:#111111;
                                padding:15px;
                                margin-bottom:8px;
                                border-radius:12px;
                                border-left:5px solid #dc3545;
                                font-weight:500;
                            ">
                                ❌ <b>{skill['skill']}</b><br>
                                Similarity: {skill['similarity_score']:.2f}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            else:
                st.success(
                    "No missing skills."
                )

        st.divider()

        st.subheader("🤖 AI Recommendations")

        recommendations = result.get(
            "recommendations",
            []
        )

        if recommendations:

            for rec in recommendations:

                st.markdown(
                    f"""
                    <div style="
                        padding:15px;
                        border-radius:12px;
                        background:#eef6ff;
                        margin-bottom:10px;
                        border-left:5px solid #1f77b4;
                        color:#111111;
                        font-weight:500;
                    ">
                        💡 {rec}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.success(
                "Excellent match! No recommendations."
            )

        with st.expander("📄 Extracted Resume Text"):
            st.write(result["resume_text"])

        with st.expander("📋 Job Description"):
            st.write(result["job_description"])

# ==================================================
# TAB 2 - ANALYTICS DASHBOARD
# ==================================================

with tab2:

    st.header("📊 Analytics Dashboard")

    try:

        stats_response = requests.get(
            f"{API_URL}/statistics",
            timeout=30
        )

        top_response = requests.get(
            f"{API_URL}/top-matches",
            timeout=30
        )

        stats = stats_response.json()
        top_matches = top_response.json()

        # ====================================
        # METRICS
        # ====================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Analyses",
                stats["total_analyses"]
            )

        with col2:
            st.metric(
                "Average Score",
                f"{stats['average_match_score']:.2f}%"
            )

        with col3:
            st.metric(
                "Highest Score",
                f"{stats['max_match_score']:.2f}%"
            )

        with col4:
            st.metric(
                "Lowest Score",
                f"{stats['min_match_score']:.2f}%"
            )

        st.divider()

        # ====================================
        # SCORE OVERVIEW CHART
        # ====================================

        st.subheader("📈 Candidate Scores")

        scores_response = requests.get(
            f"{API_URL}/all-scores",
            timeout=30
        )

        scores_data = scores_response.json()

        names = scores_data["names"]
        scores = scores_data["scores"]

        if scores:

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=names,
                        y=scores,
                        text=[
                            f"{score:.2f}%"
                            for score in scores
                        ],
                        textposition="outside"
                    )
                ]
            )

            fig.update_layout(
                template="plotly_white",
                title="Candidate Match Scores",
                xaxis_title="Candidate",
                yaxis_title="Match Score (%)",
                yaxis=dict(
                    range=[0, 100]
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "No scores available yet."
            )

        st.divider()

        # ====================================
        # TOP CANDIDATES
        # ====================================

        st.subheader("🏆 Candidate Leaderboard")

        matches = top_matches["matches"]

        if matches:

            leaderboard_data = []

            for idx, candidate in enumerate(matches, start=1):

                leaderboard_data.append({
                    "Rank": idx,

                    "Candidate":
                        candidate.get(
                            "candidate_name",
                            "Unknown"
                        ),

                    "Score (%)":
                        round(
                            candidate.get(
                                "match_score",
                                0
                            ),
                            2
                        )
                })

            leaderboard_df = pd.DataFrame(
                leaderboard_data
            )

            for _, row in leaderboard_df.iterrows():

                rank = row["Rank"]

                if rank == 1:
                    medal = "🥇"

                elif rank == 2:
                    medal = "🥈"

                elif rank == 3:
                    medal = "🥉"

                else:
                    medal = f"#{rank}"

                st.markdown(
                    f"""
                    ### {medal} {row['Candidate']}
                    **Score:** {row['Score (%)']}%
                    """
                )

        else:

            st.info(
                "No candidate analyses available."
            )

    except Exception as e:

        st.error(
            f"Analytics Error: {str(e)}"
        )

# ==================================================
# TAB 3 - RESUME RANKING
# ==================================================

with tab3:

    st.header("🏆 Multi Resume Ranking")

    ranking_files = st.file_uploader(
        "Upload Multiple Resumes",
        type=["pdf"],
        accept_multiple_files=True
    )

    ranking_jd = st.text_area(
        "Job Description For Ranking",
        height=250
    )

    rank_button = st.button(
        "Rank Candidates",
        use_container_width=True
    )

    if rank_button:

        if not ranking_files:
            st.error(
                "Please upload resumes."
            )
            st.stop()

        if len(ranking_jd.strip()) < 10:
            st.error(
                "Please enter a valid job description."
            )
            st.stop()

        with st.spinner(
            "Ranking Candidates..."
        ):

            try:

                files = []

                for file in ranking_files:

                    files.append(
                        (
                            "resume_files",
                            (
                                file.name,
                                file,
                                "application/pdf"
                            )
                        )
                    )

                response = requests.post(
                    f"{API_URL}/rank-resumes",
                    files=files,
                    data={
                        "job_description":
                            ranking_jd
                    },
                    timeout=600
                )

                result = response.json()

                rankings = result[
                    "rankings"
                ]

                st.success(
                    f"Ranked {len(rankings)} candidates"
                )

                for candidate in rankings:

                    rank = candidate["rank"]

                    if rank == 1:
                        medal = "🥇 TOP MATCH"

                    elif rank == 2:
                        medal = "🥈"

                    elif rank == 3:
                        medal = "🥉"

                    else:
                        medal = f"#{rank}"

                    st.markdown(
                        f"""
                        ### {medal}
                        **{candidate['candidate_name']}**

                        Score:
                        {candidate['score']}%

                        Matching Skills:
                        {candidate['matching_skills']}

                        Missing Skills:
                        {candidate['missing_skills']}
                        """
                    )

                    st.divider()

            except Exception as e:

                st.error(str(e))