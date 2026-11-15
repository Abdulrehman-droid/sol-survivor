from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
import numpy as np
import joblib
import random

app = Flask(__name__)
app.secret_key = 'sol_survivor_secret_key_nasa'

# Load space assets with on-the-fly fallback
def load_assets():
    try:
        model = joblib.load('storm_model.joblib')
        df = pd.read_csv('nasa_donki_flares.csv')
    except Exception:
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

def init_game():
    session['sol'] = 1
    session['power'] = 100
    session['oxygen'] = 100
    session['health'] = 100
    session['persona_scores'] = {"Engineer": 0, "Biologist": 0, "Commander": 0}

    # Choose first flare event
    sample = flares_df.sample(n=1).iloc[0].to_dict()
    session['current_flare'] = {
        'class_type': str(sample['class_type']),
        'severity_score': float(sample['severity_score']),
        'class_letter_encoded': int(sample['class_letter_encoded']),
        'active_region': int(sample['active_region'])
    }
    session['game_over'] = False
    session['game_log'] = []

@app.route('/')
def index():
    if 'sol' not in session:
        init_game()

    # Live ML Inference
    flare = session['current_flare']
    input_features = [[flare['severity_score'], flare['class_letter_encoded'], flare['active_region']]]
    risk_proba = float(model.predict_proba(input_features)[0][1] * 100)

    # Determine warning dynamically
    is_storm_alert = risk_proba > 50

    return render_template(
        'index.html',
        sol=session['sol'],
        power=session['power'],
        oxygen=session['oxygen'],
        health=session['health'],
        flare=flare,
        risk_proba=round(risk_proba, 1),
        is_storm_alert=is_storm_alert,
        game_over=session['game_over'],
        game_log=session['game_log'],
        persona_scores=session['persona_scores']
    )

@app.route('/action', methods=['POST'])
def action():
    if session.get('game_over'):
        return redirect(url_for('index'))

    choice = request.form.get('choice')
    risk_proba = float(request.form.get('risk_proba', 0))

    # Resolve actions based on Sol environmental conditions
    if risk_proba > 50:
        if choice == "A":
            session['power'] = max(0, session['power'] - 25)
            session['persona_scores']['Engineer'] += 10
            session['game_log'].append("Shields engaged successfully. Base remained safe.")
        elif choice == "B":
            session['oxygen'] = max(0, session['oxygen'] - 25)
            session['persona_scores']['Commander'] += 10
            session['game_log'].append("Moved to deep bunker. Safe, but high oxygen consumed.")
        else:
            session['health'] = max(0, session['health'] - 35)
            session['power'] = min(100, session['power'] + 15)
            session['persona_scores']['Biologist'] += 10
            session['game_log'].append("Attempted override. Crew exposed to severe solar radiation!")
    else:
        if choice == "A":
            session['power'] = max(0, session['power'] - 10)
            session['health'] = min(100, session['health'] + 15)
            session['persona_scores']['Biologist'] += 10
            session['game_log'].append("Experiments conducted. Found Martian microbes!")
        elif choice == "B":
            session['power'] = max(0, session['power'] - 15)
            session['oxygen'] = min(100, session['oxygen'] + 15)
            session['persona_scores']['Engineer'] += 10
            session['game_log'].append("Oxygen recycling efficiency restored back to peak levels.")
        else:
            session['power'] = min(100, session['power'] + 5)
            session['oxygen'] = min(100, session['oxygen'] + 5)
            session['health'] = min(100, session['health'] + 5)
            session['persona_scores']['Commander'] += 10
            session['game_log'].append("Conserved resources and rested during peaceful space conditions.")

    # Next Sol
    session['sol'] += 1

    if session['power'] <= 0 or session['oxygen'] <= 0 or session['health'] <= 0 or session['sol'] > 7:
        session['game_over'] = True
    else:
        sample = flares_df.sample(n=1).iloc[0].to_dict()
        session['current_flare'] = {
            'class_type': str(sample['class_type']),
            'severity_score': float(sample['severity_score']),
            'class_letter_encoded': int(sample['class_letter_encoded']),
            'active_region': int(sample['active_region'])
        }

    session.modified = True
    return redirect(url_for('index'))

@app.route('/restart')
def restart():
    init_game()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
