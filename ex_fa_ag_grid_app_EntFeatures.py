# Import libraries
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas as pd
import warnings

# Load data from csv file and create a dataframe
@st.cache_data
def load_data():
    # Load data from CSV (assuming 'ex_fake_data.csv' is in your working directory)
    data = pd.read_csv('ex_fake_data.csv')
    return data

data = load_data()

# Convert the data to a pandas DataFrame
df = pd.DataFrame(data)

# Pivot the data based on 'BU Level 1'
pivoted_df = df.pivot_table(index=['Factor L1', 'Factor L2', 'Factor L3', 'Factor L4'],
                            columns='BU Level 1', values='Value', aggfunc='sum')

# Flatten the multi-level column index created by pivot_table
pivoted_df.columns = pivoted_df.columns.get_level_values(0)

# Reset the index to turn the multi-index into columns
pivoted_df.reset_index(inplace=True)

# Add the invisible comment columns with sequential comments
pivoted_df['Upstream_Comments'] = [f"Upstream Comment {i+1}" for i in range(len(pivoted_df))]
pivoted_df['Prod. Sol._Comments'] = [f"Prod Sol Comment {i+1}" for i in range(len(pivoted_df))]

df = pivoted_df

# Initialize session state if not already initialized
if 'grid_response_stag' not in st.session_state :
    st.session_state['grid_response_stag'] = {}  # Initialize with an empty dictionary

# Before AgGrid - Show the session state values
# Note: variable names have _stag as suffix (state after grid i.e. stag)
# Only proceed if grid_response_stag has a value (i.e., AgGrid has been rendered)

st.write("//*** This is from Session State - Before AgGrid ***//")

if st.session_state['grid_response_stag']:

    # Get and display row 1 data from grid response stored in session state
    st.write("*** Session State - Showing Row 1 Data as a sample (without selection) ***")
    grid_response_stag = st.session_state.get('grid_response_stag', {})

    if 'gridOptions' in grid_response_stag:
        grid_options = grid_response_stag['gridOptions']
        if 'rowData' in grid_options:
            row_data = grid_options['rowData']

            # Ensure that row 1 exists and display it
            if len(row_data) > 0:
                row_1_data = row_data[0]  # Get row 1 (index 0)
                
                # Remove 'Upstream_Comments' and 'Prod. Sol._Comments' from row data
                columns_to_remove = ['Upstream_Comments', 'Prod. Sol._Comments']
                filtered_row_1_data = {k: v for k, v in row_1_data.items() if k not in columns_to_remove}
                
                # Extract only the values from the filtered row 1 (now without the comment columns)
                row_1_values = filtered_row_1_data.values()
                
                # Filter out any unwanted values like 0 or empty values
                cleaned_row_1_values = [str(value) for value in row_1_values if value not in [0, '0', None, '']]
                
                # Join the cleaned values into a single string, separated by commas
                row_1_values_str = ", ".join(cleaned_row_1_values)
                
                # Display the cleaned row 1 values
                st.write(row_1_values_str)  # Display row 1 values in one line
            else:
                st.write("No data found in rowData.")
        else:
            st.write("No rowData found in gridOptions.")
    else:
        st.write("No gridOptions found in gridResponse.")

    # Show selected row and cell details from the grid
    st.write("*** Session State - Showing Selected Data ***")
    if 'gridState' in grid_response_stag:
        grid_state = grid_response_stag['gridState']
        
        # Display selected rows
        row_selection_stag = grid_state.get('rowSelection', None)
        if row_selection_stag:
            st.write(f"Selected Row(s): {row_selection_stag}")
            selected_rows_stag = df.iloc[row_selection_stag]
            # st.write(f"Selected Rows Data: {selected_rows_stag}")

        # Display selected cell details
        cell_selection_stag = grid_state.get('focusedCell', None)
        if cell_selection_stag:
            col_id_stag = cell_selection_stag.get('colId')
            row_index_stag = cell_selection_stag.get('rowIndex')
            row_pinned_stag = cell_selection_stag.get('rowPinned')
            
            if row_index_stag is not None and col_id_stag is not None:
                cell_value_stag = df.at[row_index_stag, col_id_stag]
                # Note: as this value after AgGrid is rendered and this code is before, the previous selected values are shown.
                # not the latest value
                st.write(f"Selected Cell - Row Index: {row_index_stag}, Column Id: {col_id_stag}, Row Pinned: {row_pinned_stag}, (Value: {cell_value_stag})")
    else:
        st.write("Session State - No selections yet")
else:
    st.write("AgGrid not rendered yet.")

# From here code to render data for AgGrid starts
# JavaScript code to style rows based on the row number (even or odd)
jscode = JsCode("""
    function(params) {
        if (params.node.rowIndex % 2 === 0) {
            return {
                'backgroundColor': 'lightblue',
                'color': 'black'
            };
        } else {
            return {
                'backgroundColor': 'white',
                'color': 'black'
            };
        }
    };
""")

# JavaScript code to change cell color to yellow on edit
cell_edit_jscode = JsCode("""
    function(event) {
        var updatedNode = event.node;
        var colId = event.colDef.field;
        var rowIndex = updatedNode.rowIndex;

        var cellElement = event.api.getCellRendererInstances({ rowNodes: [updatedNode], columns: [colId] })[0].eGui;
        if (cellElement) {
            cellElement.style.backgroundColor = 'yellow';
        }
    }
""")

# JavaScript code to handle cell click event for Prod. Sol. and Upstream columns
cell_click_jscode = JsCode("""
    function(params) {
        var clickedCol = params.column.getColId();
        var cellValue = params.value;
        var rowIndex = params.rowIndex;

        // var columnsToCheck = ['Prod. Sol.', 'Upstream'];
        var columnsToCheck = ['Upstream'];

        if (columnsToCheck.includes(clickedCol)) {
            var comment = '';
            if (clickedCol === 'Upstream') {
                comment = params.node.data['Upstream_Comments'];
            } else if (clickedCol === 'Prod. Sol.') {
                comment = params.node.data['Prod. Sol._Comments'];
            }

            window.parent.postMessage({
                type: 'cellClick', 
                column: clickedCol, 
                row: rowIndex, 
                comment: comment
            }, '*');

            alert("Comment: " + comment + " :-: " + "You clicked the '" + clickedCol + "' column (Row: " + rowIndex + ") with value: " + cellValue);
        }
    }
""")

# Configure grid options using GridOptionsBuilder
builder = GridOptionsBuilder.from_dataframe(df)
builder.configure_pagination(enabled=True)
builder.configure_selection(selection_mode='single', use_checkbox=False)

# Disable sorting for all columns
for column in df.columns:
    builder.configure_column(column, sortable=False)

# Enable auto-sizing for all columns
builder.configure_columns(autoSize=True)

# Make "Prod. Sol." and "Upstream" columns editable
editable_columns = ['Prod. Sol.', 'Upstream', 'Upstream_Comments', 'Prod. Sol._Comments']
for column in editable_columns:
    if column in df.columns:
        builder.configure_column(column, editable=True)

# Hide the comment columns
builder.configure_column('Upstream_Comments', hide=True)
builder.configure_column('Prod. Sol._Comments', hide=True)

builder.configure_column('Factor L1', pinned='left')
builder.configure_column('Factor L2', pinned='left')
builder.configure_column('Factor L3', pinned='left')

# Disable column visibility toggling by suppressing the columns tool panel and virtualisation
builder.configure_grid_options(
    suppressColumnVirtualisation=True,
    suppressColumnsToolPanel=True
)

# Set the 'domLayout' property to 'autoHeight'
grid_options = builder.build()
grid_options['domLayout'] = 'autoHeight'
grid_options['getRowStyle'] = jscode

# Add the event for cell value changes
grid_options['onCellValueChanged'] = cell_edit_jscode
grid_options['onCellClicked'] = cell_click_jscode  # Attach the cell click handler

st.markdown(
    "<h2 style='color: red; font-weight: bold;'>Factor Analysis using AgGrid</h2>", 
    unsafe_allow_html=True
)
# st.button("Save")

return_value = AgGrid(df, gridOptions=grid_options, fit_columns_on_grid_load=True, editable=True,
                      allow_unsafe_jscode=True)


# After AgGrid - Show the session state values
st.write("//*** This is from Session State - After AgGrid ***//")
# Note: variable names have _stag as suffix (state after grid i.e. stag)

# Extract the grid response from the return value
grid_response_stag = return_value.get('grid_response', {})

# Store the grid response in session state
st.session_state['grid_response_stag'] = grid_response_stag

# Get and display row 1 data from grid response stored in session state
st.write("*** Session State - Showing Row 1 Data as a sample (without selection) ***")
grid_response_stag = st.session_state.get('grid_response_stag', {})

if 'gridOptions' in grid_response_stag:
    grid_options = grid_response_stag['gridOptions']
    if 'rowData' in grid_options:
        row_data = grid_options['rowData']

        # Ensure that row 1 exists and display it
        if len(row_data) > 0:
            row_1_data = row_data[0]  # Get row 1 (index 0)
            
            # Remove 'Upstream_Comments' and 'Prod. Sol._Comments' from row data
            columns_to_remove = ['Upstream_Comments', 'Prod. Sol._Comments']
            filtered_row_1_data = {k: v for k, v in row_1_data.items() if k not in columns_to_remove}
            
            # Extract only the values from the filtered row 1 (now without the comment columns)
            row_1_values = filtered_row_1_data.values()
            
            # Filter out any unwanted values like 0 or empty values
            cleaned_row_1_values = [str(value) for value in row_1_values if value not in [0, '0', None, '']]
            
            # Join the cleaned values into a single string, separated by commas
            row_1_values_str = ", ".join(cleaned_row_1_values)
            
            # Display the cleaned row 1 values
            st.write(row_1_values_str)  # Display row 1 values in one line
        else:
            st.write("No data found in rowData.")
    else:
        st.write("No rowData found in gridOptions.")
else:
    st.write("No gridOptions found in gridResponse.")

# Show selected row and cell details from the grid
st.write("*** Session State - Showing Selected Data ***")
if 'gridState' in grid_response_stag:
    grid_state = grid_response_stag['gridState']
    
    # Display selected rows
    row_selection = grid_state.get('rowSelection', None)
    if row_selection:
        st.write(f"Selected Row(s): {row_selection}")
        selected_rows = df.iloc[row_selection]

    # Display selected cell details
    cell_selection = grid_state.get('focusedCell', None)
    if cell_selection:
        col_id = cell_selection.get('colId')
        row_index = cell_selection.get('rowIndex')
        row_pinned = cell_selection.get('rowPinned')
        
        if row_index is not None and col_id is not None:
            cell_value = df.at[row_index, col_id]
            st.write(f"Selected Cell - Row Index: {row_index}, Column Id: {col_id}, Row Pinned: {row_pinned}, (Value: {cell_value})")
else:
    st.write("Session State - No selections yet")

# Store the edited data in session state (handle if it is a DataFrame)
edited_data = return_value.get('data', [])

# Check if edited_data is a DataFrame, and then handle accordingly
if isinstance(edited_data, pd.DataFrame):
    st.session_state['edited_data'] = edited_data if not edited_data.empty else None
else:
    st.session_state['edited_data'] = edited_data

# Display the session state for debugging
# Commented as this was showing lot of data. Uncomment to understand/troubleshoot
# st.write("Session State: ", st.session_state)

# Display row and cell selections
st.write("//*** From AgGrid - Show Row 1 data and Selected Data ***// ")

st.write("*** Showing Row 1 Data as a sample (without selection) ***")
grid_options = return_value.get('grid_response', {}).get('gridOptions', {})
if 'rowData' in grid_options:
    row_data = grid_options['rowData']
    
    # Ensure that row 1 exists and display it
    if len(row_data) > 0:
        row_1_data = row_data[0]  # Get row 1 (index 0)
        
        # Remove 'Upstream_Comments' and 'Prod. Sol._Comments' from row data
        columns_to_remove = ['Upstream_Comments', 'Prod. Sol._Comments']
        filtered_row_1_data = {k: v for k, v in row_1_data.items() if k not in columns_to_remove}
        
        # Extract only the values from the filtered row 1 (now without the comment columns)
        row_1_values = filtered_row_1_data.values()
        
        # Filter out any unwanted values like 0 or empty values
        cleaned_row_1_values = [str(value) for value in row_1_values if value not in [0, '0', None, '']]
        
        # Join the cleaned values into a single string, separated by commas
        row_1_values_str = ", ".join(cleaned_row_1_values)
        st.write(row_1_values_str)  # Display cleaned row 1 values in one line
    else:
        st.write("No data found in rowData.")
else:
    st.write("No rowData found in gridOptions.")

st.write("*** Showing Selected Data ***")
if 'gridState' in return_value.grid_response:
    row_selection = return_value.grid_response['gridState'].get('rowSelection', None)
    if row_selection:
        st.write(f"Selected Row(s): {row_selection}")
        selected_rows = df.iloc[row_selection]

    cell_selection = return_value.grid_response['gridState'].get('focusedCell', None)
    if cell_selection:
        col_id = cell_selection.get('colId')
        row_index = cell_selection.get('rowIndex')
        rowPinned = cell_selection.get('rowPinned')
        if row_index is not None and col_id is not None:
            cell_value = df.at[row_index, col_id]
            st.write(f"Selected Cell - Row Index: {row_index}, Column Id: {col_id}, Row Pinned: {rowPinned}, (Value: {cell_value})")
else:
    st.write("No selections yet")

# Capture the edited data (if any) and display
if 'edited_data' in st.session_state and st.session_state['edited_data'] is not None:
    st.write("//*** Edited Data: ***//")
    st.write(st.session_state['edited_data'])

# Suppress FutureWarnings for deprecation
warnings.filterwarnings("ignore", category=FutureWarning)

# Below code is work in progress
# Handle the message from JavaScript (cell click event)
# message = st.query_params  # Change this line to use st.query_params
# if 'cellClick' in message:
#     column = message['cellClick'][0]
#     row = int(message['row'][0])  # Make sure the row index is treated as an integer
#     comment = message['comment'][0]  # Get the comment from the message
#     st.write(f"You clicked on the '{column}' column in row {row}.")
#     st.write(f"Corresponding comment: {comment}")

#     # Show a text input for editing the clicked cell value
#     cell_value = df.at[row, column]
#     user_input = st.text_input(f"Edit {column} value:", value=cell_value)
#     if user_input:
#         df.at[row, column] = user_input  # Update the dataframe with the new value
