import streamlit as st 
import datetime
import pandas as pd 
from streamlit_folium import st_folium
import ast
import folium
import numpy as np

# Set the page layout to wide mode for better display
st.set_page_config(layout="wide", page_title = "Performance Analyse- Ein Fallbeispiel von Uber Reports.")

# Import data from CSV file containing relevant columns
df = pd.read_csv("data.csv") 

# Define a function to convert string entries back to their original format using ast.literal_eval
def redo_type(x):
    # Check if the entry x is not NaN
    if pd.notna(x):
        try:
            # Evaluate the string representation to convert it back to its original format (e.g., tuple)
            return ast.literal_eval(x)
        except(ValueError, SyntaxError):
            # If conversion fails, return the original value
            return x
    else:
        # If x is NaN, return np.nan
        return np.nan

# Apply the redo_type function to columns 'Abhol_geo' and 'Ziel_geo' to restore original types
df['Abhol_geo'] = df['Abhol_geo'].apply(redo_type)
df['Ziel_geo'] = df['Ziel_geo'].apply(redo_type)

# Sidebar input for driver selection
Drivers_Name = st.sidebar.selectbox(
    "Fahrer", 
    options=['Bxter Bustermann', 'Cxter Custermann', 'Dxter Dustermann', 'Exter Eustermann', 'Fxter Fustermann', 
             'Gxter Gustermann', 'Hxter Hustermann', 'Ixter Iustermann', 'Jxter Justermann', 'Kxter Kustermann', 
             'Lxter Lustermann', 'Mxter Mustermann', 'Nxter Nustermann', 'Oxter Oustermann', 'Pxter Pustermann']
)

# Set default start and end dates for filtering
Aug_1 = datetime.date(2024, 8, 1)
Sep_1 = datetime.date(2024, 9, 1)
date = st.sidebar.date_input("Umsatzdatum Auswählen", value=(Aug_1, Sep_1), format="DD.MM.YYYY")

# Initialize start and end dates as None
start_date = None
end_date = None

# Convert selected date range into formatted start and end dates
if isinstance(date, tuple) and len(date) == 2:
    start_date = date[0].strftime('%d.%b')
    end_date = date[1].strftime('%d.%b')
    try:
        # Display header with formatted driver name and date range
        st.header(f"Performance von :green[_{Drivers_Name}_]  von :red[_{date[0].strftime('%d')}_] bis :red[_{date[1].strftime('%d %b')}_]")
    except Exception as e:
        # Show error if formatting fails
        st.error(f"An error occurred: {str(e)}")
else:
    # Warning message if end date is not selected
    st.sidebar.warning("Bitte ein Enddatum auswählen.")

# Initialize the Folium map centered on Frankfurt
frankfurt_Map = folium.Map(location=(50.1071, 8.6638), zoom_start=10)

# Function to add pickup and destination markers and draw a line between them
def add_marker_and_line(row):
    # Check for valid pickup location (latitude, longitude tuple)
    if isinstance(row['Abhol_geo'], tuple) and len(row['Abhol_geo']) == 2:
        # Add a green marker for the pickup location with distance tooltip and fare info popup
        folium.Marker(
            location=row['Abhol_geo'],
            icon=folium.Icon(color="green", icon="arrow-up"),
            popup=folium.Popup(f"Fahrterlös : {row['Fahrt_Umsatz']} €\n Fahrtdistanz: {row['Fahrtdistanz']} KM", max_width=170),
            tooltip="Klick für Mehr Info! "
        ).add_to(frankfurt_Map)

    # Check for valid destination location (latitude, longitude tuple)
    if isinstance(row['Ziel_geo'], tuple) and len(row['Ziel_geo']) == 2:
        # Add a red marker for the destination with distance tooltip and fare info popup
        folium.Marker(
            location=row['Ziel_geo'],
            icon=folium.Icon(color='red', icon='arrow-down'),
            popup=folium.Popup(f"Fahrterlös : {row['Fahrt_Umsatz']} €\n Fahrtdistanz: {row['Fahrtdistanz']} KM", max_width=170),
            tooltip="Klick für Mehr Info! "
        ).add_to(frankfurt_Map)

        # Draw a line between pickup and destination locations if both are valid
        if isinstance(row['Abhol_geo'], tuple) and isinstance(row['Ziel_geo'], tuple):
            folium.PolyLine(
                locations=[row['Abhol_geo'], row['Ziel_geo']],
                color="red",
                weight=2.5,
                opacity=1
            ).add_to(frankfurt_Map)

# Define two columns for displaying driver metrics and map
col1, col2 = st.columns((1, 5))

with col1:
    # Display driver metrics including ratings, acceptance rate, online hours, and completed trips
    st.metric("##### Fahrerbewertungen", value=df[df["Pseudo_Drivers_Name"] == Drivers_Name]["Fahrer_Bewertung"].unique(), delta="Ø von 500 Bewertungen")
    st.divider()
    
    Annahmerate = df[df["Pseudo_Drivers_Name"] == Drivers_Name]["Annahmerate"].unique() * 100
    st.metric("##### Annahmerate", value=f"{int(Annahmerate)} %", delta="80 % Vorausgesetzt")
    st.divider()
    
    Online_Stunden = df[df["Pseudo_Drivers_Name"] == Drivers_Name]["Online"].unique()
    st.metric("##### Online Stunden", value=int(Online_Stunden), delta=f"Überstunden {(Online_Stunden) - 173}")
    st.divider()
    
    Auftrag = df[df["Pseudo_Drivers_Name"] == Drivers_Name]["Abgeschlossene_Fahrten"].unique()
    st.metric("##### Abgeschlossene Fahrten", value=int(Auftrag), delta="Mindestens 200")

with col2:
    # Filter data by selected driver name and date range
    df_X = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    df_X = df_X[df_X["Pseudo_Drivers_Name"] == Drivers_Name]
    
    # Calculate total revenue, promotions, driver share, and company share
    Umsatz = df_X["Fahrt_Umsatz"].sum().round(2)
    Aktion = df_X["Aktion"].sum().round(2)
    Fahrer_Anteil = ((Umsatz + Aktion) * 0.45).round(2)
    Unternehmer_Anteil = ((Umsatz + Aktion) * 0.55).round(2)
    
    # Set result text based on revenue threshold
    result = "Weniger als 7K" if Umsatz <= 7000 else "Mehr als 7K"
    
    # Display calculated metrics across four columns
    col1, col2, col3, col4 = st.columns((1, 1, 1, 1))
    with col1:
        st.metric("##### Gesamtumsatz", value=Umsatz + Aktion, delta=result)
    with col2:
        st.metric("##### Davon Aktion", value=Aktion, delta="von 1600 €")
    with col3:
        st.metric("##### Fahrer Anteil", value=Fahrer_Anteil, delta="€")
    with col4:
        st.metric("##### Unternehmer Anteil", value=Unternehmer_Anteil, delta="€")
    
    # Apply function to add markers and lines on the map for filtered trips
    df_X.apply(add_marker_and_line, axis=1)
    
    # Display the map in Streamlit with specified dimensions
    st_folium(frankfurt_Map, width=1300, height=500)
