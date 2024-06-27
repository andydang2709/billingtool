import pandas as pd
import streamlit as st

st.title('Billing Tool')

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    def clean_data(df):
        # Drop rows with missing data in column: 'First Name'
        df = df.dropna(subset=['First Name'])
        # Select columns: 'First Name', 'Last Name' and 3 other columns
        df = df.loc[:, ['First Name', 'Last Name', 'Check In', 'Check Out', 'Room Type']]
        # Change column type to datetime64[ns] for column: 'Check In'
        df = df.astype({'Check In': 'datetime64[ns]'})
        # Change column type to datetime64[ns] for column: 'Check Out'
        df = df.astype({'Check Out': 'datetime64[ns]'})
        df = df.reset_index(drop=True)
        return df

    df_clean = clean_data(df.copy())

    df_clean['Days Stayed'] = (df_clean['Check Out']-df_clean['Check In']).dt.days

    single_price = int(input("Input Single Room's Price"))
    double_price = int(input("Input Double Room's Price"))

    df_clean['Unit Price'] = df_clean['Room Type'].apply(lambda x: single_price if x == 'Single' else double_price if x == 'Double' else None)

    df_clean['Charge'] = df_clean['Days Stayed'] * df_clean['Unit Price']

    total_charge_per_group = df_clean.groupby(['Check In', 'Check Out']).agg(
        {'Charge': 'sum', 'Days Stayed': 'sum', 'Unit Price': 'first'}
    ).reset_index()

    st.write(total_charge_per_group)
else:
    st.write("Please upload a CSV file to proceed.")