  --Version 1.3--
  Step 1 new .py file "V-1.2.py" in a new directory called versions.
  Step 2 create new table in database called cri_version value version.
  Step 3 create handler on Criman.py needs to have a method call to find files in version directory.  Then read from the new version table to compare files.  If all files match then do nothing.  If a version files I.E. "V-1.x.py" then run that new file. 
  Step 4 create new version file "V-1.3.py" update values in database to allow NULL if it is called description or asset tag.

--Version1.4--
  Step 1 new versions file "V-1.4.py" 
  Step 2 SQLite database script to remove mfr_desc and md_description from CRIMan.db
  Step 4 Add field service srv_owner TEXT allow NULL
  Step 5 remove from in AddTool.html description for new manufacture and new model. Then Rename Gauge Number to Gauge Serial Number. Then add Owner to Unit & Service after Calibrated By.
  Step 6 remove description from Manufacturers.html and Models.html
  Step 7 Add Owner to Service.html include to edit and add modal
  Step 8 remove mfr_desc and md_description add srv_owner in import_bp.py and export.py
  
--Version1.5--
  Step 1 Create new datanormalization.html page and blueprint page datanormalization.py
  Step 2 Read CRIMan.db manufactuers, models, and service tables
  Step 3 Create process run by button on datanormalization.html to run a method "normalize" in datanormalization.py that will remove duplicate manufactuers picking just one and remap new mfr_id to the md_mfr_id. 
  Step 4 Add to the DataNormalization  a normalization for Models that normalizes the data no just based off of the 4 fields md_name, md_size, md_endsize, and md_mfr_id.  Only allow this to be run if there are no duplicate manufacturers.

  --Version1.6--
   Step 1 Create a search feature to search the data tables loaded on screen. 
   Step 2 apply search feature to index.html, Manufacuteres.html, Models.html, and Service.html