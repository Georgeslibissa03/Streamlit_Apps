# Importation des librairies
import streamlit as st
from pandas_datareader.data import DataReader
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import date
import plotly.express as px
import plotly.tools as tls

# URLs pour les indices boursiers
url_sp500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"  # USA
url_cac40 = "https://en.wikipedia.org/wiki/CAC_40"  # Paris
url_ftse100 = "https://en.wikipedia.org/wiki/FTSE_100_Index"  # Londres
url_nikkei = "https://topforeignstocks.com/indices/the-components-of-the-nikkei-225-index/"  # Tokyo
url_dax = "https://en.wikipedia.org/wiki/DAX"  # Berlin

# Fonction pour lire les tables en toute sécurité
def read_table(url, index):
    try:
        df = pd.read_html(url)[index]
        st.success(f"Table lue avec succès depuis {url}.")
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture de la table à partir de {url} : {e}")
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur

# Chargement et traitement des données pour chaque indice boursier
dax = read_table(url_dax, 3)
if 'Company' in dax.columns and 'Ticker symbol' in dax.columns:
    dax['NameOfStock'] = dax['Company'] + "_" + dax['Ticker symbol']

nikkei = read_table(url_nikkei, 0)
if 'Company Name' in nikkei.columns and 'Code' in nikkei.columns:
    nikkei['Company Name'] = nikkei['Company Name'].replace(",", "", regex=True)  # Supprimer les virgules
    nikkei['NameOfStock'] = nikkei['Company Name'] + "_" + nikkei['Code'].astype(str) + ".T"

sp500 = read_table(url_sp500, 0)
if 'Security' in sp500.columns and 'Symbol' in sp500.columns:
    sp500['NameOfStock'] = sp500['Security'] + "_" + sp500['Symbol']

cac40 = read_table(url_cac40, 3)
if 'Company' in cac40.columns and 'Ticker' in cac40.columns:
    cac40['NameOfStock'] = cac40['Company'] + "_" + cac40['Ticker']

ftse100 = read_table(url_ftse100, 3)
if 'Company' in ftse100.columns and 'EPIC' in ftse100.columns:
    ftse100['NameOfStock'] = ftse100['Company'] + "_" + ftse100["EPIC"]

# Fonction pour charger les données de prix d'une action
@st.cache_data
def load_data(symbol, start_date, end_date):
    try:
        stock_data = DataReader(symbol, data_source="yahoo", start=start_date, end=end_date)
        return stock_data
    except Exception as e:
        st.error(f"Erreur lors du chargement des données pour {symbol}: {e}")
        return None

# Fonction pour obtenir la liste des actions d'un marché spécifique
def list_of_stocks(market_name):
    if market_name == "SP500 (USA)":
        return sp500['NameOfStock'].to_list()
    elif market_name == "CAC 40 (France)":
        return cac40['NameOfStock'].to_list()
    elif market_name == "FTSE 100 (Angleterre)":
        return ftse100['NameOfStock'].to_list()
    elif market_name == "NIKKEI (Japon)":
        return nikkei['NameOfStock'].to_list()
    else:
        return dax['NameOfStock'].to_list()

# Interface utilisateur
st.title("📈 Analyse des Marchés Boursiers")
st.sidebar.header("Configuration de l'Analyse")

# Choix du marché boursier
market = st.sidebar.selectbox('Choisissez un Marché Boursier', ["SP500 (USA)", "CAC 40 (France)", "FTSE 100 (Angleterre)", "NIKKEI (Japon)", "DAX (Allemagne)"])

# Récupération de la liste des actions pour le marché choisi
stocks_list = list_of_stocks(market_name=market)

# Choix d'une action à analyser
stock = st.sidebar.selectbox('Choisissez une Action à Analyser', stocks_list)

# Choix de la période d'analyse
st.sidebar.write('Choisissez une Période d\'Analyse :')
date1 = st.sidebar.date_input("Date de Début", value=date(2017, 1, 1))
date2 = st.sidebar.date_input("Date de Fin", value=date(2024, 1, 1))

# Choix des moyennes mobiles
st.sidebar.header("Paramètres des Moyennes Mobiles")
short = st.sidebar.slider("Moyenne Mobile Courte (jours)", min_value=1, max_value=200, value=20)
long = st.sidebar.slider("Moyenne Mobile Longue (jours)", min_value=1, max_value=200, value=100)

# Récupération des données boursières
df = load_data(symbol=stock.split("_")[1], start_date=date1, end_date=date2)

if df is not None:
    # Affichage des données brutes si l'option est cochée
    if st.sidebar.checkbox("Afficher les Données Brutes", False):
        st.subheader(f"Données de {stock.split('_')[0]}")
        st.write(df)

    # Création des graphiques
    st.header(f"Analyse de {stock.split('_')[1]}")
    
    # Boxplot des prix
    box = px.box(df, y="Close", title=f"{stock.split('_')[1]} - Prix de Clôture", color_discrete_sequence=['#1f77b4'])
    st.plotly_chart(box, use_container_width=True)

    # Graphique du volume
    volume_chart = px.line(df.reset_index(), x="Date", y="Volume", title=f"{stock.split('_')[1]} - Volume", color_discrete_sequence=['#ff7f0e'])
    st.plotly_chart(volume_chart, use_container_width=True)

    # Calcul des moyennes mobiles
    short_rolling = df['Close'].rolling(window=short).mean()
    long_rolling = df['Close'].rolling(window=long).mean()

    # Calcul des signaux d'achat et de vente
    df['Signal'] = 0.0
    df['Signal'] = np.where(short_rolling > long_rolling, 1.0, 0.0)
    df['Position'] = df['Signal'].diff()

    # Tracé des données avec matplotlib
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Close'].index, df['Close'], label='Prix de Clôture', color='blue')
    ax.plot(short_rolling.index, short_rolling, label=f'{short} jours Rolling', color='orange')
    ax.plot(long_rolling.index, long_rolling, label=f'{long} jours Rolling', color='green')

    # Tracé des signaux d'achat et de vente
    ax.plot(df[df['Position'] == 1].index, short_rolling[df['Position'] == 1], '^', markersize=15, color='black', label='Acheter')
    ax.plot(df[df['Position'] == -1].index, short_rolling[df['Position'] == -1], 'v', markersize=15, color='red', label='Vendre')
    
    # Configuration des axes et légende
    ax.set_xlabel('Date')
    ax.set_ylabel('Prix de Clôture ($)')
    ax.set_title(f'Analyse des Moyennes Mobiles pour {stock.split("_")[1]}')
    ax.legend()
    ax.grid()

    # Conversion et affichage avec Plotly
    plotly_fig = tls.mpl_to_plotly(fig)
    st.plotly_chart(plotly_fig, use_container_width=True)
else:
    st.warning("Aucune donnée disponible pour l'action sélectionnée.")
