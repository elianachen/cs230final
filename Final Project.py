"""
Name:       Eliana Chen
CS230:      Section 4
Data:       McDonald_s_Reviews.csv
URL:

Description:
This program allows users to explore customer reviews of McDonald's locations across the U.S. Users can filter reviews by state and rating, see store locations on a map, view analytics, and even submit their own reviews through a sidebar form. Additional features include custom filtering, visual trends by state, and highlighted top-rated states.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="McReviews USA", layout="wide")
st.markdown("""
    <style>
    body, .main, .block-container {
        background-color: #c8102e;
        color: #FFD100;
        font-family: sans-serif;
    }
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #FFD100;
    }
    section[data-testid="stSidebar"] * {
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# Clean data
path = "McDonald_s_Reviews(in).csv"
df_mcd = pd.read_csv(path, encoding="ISO-8859-1")
df_mcd.columns = df_mcd.columns.str.strip()
df_mcd["rating"] = pd.to_numeric(df_mcd["rating"].str.extract(r'(\d+(\.\d+)?)')[0], errors="coerce")
df_mcd["review"] = df_mcd["review"].fillna("No review provided")
df_mcd = df_mcd.dropna(subset=["latitude", "longitude"])

# Extract state function
def extract_state(address):
    if pd.isna(address): return None
    for part in reversed(address.split(",")):
        for token in part.strip().split():
            if len(token) == 2 and token.isupper():
                return token
    return None

df_mcd["state"] = df_mcd["store_address"].apply(extract_state)

review_file = "submitted_reviews.csv"
if os.path.exists(review_file):
    df_extra = pd.read_csv(review_file)
    df = pd.concat([df_mcd, df_extra], ignore_index=True)
else:
    df = df_mcd.copy()

# Sidebar form for new reviews
st.sidebar.header("Submit a New Review")
with st.sidebar.form("review_form"):
    new_address = st.text_input("Store Address")
    new_rating = st.slider("Rating", 1.0, 5.0, 3.0, step=0.5)
    new_review = st.text_area("Your Review")
    new_lat = st.number_input("Latitude", value=0.0)
    new_lon = st.number_input("Longitude", value=0.0)
    submit = st.form_submit_button("Add Review")

if submit:
    new_data = pd.DataFrame({
        "store_address": [new_address],
        "rating": [new_rating],
        "review": [new_review if new_review else "No review provided"],
        "latitude": [new_lat],
        "longitude": [new_lon],
        "state": [extract_state(new_address)]
    })
    if os.path.exists(review_file):
        existing = pd.read_csv(review_file)
        new_combined = pd.concat([existing, new_data], ignore_index=True)
    else:
        new_combined = new_data
    new_combined.to_csv(review_file, index=False)
    st.sidebar.success("Review submitted!")
    df = pd.concat([df, new_data], ignore_index=True)

# Filtering function
def filter_by_rating(data, threshold=3.0): #default threshold is 3.0
    return data[data["rating"] >= threshold]

# Summary stats function
def get_summary_stats(data):
    return data["rating"].mean(), data["rating"].count() #returns average rating and total number of ratings

st.image("McDonald's — Video series - ILLO Studio.gif")

# Tabs
home_tab, explore_tab, analytics_tab = st.tabs(["Home", "Explore Reviews", "Analytics"])

with home_tab:
    st.title("Welcome to CS230 McReviews USA by Eliana")
    st.markdown("""Welcome to McReviews USA, where you can view real customer feedback from McDonald's locations all across the United States.
        Use the map and filters to search by state, rating, or address. Explore rating trends and submit your own review using the sidebar!""")
    st.subheader("What's new: The McDonald's Minecraft Meal")
    st.caption("A playful collaboration between McDonald’s and Minecraft to create an immersive, themed meal experience that bridges digital culture and brand engagement.")
    st.video("https://www.youtube.com/embed/lXGoJqft8tQ")

with explore_tab:
    st.title("Explore Reviews")
    col1, col2, col3 = st.columns([1, 1, 2]) #create 3 columns to filter (state, rating, address search)
    with col1:
        states = ['All'] + sorted(df["state"].dropna().unique()) #get unique states from the dataframe
        selected_state = st.selectbox("Select a State", states)
    with col2:
        min_rating = st.slider("Minimum Rating", 1.0, 5.0, 3.0, step=0.5) #filter reviews by minimum rating
    with col3:
        search = st.text_input("Search Address")

    df_filtered = filter_by_rating(df, min_rating)
    if selected_state != 'All':
        df_filtered = df_filtered[df_filtered["state"] == selected_state]
    if search:
        df_filtered = df_filtered[df_filtered["store_address"].str.contains(search, case=False, na=False)]

    st.subheader("Map of McDonald's Locations")
    if not df_filtered.empty:
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=df_filtered["latitude"].mean(),
                longitude=df_filtered["longitude"].mean(),
                zoom=4
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df_filtered,
                    get_position='[longitude, latitude]',
                    get_color='[200, 16, 46, 160]',
                    get_radius=8000
                )
            ]
        ))
    else:
        st.info("No matching stores found.")

    st.subheader("Reviews Table")
    if not df_filtered.empty:
        sort_choice = st.selectbox("Sort Ratings", ["Descending", "Ascending"])
        asc = sort_choice == "Ascending"
        df_sorted = df_filtered.sort_values(by=["state", "rating"], ascending=[True, asc])
        st.dataframe(df_sorted[["store_address", "state", "rating", "review"]])
    else:
        st.warning("No reviews to show.")

with analytics_tab:
    st.header("Ratings Analytics")
    avg_rating, total_reviews = get_summary_stats(df)
    col1, col2 = st.columns(2)
    col1.metric("Average Rating", round(avg_rating, 2))
    col2.metric("Total Reviews", total_reviews)

    state_avg = df.groupby("state")["rating"].mean().sort_values(ascending=False)
    rating_counts = df["rating"].value_counts().sort_index()

    st.subheader("Average Rating by State")
    fig1 = plt.figure(figsize=(10, 5))
    sns.barplot(x=state_avg.index, y=state_avg.values)
    plt.title("Average Rating by State")
    plt.xlabel("State")
    plt.ylabel("Average Rating")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    st.subheader("Rating Distribution")
    fig2 = plt.figure(figsize=(8, 4))
    sns.histplot(df["rating"], bins=10, kde=True)
    plt.title("Distribution of Ratings")
    plt.xlabel("Rating")
    plt.ylabel("Frequency")
    st.pyplot(fig2)
