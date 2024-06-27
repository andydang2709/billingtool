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
        # Change column type to datetime64[ns] for columnn 'Check In' and 'Check Out'
        df['Check In'] = pd.to_datetime(df['Check In']).dt.date
        df['Check Out'] = pd.to_datetime(df['Check Out']).dt.date
        df = df.reset_index(drop=True)
        return df

    df_clean = clean_data(df.copy())

    df_clean['Days Stayed'] = (pd.to_datetime(df_clean['Check Out']) - pd.to_datetime(df_clean['Check In'])).dt.days

    single_price = st.number_input("Input Single Room's Price", min_value=0)
    double_price = st.number_input("Input Double Room's Price", min_value=0)
    single_suite_price = single_price + 4
    double_suite_price = double_price + 4

    df_clean['Unit Price'] = df_clean['Room Type'].apply(lambda x: single_price if x == 'Single' else double_price if x == 'Double' else single_suite_price if x == 'Single Suite' else double_suite_price if x == 'Double Suite' else None)

    df_clean['Charge'] = df_clean['Days Stayed'] * df_clean['Unit Price']

    # Group the data
    total_charge_per_group = df_clean.groupby(['Check In', 'Check Out', 'Room Type', 'Unit Price']).agg(
        {'Charge': 'sum', 'Days Stayed': 'sum', 'First Name': 'count'}
    ).reset_index()

    # Rename columns
    total_charge_per_group.rename(columns={
        'Days Stayed': 'Item Count',
        'Unit Price': 'Unit Amount',
        'Charge': 'Charge Amount',
        'First Name': 'People'
    }, inplace=True)

    # Generate the description column
    total_charge_per_group['Description'] = total_charge_per_group.apply(
        lambda row: f"{row['People']} people * ${row['Unit Amount']} {row['Room Type']} * {row['Days Stayed']} nights", axis=1
    )

    # Reorder columns
    total_charge_per_group = total_charge_per_group[['Item Count', 'Unit Amount', 'Charge Amount', 'Check In', 'Check Out', 'Description']]

    st.write(total_charge_per_group)
else:
    st.write("Please upload a CSV file to proceed.")