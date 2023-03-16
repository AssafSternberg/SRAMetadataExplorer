# :dna: SRA Metadata Explorer
The `SRA Metadata Explorer` application is written in Python (3.10.9). It uses the [`pysradb`](https://github.com/saketkc/pysradb) package, written by Saket Choudhary, to download metadata from the Sequence Read Archive ([SRA](https://www.ncbi.nlm.nih.gov/sra)), maintained by the National Center for Biotechnology Information (NCBI).

The application accepts one of three search or load inputs,

   1. A study, experiment or sample code, or codes. For multiple codes enter them separated by a pipe symbol '|', e.g., SRP017942|SRP015946|SRP028720.  
   2. A search text enclosed within parentheses, e.g., "ribosome profiling.  
   3. A CSV file name, or path. Currently, the file has to be on the same computer/server that the app is running on.  

**Notice:** text searches might take a long time to run.

Once the metadata is retrieved, the filters in the side bar get updated based and the user can filter the data based on them. In addition, a table with statistics for each study, and interactive box plots (using the [`plotly_express`](https://plotly.com/python/plotly-express/) package) with the spots, bases, size and read lengths, grouped by the studies. The table and charts are initialized with up to the 5 first studies in the data.

At times, the pysradb API times out and fails to retrieve the requested metadata. If this is the case, try again later. In the mean time, you can use one of the CSV files `metadata[1/2].csv` to try out the app.

### Installation
To install `streamlit` using pip:  
`pip install streamlit`  
or alternatively,  
`conda install streamlit`  

To install `pysradb` using pip:
`pip install pysradb`  
or alternatively,  
`conda install - c bioconda pysradb`

To install `plotly_express` using pip:
`pip install plotly_express`  
or alternatively,  
`conda install plotly_express`

### Running the App and Known Issues
To run the app:  
`streamlit run SRAMetadataExplorer.py`  
A local server will be started, and the app will be launched in a new browser tab.

If running `streamlit run filename.py` gives a `ModuleNotFoundError: No module named 'streamlit.cli'`, go to anaconda3/envs/[env name]/bin/ and edit the `streamlit` file from,  
   `from streamlit.cli import main`  
to,  
   `from streamlit.web.cli import main`

### Dependencies
streamlit  
pysradb  
pandas  
plotly_express  
re  
*to see all dependencies view `environment.yml`

### Future Development Ideas 

- Improve and expand missing data imputation.  

- Add an option to write out the selected studies, experiments and/or samples to a file that can be run to download the related data.  

- Add an 'Analysis' tab to the app, in which the sequencing data can  be analyzed.
