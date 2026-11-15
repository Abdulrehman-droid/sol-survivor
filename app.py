import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import random

# Page config
st.set_page_config(
    page_title="Sol-Survivor: The AI Mission Director",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS to make it vibrant and child-friendly
st.markdown(""""
<style>
    .main {
        background-color: #0b0f19;
        color: #f0f4f8;
    }
    .stProgress > div > div > div > div {
        background-color: #f63366;
    }
    h1, h2, h3, h4 {
        color: #ff4b4b !important;
        font-family: 'Courier New', Courier, monospace;
    }
    .card {
        background-color: #171d2e;
        border-radius: 10px;
        padding: 20px;
        border: 2px solid #323d5a;
        margin-bottom: 20px;
    }
</style>
"""", unsafe_allow_html=True)

# Load space assets with fallbacks
@st.cache_resource
def load_assets():
    try:
        model = joblib.load('storm_model.joblib')
        df = pd.read_csv('nasa_donki_flares.csv')
    except Exception:
        # On-the-fly model recreation if executed standalone
        from sklearn.ensemble import RandomForestClassifier
        df = pd.DataFrame({
            'class_type': ['X2.5', 'M4.1', 'C1.2', 'X10.1', 'C9.3'] * 10,
            'severity_score': [250.0, 41.0, 1.2, 1010.0, 9.3] * 10,
            'class_letter_encoded': [ord('X'), ord('M'), ord('C'), ord('X'), ord('C')] * 10,
            'active_region': [13599, 13600, 13601, 13602, 13603] * 10,
            'storm_flag': [1, 0, 0, 1, 0] * 10
        })
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(df[['severity_score', 'class_letter_encoded', 'active_region']], df['storm_flag'])
    return model, df

model, flares_df = load_assets()

# Game State Init
if 'sol' not in st.session_state:
    st.session_state.sol = 1
    st.session_state.power = 100
    st.session_state.oxygen = 100
    st.session_state.health = 100
    st.session_state.persona_scores = {"Engineer": 0, "Biologist": 0, "Commander": 0}
    st.session_state.current_flare = flares_df.sample(n=1).iloc[0].to_dict()
    st.session_state.game_over = False
    st.session_state.game_log = []

# Reset Function
def restart_mission():
    st.session_state.sol = 1
    st.session_state.power = 100
    st.session_state.oxygen = 100
    st.session_state.health = 100
    st.session_state.persona_scores = {"Engineer": 0, "Biologist": 0, "Commander": 0}
    st.session_state.current_flare = flares_df.sample(n=1).iloc[0].to_dict()
    st.session_state.game_over = False
    st.session_state.game_log = []

# Banner
st.title("🔴 SOL-SURVIVOR: The AI Mission Director")
st.write("**Target Audience: Junior Astronauts (Ages 7–12)** | Space Mission Simulator")

# Check constraints
if st.session_state.power <= 0 or st.session_state.oxygen <= 0 or st.session_state.health <= 0:
    st.session_state.game_over = True

# --- MAIN SCREEN ---
if not st.session_state.game_over and st.session_state.sol <= 7:

    # ML Prediction Dashboard
    flare_class = st.session_state.current_flare['class_type']
    severity_sc = st.session_state.current_flare['severity_score']
    input_features = [[severity_sc, st.session_state.current_flare['class_letter_encoded'], st.session_state.current_flare['active_region']]]

    # Model Prediction Confidence
    risk_proba = model.predict_proba(input_features)[0][1] * 100

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"""<div class='card'>
            <h3>📅 Sol: {st.session_state.sol} / 7</h3>
            <p style='color: #a0aec0;'>A Sol is one day on Mars! It is 39 minutes longer than an Earth day.</p>
        </div>""", unsafe_allow_html=True)

        # Resource Indicators
        st.subheader("🛰️ Lifeline Indicators")
        st.write(f"🔋 **Power Grid**: {st.session_state.power}%")
        st.progress(max(0, min(st.session_state.power, 100)))

        st.write(f"🌬️ **Oxygen Reserves**: {st.session_state.oxygen}%")
        st.progress(max(0, min(st.session_state.oxygen, 100)))

        st.write(f"💚 **Crew Health Status**: {st.session_state.health}%")
        st.progress(max(0, min(st.session_state.health, 100)))

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("☀️ Solar Flare Warning System")
        st.write(f"**Sensor Reading:** Detected Solar Flare Class: **{flare_class}**")
        st.write(f"**NASA DONKI Severity Score:** {severity_sc}")

        # Plotly Gauge Chart for Kids
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = risk_proba,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "AI Storm Risk Prediction Score", 'font': {'color': '#f0f4f8'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#ff4b4b"},
                'steps': [
                    {'range': [0, 40], 'color': "#2e7d32"},
                    {'range': [40, 75], 'color': "#f57c00"},
                    {'range': [75, 100], 'color': "#d32f2f"}
                ]
            }
        ))
        fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Trade-off Cards based on Sol with extreme space events
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(f"🎯 Sol {st.session_state.sol} Mission Directive")

    # Generate options dynamically
    if risk_proba > 50:
        st.error("⚠️ RADIATION ALERT: AI predicts high likelihood of an incoming Coronal Mass Ejection!")
        opt_a_text = "Activate electromagnetic storm shields (Uses 25% Power, Protects Health)"
        opt_b_text = "Evacuate to deep subterranean tunnels (Uses 25% Oxygen, Safety Assured)"
        opt_c_text = "Attempt to override with backup solar cell arrays (Risk Health for 15% Power bonus)"
    else:
        st.success("✅ Calm space weather forecasted for this Sol.")
        opt_a_text = "Perform science experiment (Uses 10% Power, +15% Health due to optimism)"
        opt_b_text = "Run oxygen recycling maintenance (Uses 15% Power, +15% Oxygen boost)"
        opt_c_text = "Conserve all resources (+5% Power, +5% Oxygen, +5% Health)"

    choice = st.radio("How do you command your base? Select your path:", ["Option A", "Option B", "Option C"])
    st.write(f"**Selected Strategy Details:**")
    if choice == "Option A":
        st.info(f"👉 {opt_a_text}")
    elif choice == "Option B":
        st.info(f"👉 {opt_b_text}")
    else:
        st.info(f"👉 {opt_c_text}")

    if st.button("Lock Choice & Execute Step 🚀"):
        # Resolve metrics and state updates
        if risk_proba > 50:
            if choice == "Option A":
                st.session_state.power -= 25
                st.session_state.persona_scores["Engineer"] += 10
                st.session_state.game_log.append("Shields engaged successfully. Shield power drained but base remained safe.")
            elif choice == "Option B":
                st.session_state.oxygen -= 25
                st.session_state.persona_scores["Commander"] += 10
                st.session_state.game_log.append("Moved to deep bunker. High oxygen extraction required to support base deep underground.")
            else:
                st.session_state.health -= 35
                st.session_state.power += 15
                st.session_state.persona_scores["Biologist"] += 10
                st.session_state.game_log.append("Attempted system overrides. Solar arrays damaged by high-speed protons. Crew exposed to severe solar particle radiation!")
        else:
            if choice == "Option A":
                st.session_state.power -= 10
                st.session_state.health += 15
                st.session_state.persona_scores["Biologist"] += 10
                st.session_state.game_log.append("Science experiments conducted. Discovered unique Martian microbes!")
            elif choice == "Option B":
                st.session_state.power -= 15
                st.session_state.oxygen += 15
                st.session_state.persona_scores["Engineer"] += 10
                st.session_state.game_log.append("Oxygen recycling efficiency restored back to top tier levels.")
            else:
                st.session_state.power += 5
                st.session_state.oxygen += 5
                st.session_state.health += 5
                st.session_state.persona_scores["Commander"] += 10
                st.session_state.game_log.append("Cozy night spent resting in quarters to save precious energy.")

        # Next Sol transition
        st.session_state.sol += 1
        st.session_state.current_flare = flares_df.sample(n=1).iloc[0].to_dict()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- END GAME LOGIC ---
else:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if st.session_state.power > 0 and st.session_state.oxygen > 0 and st.session_state.health > 0:
        st.balloons()
        st.header("🎉 MISSION SURVIVED! YOU CONQUERED THE RED PLANET!")
        st.write("Congratulations, Junior Astronaut! All 7 Sols completed with active base operations.")
    else:
        st.error("💀 MISSION CRITICAL FAILURE: Your colony ran out of essential lifelines!")
        st.write("Keep practicing to become the supreme Space Commander! Space is challenging.")

    # Determine Persona
    best_role = max(st.session_state.persona_scores, key=st.session_state.persona_scores.get)
    st.subheader(f"Your Official NASA Space Badge: **{best_role}**")

    if best_role == "Engineer":
        st.info("🔧 **The Life-Support Guardian:** You prioritizing maintaining power grids, repairing critical components, and protecting electronics!")
    elif best_role == "Biologist":
        st.info("🔬 **The Astrobiology Champion:** You focused heavily on organic life, discovery, research experiments, and health safety!")
    else:
        st.info("🛡️ **The Calculated Risk-Taker:** You maintained balance, prioritized tactical team maneuvers, and safely organized operations!")

    st.subheader("📜 Mission Logs")
    for log in st.session_state.game_log:
        st.write(f"- {log}")

    if st.button("Launch Next Simulation 🛰️"):
        restart_mission()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- TRACK 3: NASA Attribution Explander ---
with st.expander("📚 NASA Data Sources, Science & Attribution"):
    st.markdown(""""
    ### Real NASA Data Sources Utilized:
    - **NASA DONKI (Database of Solar Activity & Space Weather Events):** Real-time monitoring of Solar Flares (FLR) and Coronal Mass Ejections (CME) allows our Space Warning model to run hazard risk metrics dynamically.
    - **NASA OSDR (Open Science Data Repository):** Used as inspiration for radiation particle effects on crew health safety metrics.

    ### Key Concepts for Junior Astronauts:
    *   **Sol:** A day on Mars (24 hours and 39 minutes long).
    *   **CME (Coronal Mass Ejection):** Large bubble of space plasma containing high magnetic energy particles thrown out from the Sun.
    *   **Radiation Dose:** The amount of cosmic space radiation absorbed by space suits and metal bunkers.
    """)
