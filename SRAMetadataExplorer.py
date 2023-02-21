import streamlit as st  # pip/conda install streamlit
# from st_aggrid import AgGrid # pip/conda install streamlit-aggrid
import pandas as pd  # pip/conda install pandas
import plotly.express as px  # pip/conda install plotly_express
from pysradb import SRAweb  # conda install -c bioconda pysradb
import re
import os

workingDirectory = "/home/assaf/Assaf/Science/Data Science/Genomic Analysis/SRA metadata explorer"
os.chdir(workingDirectory)

# Column names to be selected or used for empty dataframe
dfColumns = ['study_accession', 'study_title', 'experiment_accession', 
           'experiment_title', 'organism_taxid ', 'organism_name', 
           'library_strategy', 'library_source', 'library_selection', 
           'library_layout', 'sample_accession', 'instrument', 
           'total_spots', 'total_size', 'run_accession', 
           'run_total_bases', 'run_total_spots', 
           'read_length']
df = pd.DataFrame(data = None, columns = dfColumns)
df_empty = pd.DataFrame(data = None, columns = dfColumns)

st.set_page_config(
    page_title = "SRA Metadata Explorer",
    page_icon = "🧬", # ":dna:",
    layout = "wide"
    )

#==== Title =====================================================
st.title("🧬 SRA Metadata Explorer") 


#==== Load/Search ===============================================
inputLayout = "not-Sidebar" # "no-Sidebar
if inputLayout == "Sidebar":
    loadSearch = st.sidebar.text_input("Enter study/experiment/sample/run accession codes or a text to  search for: ", placeholder=('SRP017942|SRP015946|SRP028720 or "Sars-Cov-2" ')) 
    
else:
    loadSearch = st.text_input("Enter study/experiment/sample/run accession codes* or text to search for**: ", placeholder=('SRP017942|SRP015946|SRP028720 or "Sars-Cov-2" ')) 
    st.markdown('''<p style=\"font-size:10px;\">*Codes can be SRP/ERP/GMP/DRP SRS/ERS/DRS/GMS SRX/ERX/GMX/DRX or SRR/ERR/GMR/DRR. For multiple codes, seperate codes by '|' (pipe symbol). </br> 
                **Enter search  text between parentheses. Search by text might take a while.</p>''', unsafe_allow_html = True)

# st.write("loadSearch = ", loadSearch)

# Check if user entered a valid code or valid search text
if loadSearch != '':
    db = SRAweb()
    if bool(re.fullmatch('".+"', loadSearch)):  # search text
        df = db.search_sra(search_str = loadSearch)
    elif bool(re.fullmatch("^\D\D\D\d+[|\D\D\D\d+|]*[\D\D\D\d+$]*", loadSearch)): # valid code or codes seperated by '|'
        df = db.sra_metadata(loadSearch)  # replace any '|' by an ' OR ' diliminator for a search with more than one code
    else:
        st.markdown('<p style="color:Red; font-size:16px;">You did not enter a valid input. Please try again.</p>', unsafe_allow_html = True)

if df is None:
    df = df_empty
    
# df = pd.read_csv('metadata2.csv')

if len(df) != 0:
    df = df.loc[:,dfColumns[:-1]]  # remove 'read_length' as it 
                                   # hasn't been added yet 
    
    # fill in a 'nan' value for missing data
    df.loc[df['total_spots'] == '', 'total_spots'] = 'nan'
    df.loc[df['run_total_spots'] == '', 'run_total_spots'] = 'nan'
    df.loc[df['total_size'] == '', 'total_size'] = 'nan'
    df.loc[df['run_total_bases'] == '', 'run_total_bases'] = 'nan'
    
    # convert to float, because int('nan') gives a IntCastingNaNError             
    df['total_spots'] = df['total_spots'].astype('float')
    df['run_total_spots'] = df['run_total_spots'].astype('float')
    df['total_size'] = df['total_size'].astype('float')
    df['run_total_bases'] = df['run_total_bases'].astype('float')
    
    # calculate the read length
    df['read_length'] = ( (df['run_total_bases'] / 
                           df['run_total_spots']).round() )
    
    # fill  missing values in Col1 based on known values in Col2
    def fill_missing_values(df,Col1,Col2):
        uniqueCol2_noCol1 = df[Col2].loc[df[Col1].isnull()].unique()
        for i in range(len(uniqueCol2_noCol1)):
            n = len(df.loc[(df[Col2] == uniqueCol2_noCol1[i]) & 
                           (df[Col1].isnull()),Col2]) 
            indecies = df.loc[(df[Col2] == uniqueCol2_noCol1[i]) & 
                              (df[Col1].isnull()),Col1].index
            if len(df.loc[(df[Col2] == uniqueCol2_noCol1[i]) & 
                          (df[Col1].notnull()),Col1].unique()) > 0:
                df.loc[indecies,Col1] = df.loc[(df[Col2] == uniqueCol2_noCol1[i]) & 
                                               (df[Col1].notnull()),Col1].unique().repeat(n)
        return df
    
    if df.loc[:,'organism_name'].isnull().sum() > 0:
        df = fill_missing_values(df, 'organism_name', 'organism_taxid ')
    
    # Use of the filling_missing_values function can  be added to other
    # columns too - for instance,
    # fill_missing_values(df, 'study_title', 'study_accession')
    
    
    df_selection = df.copy()
    
    # min/max values for selection  sliders
    minSpots, maxSpots = (df.run_total_spots
                            .agg(['min', 'max'])
                            .astype('int'))
    minSize, maxSize = (df.total_size
                            .agg(['min', 'max'])
                            .astype('int'))
    minBases, maxBases = (df.run_total_bases
                            .agg(['min', 'max'])
                            .astype('int'))
    minReadLength, maxReadLength = (df.read_length
                                      .agg(['min', 'max'])
                                      .astype('int')) 
else:   # values for the initial 
    minSpots, maxSpots = [0, 1000000]
    minSize, maxSize = [0, 1000000]
    minBases, maxBases = [0, 1000000]
    minReadLength, maxReadLength = [0, 100]

#==== Filters ===============================================  
st.sidebar.title("Data Selection Filters:")  
studySelect = st.sidebar.multiselect(
    "Filter by 'study accession': ",
     options = df['study_accession'].unique(),
     default = df['study_accession'].unique()
     )
if df["study_accession"].isnull().sum() > 0:
    studyNaN = st.sidebar.checkbox("Remove rows missing 'study_accession' values?")
else:
    studyNaN = False
    
organismSelect = st.sidebar.multiselect(
    "Filter by 'organism_name': ",
    options = df['organism_name'].unique().tolist(),
    default = df['organism_name'].unique().tolist()
    )
if df["organism_name"].isnull().sum() > 0:
    organismNaN = st.sidebar.checkbox("Remove rows missing 'organism_name' values?")
else:
    organismNaN = False
    
libraryStrategySelect = st.sidebar.multiselect(
    "Filter by 'library_strategy': ",
    options = df['library_strategy'].unique(),
    default = df['library_strategy'].unique()
    )
if df["library_strategy"].isnull().sum() > 0:
    libraryStrategyNaN = st.sidebar.checkbox("Remove rows missing 'library_strategy' values?")
else:
    libraryStrategyNaN = False
    
librarySourceSelect = st.sidebar.multiselect(
    "Filter by 'library_source': ",
    options = df['library_source'].unique(),
    default = df['library_source'].unique()
    )
if df["library_source"].isnull().sum() > 0:
    librarySourceNaN = st.sidebar.checkbox("Remove rows missing 'library_source' values?")
else:
    librarySourceNaN = False
    
librarySelectionSelect = st.sidebar.multiselect(
    "Filter by 'library_selection': ",
    options = df['library_selection'].unique(),
    default = df['library_selection'].unique()
    )
if df["library_selection"].isnull().sum() > 0:
    librarySelectionNaN = st.sidebar.checkbox("Remove rows missing 'library_selection' values?")
else:
    librarySelectionNaN = False
    
libraryLayoutSelect = st.sidebar.multiselect(
    "Filter by 'library_layout': ",
    options = df['library_layout'].unique(),
    default = df['library_layout'].unique()
    )
if df["library_layout"].isnull().sum() > 0:
    libraryLayoutNaN = st.sidebar.checkbox("Remove rows missing 'library_layout' values?")
else:
    libraryLayoutNaN = False
    
instrumentSelect = st.sidebar.multiselect(
    "Filter by 'instrument': ",
    options = df['instrument'].unique(),
    default = df['instrument'].unique()
    )
if df["instrument"].isnull().sum() > 0:
    instrumentNaN = st.sidebar.checkbox("Remove rows missing 'instrument' values?")
else:
    instrumentNaN = False
    
spotsSelect = st.sidebar.slider(
    "Filter by 'run_total_spots' range: ",
    min_value = minSpots,
    max_value = maxSpots,
    value= [minSpots, maxSpots],
    step = int((maxSpots - minSpots)/1000000)
    )
if df["run_total_spots"].isnull().sum() > 0:
    spotsNaN = st.sidebar.checkbox("Remove rows missing 'run_total_spots' values?")
else:
    spotsNaN = False
    
basesSelect = st.sidebar.slider(
    "Filter by 'run_total_bases' range: ",
    min_value = minBases,
    max_value = maxBases,
    value= [minBases, maxBases],
    step = int((maxBases - minBases)/1000000)
    )
if df["run_total_bases"].isnull().sum() > 0:
    basesNaN = st.sidebar.checkbox("Remove rows missing 'run_total_bases' values?")
else:
    basesNaN = False
    
readLengthSelect = st.sidebar.slider(
    "Filter by 'read_length' range: ",
    min_value = minReadLength,
    max_value = maxReadLength,
    value= [minReadLength, maxReadLength],
    step = 1
    )
if df["read_length"].isnull().sum() > 0:
    readLengthNaN = st.sidebar.checkbox("Remove rows missing 'read_length' values?")
else:
    readLengthNaN = False
    
sizeSelect = st.sidebar.slider(
    "Filter by 'total_size' range: ",
    min_value = minSize,
    max_value = maxSize,
    value= [minSize, maxSize],
    step = int((maxSize - minSize)/1000000)
    )
if df["total_size"].isnull().sum() > 0:
    sizeNaN = st.sidebar.checkbox("Remove rows missing 'total_size' values?")
else:
    sizeNaN = False

#==== Plots and Statistics ====================================================================
# if len(df) != 0:
#     expandStats = True
# else:
#     expandStats = False
# statsExpander = st.expander("Statistics and Visualiations:", 
#                             expanded = expandStats)
# with statsExpander:
    
# Chart with aggregated data by study or studies
# whichStudy = 


# number of organism names

# plotsExpander = st.expander("Plots and Statistics:", expanded = True)
# with plotsExpander:
#     if len(df) != 0:
#         a = df.groupby('organism_name')['library_source'].nunique()
#         barChart = px.bar(data_frame = a,
#                           x = 'organism_name',
#                           y = 'library_source',
#                           color = 'organism_name'
#                           )
#         st.plotly_chart(barChart)
    

#==== Selected data ===================================================
dfExpander = st.expander("Selected dataframe:", expanded = True)
with dfExpander:
    if len(df) != 0:
        #st.dataframe(df, )
        #st.table(df)
        
        # Remove rows with missing values
        userColumns = {"study_accession": studyNaN, 
                   "organism_name": organismNaN, 
                   "library_strategy": libraryStrategyNaN,
                   "library_source": librarySourceNaN,
                   "library_selection": librarySelectionNaN,
                   "library_layout": libraryLayoutNaN,
                   "instrument": instrumentNaN,
                   "total_spots": spotsNaN,
                   "total_size": sizeNaN,
                   "run_total_bases": basesNaN,
                   "read_length": readLengthNaN
                   }
        userSubset = [key for key in  userColumns if userColumns[key] == True] 
        df_selection = df.dropna(subset = userSubset, how = 'any')
        
        # Filer data by user selection criteria
        selection = ['study_accession in @studySelect', 
           'organism_name in @organismSelect',
           'library_strategy in @libraryStrategySelect',
           'library_source in @librarySourceSelect',
           'library_selection in @librarySelectionSelect', 
           'library_layout in @libraryLayoutSelect',
           'instrument in @instrumentSelect',
           '@spotsSelect[0] <= total_spots <= @spotsSelect[1]', 
           '@sizeSelect[0] <= total_size <= @sizeSelect[1]',
           '@readLengthSelect[0] <= read_length <= @readLengthSelect[1]']
        
        # df_selection = df.query(' & '.join(selection))
        df_selection = df_selection.query(' & '.join(selection))
        with st.spinner("Uploading data"):
            # AgGrid(df_selection)
            st.dataframe(df_selection,)