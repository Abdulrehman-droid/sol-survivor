import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import random
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Sol-Survivor: Interactive AI Arcade",
    page_icon="🔴",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
    body, .main {
        background-color: #050811 !important;
        color: #e2e8f0;
    }
    .header-box {
        background: linear-gradient(135deg, #121829 0%, #0c101d 100%);
        border: 2px solid #ff4b4b;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
    }
    h1, h2, h3 {
        color: #ff4b4b !important;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
    }
    .badge-card {
        background: #101626;
        border-radius: 8px;
        border: 1px dashed #38bdf8;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Load files safely
@st.cache_resource
def load_data():
    try:
        models = joblib.load('storm_model.joblib')
        df = pd.read_csv('nasa_donki_flares.csv')
    except:
        from sklearn.ensemble import RandomForestRegressor
        df = pd.DataFrame({
            'class_type': ['X5.6', 'M2.1', 'C8.1'] * 10,
            'severity_score': [560.0, 21.0, 8.1] * 10,
            'class_letter_encoded': [88, 77, 67] * 10,
            'active_region': [13602, 13608, 13601] * 10,
            'wave_speed': [7.0, 4.2, 2.5] * 10,
            'spawn_frequency': [45.0, 75.0, 90.0] * 10
        })
        X = df[['severity_score', 'class_letter_encoded', 'active_region']]
        sm = RandomForestRegressor(n_estimators=5, random_state=42).fit(X, df['wave_speed'])
        fm = RandomForestRegressor(n_estimators=5, random_state=42).fit(X, df['spawn_frequency'])
        models = {'speed_model': sm, 'freq_model': fm}
    return models, df

models, flares_df = load_data()

# Header
st.markdown("""
<div class='header-box'>
    <h1>🔴 SOL-SURVIVOR: THE MARTIAN ARCADE</h1>
    <p style='color: #a5b4fc; font-size: 1.1rem;'>Pilot the Mars Rover & Astronaut Suit. Avoid Incoming Radiation Particles Predicted by NASA ML Data!</p>
</div>
""", unsafe_allow_html=True)

if 'current_sol_events' not in st.session_state:
    sampled = flares_df.sample(n=7).to_dict(orient='records')
    st.session_state.current_sol_events = sampled

current_sol_idx = st.query_params.get("sol", "1")
try:
    sol_num = int(current_sol_idx)
except:
    sol_num = 1
sol_num = max(1, min(7, sol_num))

current_flare = st.session_state.current_sol_events[sol_num - 1]

input_data = [[current_flare['severity_score'], current_flare['class_letter_encoded'], current_flare['active_region']]]
predicted_speed = float(models['speed_model'].predict(input_data)[0])
predicted_freq = float(models['freq_model'].predict(input_data)[0])

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"🎮 Live Pilot Panel - Sol {sol_num} / 7")

    game_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; background: #050811; color: white; overflow: hidden; font-family: sans-serif; }}
            #gameContainer {{ position: relative; width: 100%; max-width: 800px; margin: auto; }}
            canvas {{ background: #110d0a; border: 3px solid #ff4b4b; border-radius: 8px; display: block; width: 100%; }}
            .touch-bar {{ display: flex; justify-content: space-around; margin-top: 10px; gap: 8px; }}
            .btn {{ flex: 1; padding: 12px; font-size: 16px; background: #1e293b; color: white; border: 2px solid #475569; border-radius: 6px; cursor: pointer; text-align: center; font-weight: bold; user-select: none; }}
            .btn:active {{ background: #ff4b4b; border-color: #ef4444; }}
            .shield-btn {{ background: #3b82f6 !important; border-color: #60a5fa !important; }}
        </style>
    </head>
    <body>
        <div id="gameContainer">
            <canvas id="gameCanvas" width="800" height="450"></canvas>
            <div class="touch-bar">
                <div class="btn" id="btnLeft">◀ LEFT</div>
                <div class="btn" id="btnRight">RIGHT ▶</div>
                <div class="btn shield-btn" id="btnShield">🛡️ SHIELD (Hold)</div>
            </div>
        </div>

        <script>
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');

            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            function playSound(type) {{
                try {{
                    let osc = audioCtx.createOscillator();
                    let gain = audioCtx.createGain();
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);

                    if (type === 'hit') {{
                        osc.type = 'sawtooth';
                        osc.frequency.setValueAtTime(150, audioCtx.currentTime);
                        osc.frequency.exponentialRampToValueAtTime(10, audioCtx.currentTime + 0.3);
                        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
                        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                        osc.start(); osc.stop(audioCtx.currentTime + 0.3);
                    }} else if (type === 'pickup') {{
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(400, audioCtx.currentTime);
                        osc.frequency.exponentialRampToValueAtTime(1200, audioCtx.currentTime + 0.2);
                        gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
                        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
                        osc.start(); osc.stop(audioCtx.currentTime + 0.2);
                    }} else if (type === 'shield') {{
                        osc.type = 'triangle';
                        osc.frequency.setValueAtTime(80, audioCtx.currentTime);
                        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                        gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
                        osc.start(); osc.stop(audioCtx.currentTime + 0.15);
                    }}
                }} catch(e) {{}}
            }}

            const physics = {{
                waveSpeed: {predicted_speed},
                spawnFreq: {predicted_freq}
            }};

            const rover = {{
                x: 400,
                y: 380,
                width: 50,
                height: 40,
                speed: 6,
                shieldActive: false,
                power: 100,
                o2: 100,
                health: 100
            }};

            let particles = [];
            let items = [];
            let score = 0;
            let shieldDoseSaved = 0;
            let keys = {{}};
            let frameCount = 0;
            let gameOver = false;

            let touchLeft = false, touchRight = false, touchShield = false;
            document.getElementById('btnLeft').addEventListener('mousedown', () => touchLeft = true);
            document.getElementById('btnLeft').addEventListener('mouseup', () => touchLeft = false);
            document.getElementById('btnRight').addEventListener('mousedown', () => touchRight = true);
            document.getElementById('btnRight').addEventListener('mouseup', () => touchRight = false);
            document.getElementById('btnShield').addEventListener('mousedown', () => {{ touchShield = true; playSound('shield'); }});
            document.getElementById('btnShield').addEventListener('mouseup', () => touchShield = false);

            document.getElementById('btnLeft').addEventListener('touchstart', (e) => {{ e.preventDefault(); touchLeft = true; }});
            document.getElementById('btnLeft').addEventListener('touchend', () => touchLeft = false);
            document.getElementById('btnRight').addEventListener('touchstart', (e) => {{ e.preventDefault(); touchRight = true; }});
            document.getElementById('btnRight').addEventListener('touchend', () => touchRight = false);
            document.getElementById('btnShield').addEventListener('touchstart', (e) => {{ e.preventDefault(); touchShield = true; playSound('shield'); }});
            document.getElementById('btnShield').addEventListener('touchend', () => touchShield = false);

            window.addEventListener('keydown', e => {{ keys[e.code] = true; }});
            window.addEventListener('keyup', e => {{ keys[e.code] = false; }});

            function spawnHazards() {{
                if (frameCount % Math.round(physics.spawnFreq) === 0) {{
                    particles.push({{
                        x: Math.random() * canvas.width,
                        y: -20,
                        radius: 12 + Math.random() * 12,
                        speed: physics.waveSpeed + (Math.random() * 2)
                    }});
                }}

                if (frameCount % 180 === 0) {{
                    items.push({{
                        x: Math.random() * canvas.width,
                        y: -20,
                        type: Math.random() > 0.5 ? 'power' : 'oxygen',
                        size: 16,
                        speed: 3
                    }});
                }}
            }}

            function update() {{
                if (gameOver) return;
                frameCount++;

                if (frameCount % 60 === 0) {{
                    rover.o2 = Math.max(0, rover.o2 - 1);
                }}

                if (keys['ArrowLeft'] || keys['KeyA'] || touchLeft) {{
                    rover.x = Math.max(0, rover.x - rover.speed);
                }}
                if (keys['ArrowRight'] || keys['KeyD'] || touchRight) {{
                    rover.x = Math.min(canvas.width - rover.width, rover.x + rover.speed);
                }}

                rover.shieldActive = (keys['Space'] || touchShield) && rover.power > 1;
                if (rover.shieldActive) {{
                    rover.power = Math.max(0, rover.power - 0.25);
                }}

                for (let i = particles.length - 1; i >= 0; i--) {{
                    let p = particles[i];
                    p.y += p.speed;

                    let dist = Math.hypot((p.x - (rover.x + rover.width/2)), (p.y - (rover.y + rover.height/2)));
                    if (dist < p.radius + 20) {{
                        if (rover.shieldActive) {{
                            playSound('shield');
                            shieldDoseSaved += 15;
                        }} else {{
                            playSound('hit');
                            rover.health = Math.max(0, rover.health - 20);
                        }}
                        particles.splice(i, 1);
                        continue;
                    }}

                    if (p.y > canvas.height) particles.splice(i, 1);
                }}

                for (let i = items.length - 1; i >= 0; i--) {{
                    let item = items[i];
                    item.y += item.speed;

                    let dist = Math.hypot((item.x - (rover.x + rover.width/2)), (item.y - (rover.y + rover.height/2)));
                    if (dist < item.size + 20) {{
                        playSound('pickup');
                        if (item.type === 'power') rover.power = Math.min(100, rover.power + 25);
                        if (item.type === 'oxygen') rover.o2 = Math.min(100, rover.o2 + 25);
                        items.splice(i, 1);
                        continue;
                    }}

                    if (item.y > canvas.height) items.splice(i, 1);
                }}

                if (rover.health <= 0 || rover.o2 <= 0 || rover.power <= 0) {{
                    gameOver = true;
                    sendStats();
                }}

                score = Math.floor(frameCount / 10);
                if (score >= 400) {{
                    gameOver = true;
                    sendStats();
                }}
            }}

            function sendStats() {{
                let status = (rover.health > 0 && rover.o2 > 0 && rover.power > 0) ? "survived" : "failed";
                let stats = {{
                    "status": status,
                    "shieldDoseSaved": shieldDoseSaved,
                    "finalPower": Math.round(rover.power),
                    "finalOxygen": Math.round(rover.o2),
                    "finalHealth": Math.round(rover.health)
                }};
                window.parent.postMessage({{
                    type: 'sol_survivor_game_over',
                    data: stats
                }}, '*');
            }}

            function draw() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                ctx.fillStyle = '#1e110a';
                ctx.fillRect(0, 360, canvas.width, 90);

                items.forEach(item => {{
                    ctx.beginPath();
                    ctx.arc(item.x, item.y, item.size, 0, Math.PI * 2);
                    ctx.fillStyle = item.type === 'power' ? '#f59e0b' : '#38bdf8';
                    ctx.fill();
                    ctx.fillStyle = "#fff";
                    ctx.font = "10px monospace";
                    ctx.fillText(item.type === 'power' ? "BAT" : "O2", item.x - 10, item.y + 3);
                }});

                particles.forEach(p => {{
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                    ctx.fillStyle = '#ef4444';
                    ctx.fill();
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.radius + 4, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
                    ctx.stroke();
                }});

                ctx.fillStyle = '#e2e8f0';
                ctx.fillRect(rover.x, rover.y, rover.width, rover.height);
                ctx.fillStyle = '#f43f5e';
                ctx.fillRect(rover.x + 10, rover.y + 10, 30, 15);

                ctx.fillStyle = '#0f172a';
                ctx.fillRect(rover.x + 2, rover.y + rover.height - 5, 12, 10);
                ctx.fillRect(rover.x + rover.width - 14, rover.y + rover.height - 5, 12, 10);

                if (rover.shieldActive) {{
                    ctx.beginPath();
                    ctx.arc(rover.x + rover.width/2, rover.y + rover.height/2, 45, 0, Math.PI * 2);
                    ctx.strokeStyle = '#3b82f6';
                    ctx.lineWidth = 4;
                    ctx.stroke();
                    ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
                    ctx.fill();
                }}

                ctx.fillStyle = 'rgba(23, 29, 46, 0.8)';
                ctx.fillRect(10, 10, 300, 95);
                ctx.fillStyle = '#fff';
                ctx.font = '12px Courier New';
                ctx.fillText(`🔋 POWER: ${Math.round(rover.power)}%`, 20, 30);
                ctx.fillText(`🌬️ OXYGEN: ${Math.round(rover.o2)}%`, 20, 50);
                ctx.fillText(`💚 HEALTH: ${Math.round(rover.health)}%`, 20, 70);
                ctx.fillText(`⏱️ SOL TIME: ${score}/400`, 20, 90);

                if (gameOver) {{
                    ctx.fillStyle = 'rgba(0,0,0,0.8)';
                    ctx.fillRect(0,0, canvas.width, canvas.height);
                    ctx.fillStyle = '#ef4444';
                    ctx.font = '32px Courier New';
                    ctx.fillText("SOL COMPLETED / TERMINATED", 150, 200);
                    ctx.font = '16px Courier New';
                    ctx.fillStyle = '#fff';
                    ctx.fillText("Refreshing page updates game logs!", 220, 240);
                }}
            }}

            function loop() {{
                spawnHazards();
                update();
                draw();
                requestAnimationFrame(loop);
            }}
            loop();
        </script>
    </body>
    </html>
    """
    components.html(game_html, height=540, scrolling=False)

with col2:
    st.subheader("☀️ Solar Flare Warnings")
    st.write(f"**Event ID:** FLR-{current_flare.get('active_region', 13600)}")
    st.metric("Severity Score", f"{current_flare['severity_score']}")
    st.metric("Solar Flare Class", current_flare['class_type'])

    st.markdown("""
    **Controls:**
    - **A / D** or **Arrow Keys**: Move left / right
    - **Spacebar**: Deploy Magnetic Shield
    - Touch controllers are available on mobile!
    """)

    st.write("---")
    st.write("**Choose Your Sol:**")
    for s in range(1, 8):
        if st.button(f"Sol {s} Directive", key=f"sol_btn_{s}"):
            st.query_params["sol"] = str(s)
            st.rerun()

st.markdown("""
---
### 📚 NASA Open Data & Science Briefing (Ages 7–12)
- **NASA DONKI (Database of Solar Activity):** Real class metrics (C, M, X) directly determine solar radiation wave physics and speed!
- **NASA OSDR (Open Science Data Repository):** Inspired bio-monitoring lifeline indicators to study space flight health risks.
""")
