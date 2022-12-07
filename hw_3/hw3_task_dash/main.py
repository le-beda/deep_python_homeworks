import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import json
import statsmodels.api as sm

df = pd.read_csv("crimedata.csv")

crimes = ["murders", "rapes", "arsons", "autoTheft", "larcenies", "burglaries", "assaults", "robberies"]

state_data = df.groupby("state")[crimes].agg("sum").reset_index()
mean_state_data = df.groupby("state")[["medIncome", "householdsize", "ViolentCrimesPerPop", "nonViolPerPop"]].agg(
    "mean").reset_index()
state_data = state_data.merge(mean_state_data, on="state")

# Sidebar selectors

crime_selector = st.sidebar.radio(
    'Pick a crime type to examine:',
    sorted(crimes)
)

states_selector = st.sidebar.multiselect(
    'Select states:',
    sorted(state_data.state), default=state_data.state[0:-1:3]  # каждый третий штат по умолчанию
)

whole_country = st.sidebar.checkbox(
    'Or you can see the whole country instead', help="check this box if you want to disregard the selection above"
)

# Graphics

st.title("Crime analysis of America")

st.text(f"Violent and non violent crimes overall look something like this")

fig = px.density_contour(df, x="ViolentCrimesPerPop", y="nonViolPerPop")
fig.update_layout(xaxis={"title": "Violent Crimes"},
                  yaxis={"title": "Non Violent Crimes"})
fig  # красиво, но что это ... (сложно придумать пять разных графиков)

# st.dataframe(df)
# st.dataframe(state_data)

show_data = state_data
show_location = "USA"

if not whole_country:
    show_data = state_data.loc[state_data.state.isin(states_selector), :]
    show_location = ', '.join(states_selector)

st.text(f"Now let's look at instances of {crime_selector} in {show_location}")

st.subheader("Amount comparison on a map")
fig_map = px.choropleth(show_data, locations='state',
                        locationmode="USA-states", color=crime_selector,
                        color_continuous_scale="Viridis",
                        scope="usa",
                        )
fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig_map

st.subheader("Amount comparison (percentagewise)")
fig_pie = px.pie(show_data, values=crime_selector, names='state', color_discrete_sequence=px.colors.sequential.RdBu)
fig_pie.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig_pie

st.subheader("Median income relation")
income = st.slider(
    'Select income:',
    int(show_data.medIncome.min()), int(show_data.medIncome.max()),
    (int(show_data.medIncome.min() + 2000), int(show_data.medIncome.max() - 2000))
)

fig_sc = px.scatter(show_data[(show_data.medIncome <= income[1]) & (show_data.medIncome >= income[0])],
                    y=crime_selector, x='medIncome', trendline="ols",
                    color_discrete_sequence=px.colors.sequential.Magma, )
fig_sc.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, xaxis={"title": "Median Income, $"},
                     yaxis={"title": f"{crime_selector}, instances"})
fig_sc

st.subheader("Household size relation")
fig_hist = px.histogram(show_data[(show_data.medIncome <= income[1]) & (show_data.medIncome >= income[0])],
                        x='householdsize', color_discrete_sequence=px.colors.sequential.Magenta)
fig_hist.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, bargap=0.2, yaxis={"title": f"{crime_selector} count"},
                       xaxis={"title": f"Household Size"})
fig_hist

st.title("🎄🎄🎄")
snowing = st.radio("Excited for winter holidays?", ["no", "YES!"], horizontal=True)
if snowing == "YES!":
    st.snow()
