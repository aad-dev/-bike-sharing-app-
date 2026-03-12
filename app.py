import streamlit as st
import pandas as pd
import pickle
import sqlite3
from datetime import datetime

# database klaarzetten


def init_db():
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prediction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    season INTEGER, yr INTEGER, mnth INTEGER, hr INTEGER,
                    holiday INTEGER, weekday INTEGER, workingday INTEGER,
                    weathersit INTEGER, temp REAL, atemp REAL, hum REAL, windspeed REAL,
                    prediction INTEGER
                )''')
    conn.commit()
    conn.close()


init_db()

# inladen van augurk
with open('models/bike_rf_model.pkl', 'rb') as file:
    model = pickle.load(file)

st.title("Bike sharing voorspeller")
st.write("Vul de weersomstandigheden en datum in om te voorspellen hoeveel fietsen er dit uur verhuurd worden!")

st.sidebar.header("Voer de variabelen in:")

season = st.sidebar.selectbox(
    "Seizoen (1:Lente, 2:Zomer, 3:Herfst, 4:Winter)", [1, 2, 3, 4])
yr = st.sidebar.selectbox("Jaar (0: 2011, 1: 2012)", [0, 1])
mnth = st.sidebar.slider("Maand (1-12)", 1, 12, 1)
hr = st.sidebar.slider("Uur van de dag (0-23)", 0, 23, 12)
holiday = st.sidebar.selectbox("Feestdag? (0:Nee, 1:Ja)", [0, 1])
weekday = st.sidebar.slider("Dag van de week (0=Zondag, 6=Zaterdag)", 0, 6, 3)
workingday = st.sidebar.selectbox("Werkdag? (0:Nee, 1:Ja)", [0, 1])
weathersit = st.sidebar.selectbox(
    "Weersituatie (1:Helder - 4:Noodweer)", [1, 2, 3, 4])

# de numerieke inputs
temp = st.sidebar.slider("Temperatuur (genormaliseerd 0-1)", 0.0, 1.0, 0.5)
atemp = st.sidebar.slider(
    "Gevoelstemperatuur (genormaliseerd 0-1)", 0.0, 1.0, 0.5)
hum = st.sidebar.slider("Luchtvochtigheid (genormaliseerd 0-1)", 0.0, 1.0, 0.5)
windspeed = st.sidebar.slider(
    "Windsnelheid (genormaliseerd 0-1)", 0.0, 1.0, 0.2)

# maken van de voorspellingen
if st.button("Voorspel aantal huurfietsen"):
    # df met de kolommen net zoals uit mijn notebook
    input_data = pd.DataFrame([[season, yr, mnth, hr, holiday, weekday, workingday, weathersit, temp, atemp, hum, windspeed]],
                              columns=['season', 'yr', 'mnth', 'hr', 'holiday', 'weekday', 'workingday', 'weathersit', 'temp', 'atemp', 'hum', 'windspeed'])

    # doe de voorspelling
    voorspelling = model.predict(input_data)

    st.success(
        f"Verwacht aantal verhuurde fietsen voor dit uur: **{int(voorspelling[0])}**")

    # resultaat in de database knallen
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    huidige_tijd = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute('''INSERT INTO prediction_logs 
                 (timestamp, season, yr, mnth, hr, holiday, weekday, workingday, weathersit, temp, atemp, hum, windspeed, prediction)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (huidige_tijd, season, yr, mnth, hr, holiday, weekday, workingday, weathersit, temp, atemp, hum, windspeed, int(voorspelling[0])))

    conn.commit()
    conn.close()

# geschiedenis op het scherm zetten
st.markdown("---")
st.subheader("Database logboek")

conn = sqlite3.connect('predictions.db')
df_logs = pd.read_sql_query(
    "SELECT * FROM prediction_logs ORDER BY timestamp DESC", conn)
conn.close()

if not df_logs.empty:
    st.dataframe(df_logs)
else:
    st.info("Nog geen voorspellingen gedaan")
