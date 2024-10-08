import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, time, date

# Carichiamo le variabili d'ambiente dal file .env
load_dotenv()

# Configura Airtable
AIRTABLE_API_KEY = "patVvkwrcLfpSQFlN.6284937647e50b10895d44cd1c0829a183bfd24d488be47ca84c9538f90938e3"
BASE_ID = 'appGyD33GmhodfxlW'  # Il tuo Base ID
TABLE_ID = 'tblCPYQNiEie2tEyy'  # ID della tua tabella LEADS NUOVI

# Definiamo le colonne che vogliamo visualizzare
view_columns = ['Nome', 'Cognome', 'Servizio richiesto', 'Telefono', 'Istituto di origine', 'Presentato/a?', 'Importo pagato']

# CREDENZIALI degli utenti con Istituto di origine associato
CREDENZIALI = {
    'damapoint1': {'password': 'dama321', 'istituto': 'DamaPoint - Vomero, Via Kerbaker 92'},
    'damapoint2': {'password': 'dama321', 'istituto': 'DamaPoint - Portici, P.zzale Brunelleschi 21'},
    'damapoint3': {'password': 'dama321', 'istituto': 'DamaPoint - Nocera, Via Roma 70'},
    'damapoint4': {'password': 'dama321', 'istituto': 'DamaPoint - Benevento, C.so Vittore Emanuele III 24'},
    'damapoint5': {'password': 'dama321', 'istituto': 'DamaPoint - Torre Annunziata, C.so Umberto I 209'},
    'damapoint6': {'password': 'dama321', 'istituto': 'DamaPoint - Nola, Via Circumvallazione 12/14'},
    'damapoint7': {'password': 'dama321', 'istituto': 'DamaPoint - Salerno, Corso Giuseppe Garibaldi 217'},
    'damapoint8': {'password': 'dama321', 'istituto': 'DamaPoint - Scafati, C.so Nazionale 454'},
    'damapoint9': {'password': 'dama321', 'istituto': 'Damapoint - Castellammare, Via Roma 15'},
    'damapoint10': {'password': 'dama321', 'istituto': 'DamaPoint - Chiaia, Via Arcoleo 35'},
    'damapoint11': {'password': 'dama321', 'istituto': 'DamaPoint - San Giuseppe Vesuviano, C.so Emanuele 16'},
    'damapoint12': {'password': 'dama321', 'istituto': 'DamaPoint - Cava De’ Tirreni, C.so Principe Amodeo 5'},
    'damapoint13': {'password': 'dama321', 'istituto': 'DamaPoint - Battipaglia, Via Roma 52'},
    'damapoint14': {'password': 'dama321', 'istituto': 'DamaPoint - Pomigliano, Via F. Terracciano 119'}
}

# Funzione per connettersi a Airtable e ottenere i dati
def connect_to_airtable():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            for record in data.get('records', []):
                fields = record['fields']
                fields['id'] = record['id']
                records.append(fields)
            offset = data.get('offset', None)
            if not offset:
                break
        else:
            st.error(f"Errore nel recupero dei dati da Airtable: {response.status_code}")
            return None
    
    df = pd.DataFrame(records)
    df = df[df['Esito telefonata'] == 'App. Fissato']

    df['Presentato/a?'] = df.get('Presentato/a?', False)
    df['Importo pagato'] = df.get('Importo pagato', 0.0)

    df['Data e ora appuntamento'] = pd.to_datetime(df['Data e ora appuntamento'], errors='coerce').dt.strftime('%d-%m-%Y alle ore %H:%M')

    return df

# Funzione per il login
def login(username, password):
    if username in CREDENZIALI and CREDENZIALI[username]['password'] == password:
        st.session_state['username'] = username
        st.session_state['istituto'] = CREDENZIALI[username]['istituto']
        st.success(f"Benvenuto, Istituto: {st.session_state['istituto']}")
        return True
    else:
        st.error("Username o password non corretti")
        return False

# Funzione per aggiornare i record in Airtable
def update_airtable_record(record_id, updated_fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    valid_modalita_acconto = ["Carta", "Contanti", "Pagodil"]

    if 'ModalitàPagamentoAcc.' in updated_fields:
        if updated_fields['ModalitàPagamentoAcc.'] not in valid_modalita_acconto:
            st.error(f"Errore: '{updated_fields['ModalitàPagamentoAcc.']}' non è un'opzione valida.")
            return

    if 'Data AppRifissato' in updated_fields:
        if isinstance(updated_fields['Data AppRifissato'], (datetime, date)):
            if isinstance(updated_fields['Data AppRifissato'], date) and not isinstance(updated_fields['Data AppRifissato'], datetime):
                updated_fields['Data AppRifissato'] = datetime.combine(updated_fields['Data AppRifissato'], datetime.min.time())

            updated_fields['Data AppRifissato'] = updated_fields['Data AppRifissato'].isoformat() + 'Z'

    data = {
        "fields": updated_fields,
        "typecast": True
    }

    response = requests.patch(url, json=data, headers=headers)

    if response.status_code == 200:
        st.success(f"Cliente aggiornato correttamente.")
    else:
        st.error(f"Errore durante l'aggiornamento del record {record_id}: {response.text}")

# Funzione Streamlit per visualizzare e modificare i dati
def app():
    st.title("Dama Point | Gestione outcome appuntamento")

    if 'username' not in st.session_state:
        st.subheader("Effettua il login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)

    if 'username' in st.session_state:
        istituto_utente = st.session_state['istituto']

        df = connect_to_airtable()

        if df is not None:
            df_filtered = df[df['Istituto di origine'] == istituto_utente]

            search_query = st.text_input("Cerca cliente per Nome o Cognome")

            if search_query:
                filtered_df = df_filtered[df_filtered['Nome'].str.contains(search_query, case=False) | df_filtered['Cognome'].str.contains(search_query, case=False)]
            else:
                filtered_df = df_filtered

            if not filtered_df.empty:
                st.write(f"**{len(filtered_df)} Clienti trovati per {istituto_utente}:**")

                modalita_pagamento_acc_options = ["Carta", "Contanti", "Pagodil"]
                operatrice_consulenza_options = [
                    "Anna Maiello", "Luana Montano", "Angela Capillari", "Claudia Monaco", "Carmen Nugnes",
                    "Anna Marchese", "Ilaria Formisano", "Serena De falco", "Pariota Ilaria", "Roberta Vicidomini",
                    "Sara Fraj", "Annamaria Del Mastro", "Carla Pellone", "Giusy De Paola", "Ilenia Paolini",
                    "Martina Pierri", "Nunzia Braca", "Ginevra Barrella", "Monica Di Lauro", "Gabriella Apicella",
                    "Fanny Alfano", "Sara Frojo", "Veronica Errico", "Carmela Montanino", "Ylenia Esposito",
                    "Ortensia Balestrieri", "Luisa Pisacane", "Scala Alessia", "Carolina Piacente", "Maria Pia Vitale",
                    "Alessia Vitale", "Rossella Moccia", "Maria Teresa Regina", "Marica Faiella", "Giovanna Strollo",
                    "Antonia Passamato", "Roberta Boffa", "Carmela De Riggi", "Fenizia DI Fiore", "D'Ambrosio Filomena"
                ]

                for index, row in filtered_df.iterrows():
                    with st.expander(f"{row['Nome']} {row['Cognome']}"):
                        with st.form(key=f"form_{index}"):

                            st.write(f"Servizio richiesto: {row['Servizio richiesto']}")
                            st.write(f"Telefono: {row['Telefono']}")
                            st.write(f"Data e ora consulenza: {row['Data e ora appuntamento']}")
                            st.write(f"Operatrice consulenza assegnata: {row['Operatrice']}")

                            if f"presentato_{index}" not in st.session_state:
                                st.session_state[f"presentato_{index}"] = row['Presentato/a?']

                            if f"importo_{index}" not in st.session_state:
                                st.session_state[f"importo_{index}"] = row['Importo pagato']

                            if f"followup_{index}" not in st.session_state:
                                st.session_state[f"followup_{index}"] = "No"

                            if f"data_followup_{index}" not in st.session_state:
                                st.session_state[f"data_followup_{index}"] = None

                            if f"acconto_importo_{index}" not in st.session_state:
                                st.session_state[f"acconto_importo_{index}"] = 0.0

                            if f"modalita_acconto_{index}" not in st.session_state:
                                st.session_state[f"modalita_acconto_{index}"] = modalita_pagamento_acc_options[0]  # Predefinisci "Carta"

                            if f"modalita_saldo_{index}" not in st.session_state:
                                st.session_state[f"modalita_saldo_{index}"] = None

                            if f"operatrice_svolta_{index}" not in st.session_state:
                                st.session_state[f"operatrice_svolta_{index}"] = None

                            col1, col2 = st.columns(2)

                            presentato_a = col1.checkbox("Presentato/a?", value=st.session_state[f"presentato_{index}"], key=f"presentato_{index}_widget")
                            importo_pagato = col2.number_input("Importo pagato", min_value=0.0, value=st.session_state[f"importo_{index}"], key=f"importo_{index}_widget")
                            
                            follow_up = st.selectbox("Follow up?", ["No", "Si"], index=0, key=f"followup_{index}_widget")
                            data_followup = st.date_input("Data follow up", value=None, key=f"data_followup_{index}_widget")
                            ora_followup = st.time_input("Ora follow up", value=None, key=f"ora_followup_{index}_widget")  # Nessun orario predefinito

                            # Importo acconto senza preimpostazione
                            acconto_importo = st.number_input("Importo acconto", min_value=0.0, value=None, key=f"acconto_importo_{index}_widget")

                            # Modalità pagamento senza preimpostazione
                            modalita_acconto = st.selectbox("Modalità pagamento acconto", ["", "Carta", "Contanti", "Pagodil"], key=f"modalita_acconto_{index}_widget")
                            modalita_saldo = st.selectbox("Modalità pagamento saldo", ["", 'Contanti', 'Carta di credito', 'Pagodil'], key=f"modalita_saldo_{index}_widget")

                            # Operatrice senza preimpostazione
                            operatrice_svolta = st.selectbox("Nome operatrice consulenza svolta", [""] + operatrice_consulenza_options, key=f"operatrice_svolta_{index}_widget")

                            # Bottone per aggiornare
                            submit_button = st.form_submit_button(f"Aggiorna {row['Nome']} {row['Cognome']}")

                            if submit_button:
                                st.session_state[f"presentato_{index}"] = presentato_a
                                st.session_state[f"importo_{index}"] = importo_pagato

                                datetime_followup = datetime.combine(data_followup, ora_followup)

                                st.session_state[f"data_followup_{index}"] = datetime_followup
                                st.session_state[f"acconto_importo_{index}"] = acconto_importo
                                st.session_state[f"modalita_acconto_{index}"] = modalita_acconto
                                st.session_state[f"modalita_saldo_{index}"] = modalita_saldo
                                st.session_state[f"operatrice_svolta_{index}"] = operatrice_svolta

                                updated_fields = {
                                    'Presentato/a?': st.session_state[f"presentato_{index}"],
                                    'Importo pagato': st.session_state[f"importo_{index}"],
                                    'Importo Acconto': st.session_state[f"acconto_importo_{index}"],
                                    'ModalitàPagamentoAcc.': st.session_state[f"modalita_acconto_{index}"],
                                    'OperatriceConsulenza': st.session_state[f"operatrice_svolta_{index}"],
                                    'ModalitàPagamentoMain': st.session_state[f"modalita_saldo_{index}"],
                                    'AppRifissato': follow_up  # Aggiorna AppRifissato con il valore di Follow up
                                }
                                
                                if st.session_state[f"presentato_{index}"] is not None:
                                    updated_fields['Presentato/a?'] = st.session_state[f"presentato_{index}"]

                                if st.session_state[f"importo_{index}"] is not None:
                                    updated_fields['Importo pagato'] = st.session_state[f"importo_{index}"]

                                if acconto_importo is not None:
                                    updated_fields['Importo Acconto'] = acconto_importo

                                if modalita_acconto != "":
                                    updated_fields['ModalitàPagamentoAcc.'] = modalita_acconto

                                if modalita_saldo != "":
                                    updated_fields['ModalitàPagamentoMain'] = modalita_saldo

                                if operatrice_svolta != "":
                                    updated_fields['OperatriceConsulenza'] = operatrice_svolta

                                if follow_up:
                                    updated_fields['AppRifissato'] = follow_up  # Valore "Si" o "No" da aggiornare

                                # Se l'utente ha inserito una data di follow-up, aggiorna anche quella
                                if data_followup is not None and ora_followup is not None:
                                    datetime_followup = datetime.combine(data_followup, ora_followup)
                                    updated_fields['Data AppRifissato'] = datetime_followup.isoformat() + 'Z'
                                record_id = row['id']
                                update_airtable_record(record_id, updated_fields)

                            st.divider()

if __name__ == "__main__":
    app()
