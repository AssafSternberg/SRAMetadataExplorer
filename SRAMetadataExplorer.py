import streamlit as st  # pip/conda install streamlit
import pandas as pd  # pip/conda install pandas
import plotly.express as px  # pip/conda install plotly_express
from pysradb import SRAweb  # conda install -c bioconda pysradb
import re

st.set_page_config(
    page_title = "SRA Metadata Explorer",
    page_icon = "🧬", # the emoji code ":dna:" is not recognized
    layout = "wide"
    )

#==== Title =====================================================
st.title("🧬 SRA Metadata Explorer")  #":dna:"


# Column names to be selected or used for initial empty dataframes
dfColumns = ['study_accession', 'study_title', 'experiment_accession', 
           'experiment_title', 'organism_taxid ', 'organism_name', 
           'library_strategy', 'library_source', 'library_selection', 
           'library_layout', 'sample_accession', 'sample_title', 
           'instrument', 'total_spots', 'total_size', 'run_accession', 
           'run_total_bases', 'run_total_spots', 'read_length']
statColumns = (['number_of_experiments', 'number_of_runs', 
                'number_of_samples', 'organism, names',
                'library_strategies', 'library_sources',
                'instruments'])
df_empty = pd.DataFrame(data = None, columns = dfColumns)
df = df_empty.copy()
df_selection = df_empty.copy()
df_stats = pd.DataFrame(data = None, columns = statColumns)

tab1, tab2 = st.tabs([":bar_chart: Data", ":information_source: About"])

#==== Load/Search ===============================================
loadSearch = tab1.text_input('''Enter study/experiment/sample/run accession 
                             codes, a text to  search for or a CSV file name 
                             to  load: ''', 
                             placeholder=('SRP017942|SRP015946|SRP028720, ' + 
                                          '"Sars-Cov-2" or filename.csv')) 
tab1.markdown('''<p style=\"font-size:10px;\">*Codes can be SRP/ERP/GMP/DRP 
            SRS/ERS/DRS/GMS SRX/ERX/GMX/DRX or SRR/ERR/GMR/DRR. For multiple 
            codes, separate codes by '|' (pipe symbol). </br> 
            **Enter search  text between parentheses. Search by text might 
            take a while.</p>''', unsafe_allow_html = True)

# Check if user entered a valid code, search text or filename
if loadSearch != '':
    db = SRAweb()
    if bool(re.fullmatch('".+"', loadSearch)):  # search text between parentheses
        df = db.search_sra(search_str = loadSearch)
    elif bool(re.fullmatch("^\D\D\D\d+[|\D\D\D\d+|]*[\D\D\D\d+$]*", loadSearch)): # valid code or codes seperated by '|'
        df = db.sra_metadata(loadSearch)
    elif bool(re.fullmatch('.+\.csv', loadSearch)):  # CSV file name  
        df = pd.read_csv(loadSearch)
    else:
        tab1.markdown(''''<p style="color:Red; font-size:16px;">You did not 
                      enter a valid input. Please try again.</p>''', 
                      unsafe_allow_html = True)

# in case of a null result
if df is None:
    df = df_empty.copy()
    

if len(df) != 0:
    df = df.loc[:,dfColumns[:-1]]  # remove 'read_length' as it 
                                   # hasn't been added yet 
    
    # fill in a 'nan' value for missing data so columns can be
    # converted to a numerical type
    df.loc[df['total_spots'] == '', 'total_spots'] = 'nan'
    df.loc[df['run_total_spots'] == '', 'run_total_spots'] = 'nan'
    df.loc[df['total_size'] == '', 'total_size'] = 'nan'
    df.loc[df['run_total_bases'] == '', 'run_total_bases'] = 'nan'
    
    # convert to float, because int('nan') gives a IntCastingNaNError             
    df['total_spots'] = df['total_spots'].astype('float')
    df['run_total_spots'] = df['run_total_spots'].astype('float')
    df['total_size'] = df['total_size'].astype('float')
    df['run_total_bases'] = df['run_total_bases'].astype('float')
    
    # calculate the read lengths
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
                                               (df[Col1].notnull()),Col1].unique().repeat(n).copy()
        return df
    
    if df.loc[:,'organism_name'].isnull().sum() > 0:
        df = fill_missing_values(df, 'organism_name', 'organism_taxid ')
    
    # The filling_missing_values function can be applied to other
    # columns too. For instance,
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
else:   # values for the initial or empty df
    minSpots, maxSpots = [0, 1000000]
    minSize, maxSize = [0, 1000000]
    minBases, maxBases = [0, 1000000]
    minReadLength, maxReadLength = [0, 100]

#==== Selection filters ===============================================  
st.sidebar.title("Data Selection Filters:")  

def addSidebarSelection(column_name):
    nameSelect = st.sidebar.multiselect(
        "Filter by '{}': ".format(column_name),
         options = df[column_name].unique(),
         default = df[column_name].unique()
         )
    if df[column_name].isnull().sum() > 0:
        nameNaN = st.sidebar.checkbox("Remove rows missing '{}' values?".format(column_name))
    else:
        nameNaN = False
    return (nameSelect, nameNaN)

def addSidebar2SideSlider(column_name, col_min, col_max, step):
    if col_min != col_max:
        nameSelect = st.sidebar.slider(
            "Filter by '{}' range: ".format(column_name),
            min_value = col_min,
            max_value = col_max,
            value= [col_min, col_max],
            step = int((col_max - col_min)/step)
            )
        if df[column_name].isnull().sum() > 0:
            nameNaN = st.sidebar.checkbox("Remove rows missing '{}' values?".format(column_name))
        else:
            nameNaN = False
    else:
        nameSelect = (col_min, col_max)
        nameNaN = False
    return (nameSelect, nameNaN)

studySelect, studyNaN = addSidebarSelection('study_accession')
experimentSelect, experimentNaN = addSidebarSelection('experiment_accession')  
sampleSelect, sampleNaN = addSidebarSelection('sample_accession')
organismSelect, organismNaN = addSidebarSelection('organism_name')
libraryStrategySelect, libraryStrategyNaN = addSidebarSelection('library_strategy')
librarySourceSelect, librarySourceNaN = addSidebarSelection('library_source')
librarySelectionSelect, librarySelectionNaN = addSidebarSelection('library_selection')
libraryLayoutSelect, libraryLayoutNaN = addSidebarSelection('library_layout')
instrumentSelect, instrumentNaN = addSidebarSelection('instrument')
  
spotsSelect, spotsNaN = addSidebar2SideSlider('run_total_spots', 
                                              minSpots, maxSpots, 1000000)
basesSelect, basesNaN = addSidebar2SideSlider('run_total_bases', 
                                              minBases, maxBases, 1000000) 
readLengthSelect, readLengthNaN = addSidebar2SideSlider('read_length', 
                                                   minReadLength, 
                                                   maxReadLength, 1)  
sizeSelect, sizeNaN = addSidebar2SideSlider('total_size', 
                                              minSize, maxSize, 1000000)  
    
#==== Applying the filter ============================================
if len(df) != 0:
    # Remove rows with missing values
    userColumns = {"study_accession": studyNaN,
                   "experiment_accession": experimentNaN,
                   "sample_accession": sampleNaN,
                   "organism_name": organismNaN, 
                   "library_strategy": libraryStrategyNaN,
                   "library_source": librarySourceNaN,
                   "library_selection": librarySelectionNaN,
                   "library_layout": libraryLayoutNaN,
                   "instrument": instrumentNaN,
                   "run_total_spots": spotsNaN,
                   "total_size": sizeNaN,
                   "run_total_bases": basesNaN,
                   "read_length": readLengthNaN
                   }
    
    userSubset = [key for key in  userColumns if userColumns[key] == True] 
    df_selection = df.dropna(subset = userSubset, how = 'any')
    
    # Filer data by user selection criteria
    selection = ['study_accession in @studySelect',
                 'experiment_accession in @experimentSelect',
                 'sample_accession in @sampleSelect',
                 'organism_name in @organismSelect',
                 'library_strategy in @libraryStrategySelect',
                 'library_source in @librarySourceSelect',
                 'library_selection in @librarySelectionSelect', 
                 'library_layout in @libraryLayoutSelect',
                 'instrument in @instrumentSelect',
                 '@spotsSelect[0] <= run_total_spots <= @spotsSelect[1]', 
                 '@sizeSelect[0] <= total_size <= @sizeSelect[1]',
                 '@readLengthSelect[0] <= read_length <= @readLengthSelect[1]']
    
    df_selection = df_selection.query(' & '.join(selection))
    
        
#==== Plots and Statistics ========================================
if len(df) != 0:
    expandStats = True
else:
    expandStats = False
statsExpander = tab1.expander("Statistics and Visualiations:", 
                            expanded = expandStats)

with tab1:
    with statsExpander:
        if len(df_selection) >= 0:
            studies = df.loc[df.study_accession.notnull(),'study_accession'].unique()
            if len(studies) < 5:
                n = len(studies)
            else:
                n=5
            byStudy = st.multiselect("Select study, or studies, to view statistics: ",
                                  options = studies,
                                  default = studies[0:n])
            statsByStudy = (df.query("study_accession in @byStudy")
                                .groupby('study_accession')
                                .agg({'experiment_accession': 'count',
                                      'run_accession': 'count',
                                      'sample_accession': 'count',
                                      'organism_name': pd.Series.unique,
                                      'library_strategy': pd.Series.unique,
                                      'library_source': pd.Series.unique,
                                      'instrument': pd.Series.unique}))
            statsByStudy.columns = statColumns  # defined after title call
            st.dataframe(statsByStudy)
        else:
            statsByStudy = pd.DataFrame(data = None, columns = statColumns)
            st.dataframe(statsByStudy)
                                     
    
        def createByStudyBoxPlot(column_name):
            chart = px.box(data_frame = df.query("study_accession in @byStudy"),
                           x = 'study_accession',
                           y = column_name,
                           points = "all",
                           color = 'study_accession',
                           hover_data= ["experiment_accession", "sample_accession"])
            return st.plotly_chart(chart)
    
        col1, col2 = st.columns(2)
        with col1:
            if len(df) != 0:
                spotsChart = createByStudyBoxPlot('run_total_spots')
                
        with col2:
            if len(df) != 0:
                basesChart = createByStudyBoxPlot('run_total_bases')

        col1, col2 = st.columns(2)
        with col1:
            if len(df) != 0:
                readLengthChart = createByStudyBoxPlot('read_length')
            
        with col2:
            if (len(df) != 0):
                sizeChart = createByStudyBoxPlot('total_size')

#==== Selected dataframe =================================================
if len(df) != 0:
    expandDF = True
else:
    expandDF = False
dfExpander = tab1.expander("Selected dataframe:", expanded = expandDF)
with dfExpander:
    with st.spinner("Uploading data"):
        st.dataframe(df_selection)

#==== Selected studies, experiments and samples ===========================
if len(df) != 0:
    expandCodes = True
else:
    expandCodes = False
codesExpander = tab1.expander("Selected codes:", expanded = expandCodes)
with codesExpander:
    st.markdown("<b>Selected studies: </b>" + 
                ', '.join(df_selection.study_accession.unique()), 
                unsafe_allow_html = True)
    st.markdown("<b>Selected experiments: </b>" + 
                ', '.join(df_selection.experiment_accession.unique()), 
                unsafe_allow_html = True)

    st.markdown("<b>Selected samples: </b>" + 
                ', '.join(df_selection.sample_accession.unique()), 
                unsafe_allow_html = True)

#====== Tab 2 - About ==================================================
tab2.markdown('''<p>The <b>SRA Metadata Explorer</b> application is written 
              in Python (3.10.9). It uses the 
              <a href="https://github.com/saketkc/pysradb" target="_blank">
              <TT>pysradb</TT></a> 
              package, written by Saket Choudhary, to download metadata from 
              the Sequence Read Archive 
              <a href="https://www.ncbi.nlm.nih.gov/sra" target="_blank">
              (SRA)</a>, maintained by the National Center for Biotechnology 
              Information (NCBI).<p> 
              <p>The application accepts one 
              of three search or load inputs,
              <ol>
              <li> A study, experiment or sample code, or codes. For multiple 
              codes enter them separated by a pipe symbol '|', e.g., 
              SRP017942|SRP015946|SRP028720. </li>
              <li> A search text enclosed within parentheses, e.g., "ribosome 
              profiling.</li>
              <li> A CSV file name, or path. Currently, the file has to be on 
              the same computer/server that the app is running on.</li>
              </ol>
              <b>Notice:</b> text searches might take a long time to run.</p>
              <p>Once the metadata is retrieved, the filters in the side bar 
              get updated based and the user can filter the data based on 
              them. In addition, a table with statistics for each study, and 
              box plots with the spots, bases, size and read lengths, 
              grouped by the studies. The table and charts are initialized 
              with up to the 5 first studies in the data.</p>''', 
              unsafe_allow_html = True)
tab2.markdown('''<p>At times, the <TT>pysradb</TT> API times out and fails to 
            retrieve the requested metadata. If this is the case, try again 
            later. In the mean time, you can use one of the CSV files 
            <TT>metadata[1/2].csv</TT> to try out the app.</p>''', unsafe_allow_html = True)
st.markdown('')
st.markdown('')
st.markdown('''<p style="font-size:11px;">Developed by Assaf Sternberg, 
            February 2023.</p>''', unsafe_allow_html = True)