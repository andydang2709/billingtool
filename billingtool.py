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
        'First Name': 'People',
        'Check Out': 'Date'
    }, inplace=True)

 # Linen charge per person per night
    linen_charge_per_person_per_night = 5

# Generate the description column and separate linen charge rows
    output_data = []
    for index, row in total_charge_per_group.iterrows():
        linen_option = st.checkbox(f"Include linen charge for group from {row['Check In']} to {row['Date']}", key=f"{row['Check In']}-{row['Date']}-{row['Room Type']}")
        linen_charge = row['People'] * linen_charge_per_person_per_night * int(row['Item Count'] / row['People']) if linen_option else 0
        total_charge = row['Charge Amount']
        description = f"{row['People']} people * ${row['Unit Amount']} {row['Room Type']} * {int(row['Item Count'] / row['People'])} nights"
        
        output_data.append({
            'Item Count': row['Item Count'],
            'Unit Amount': row['Unit Amount'],
            'Charge Amount': row['Charge Amount'],
            'Date': row['Date'],
            'Description': description
        })
        
        if linen_option:
            linen_description = f"{row['People']} people * ${linen_charge_per_person_per_night} Linen Charge * {int(row['Item Count'] / row['People'])} nights"
            output_data.append({
                'Item Count': row['Item Count'],
                'Unit Amount': linen_charge_per_person_per_night,
                'Charge Amount': linen_charge,
                'Date': row['Date'],
                'Description': linen_description
            })

    output_df = pd.DataFrame(output_data)

    # Reorder columns
    output_df = output_df[['Item Count', 'Unit Amount', 'Charge Amount', 'Date', 'Description']]

    st.write(output_df)
else:
    st.write("Please upload a CSV file to proceed.")