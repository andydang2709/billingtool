import pandas as pd
import streamlit as st

st.title('Billing Tool')

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, usecols=['First Name', 'Last Name', 'Check In', 'Check Out', 'Room Type'])

    def clean_data(df):
        # Drop rows with missing data in column: 'First Name'
        df = df.dropna(subset=['First Name'])
        # Change column type to datetime64[ns] for column 'Check In' and 'Check Out'
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
    commuter_charge_per_day = 5

    # Ask for commuter groups information
    commuter_groups = st.number_input("Number of commuter groups", min_value=0, step=1)

    commuter_info = []
    for i in range(commuter_groups):
        st.subheader(f"Commuter Group {i + 1}")
        num_commuters = st.number_input(f"Number of commuters in group {i + 1}", min_value=0, step=1, key=f"num_commuters_{i}")
        commuter_check_in = st.date_input(f"Commuter Group {i + 1} Check-In Date", key=f"commuter_check_in_{i}")
        commuter_check_out = st.date_input(f"Commuter Group {i + 1} Check-Out Date", key=f"commuter_check_out_{i}")

        commuter_days_stayed = (commuter_check_out - commuter_check_in).days
        commuter_total_charge = num_commuters * commuter_days_stayed * commuter_charge_per_day

        commuter_info.append({
            'num_commuters': num_commuters,
            'commuter_check_in': commuter_check_in,
            'commuter_check_out': commuter_check_out,
            'commuter_charge_per_day': commuter_charge_per_day,
            'commuter_total_charge': commuter_total_charge,
            'commuter_days_stayed': commuter_days_stayed
        })

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

        if (linen_option):
            linen_description = f"{row['People']} people * ${linen_charge_per_person_per_night} Linen Charge * {int(row['Item Count'] / row['People'])} nights"
            output_data.append({
                'Item Count': row['Item Count'],
                'Unit Amount': linen_charge_per_person_per_night,
                'Charge Amount': linen_charge,
                'Date': row['Date'],
                'Description': linen_description
            })

    # Add commuter charges for each group
    for commuter in commuter_info:
        if commuter['num_commuters'] > 0:
            commuter_description = f"{commuter['num_commuters']} commuters * ${commuter['commuter_charge_per_day']} Commuter Charge * {commuter['commuter_days_stayed']} days"
            output_data.append({
                'Item Count': commuter['commuter_days_stayed'],
                'Unit Amount': commuter['commuter_charge_per_day'],
                'Charge Amount': commuter['commuter_total_charge'],
                'Date': commuter['commuter_check_out'],
                'Description': commuter_description
            })

    output_df = pd.DataFrame(output_data)

    # Sort and group the data
    room_type_order = {
        'Single': 1,
        'Double': 2,
        'Single Suite': 3,
        'Double Suite': 4,
        'Linen Charge': 5
    }
    output_df['Group'] = output_df['Description'].apply(lambda x: 'Linen Charge' if 'Linen Charge' in x else x.split(' ')[2])
    output_df['Group Order'] = output_df['Group'].map(room_type_order)
    output_df = output_df.sort_values(by=['Group Order', 'Date'])

    # Drop helper columns
    output_df = output_df.drop(columns=['Group', 'Group Order'])

    # Reorder columns
    output_df = output_df[['Item Count', 'Unit Amount', 'Charge Amount', 'Date', 'Description']]

    st.dataframe(output_df, use_container_width=True)
else:
    st.write("Please upload a CSV file to proceed.")
