# Databricks notebook source
# MAGIC %run ./setup

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate a JSON dataset for the Autoloader to pick up

# COMMAND ----------

# DBTITLE 1,Define Record Count, Temporary Location, Autoloader-Monitored Location and Sleep Interval Here
recordCount=5
nIDs = 10
stem_file_path = spark_storage_path
temp_path = "{}/temp".format(stem_file_path)
destination_path = "{}/autoloader".format(stem_file_path)
sleepIntervalSeconds = 2

# COMMAND ----------

# DBTITLE 1,Reset Environment & Setup
dbutils.fs.rm(temp_path, recurse=True)
dbutils.fs.rm(destination_path, recurse=True)
dbutils.fs.mkdirs(destination_path)

# COMMAND ----------

# DBTITLE 1,Functions to generate a JSON dataset for the Autoloader to pick up
import random
import string
from datetime import datetime
import time
import os

# Method to return a random User ID between 1 and 5 (set low for testing some stateful streaming aggregations, higher for more variability)
def returnCustomerID(nIDs):
  return random.randint(1, nIDs)

# Return a random float value for different purposes, rounded to 2 places
def returnValue():
  return round(random.uniform(2.11, 399.99), 2)

def returnTransactionTimestamp():
  currentDateTime = datetime.now()
  return currentDateTime.strftime("%Y-%m-%d %H:%M:%S.%f")

# Generate a record
def generateRecord(nIDs):
  return (returnCustomerID(nIDs), returnValue(), returnTransactionTimestamp())
  
# Generate a list of records
def generateRecordSet(recordCount, nIDs):
  recordSet = []
  for x in range(recordCount):
    recordSet.append(generateRecord(nIDs))
  return recordSet

# Generate a set of data, convert it to a Dataframe, write it out as one json file in a temp location, 
# move the json file to the desired location that the autoloader will be watching and then delete the temp location
def writeJsonFile(recordCount, nIDs, temp_path, destination_path):
  recordColumns = ["CustomerID", "Amount", "TransactionTimestamp"]
  recordSet = generateRecordSet(recordCount,nIDs)
  recordDf = spark.createDataFrame(data=recordSet, schema=recordColumns)
  
  # Write out the json file with Spark in a temp location - this will create a directory with the file we want
  recordDf.coalesce(1).write.format("json").save(temp_path)
  
  # Grab the file from the temp location, write it to the location we want and then delete the temp directory
  tempJson = os.path.join(temp_path, dbutils.fs.ls(temp_path)[3][1])
  dbutils.fs.cp(tempJson, destination_path)
  dbutils.fs.rm(temp_path, True)

# COMMAND ----------

# DBTITLE 1,Loop for Generating Data
t=1
while(t<50):
  writeJsonFile(recordCount, nIDs, temp_path, destination_path)
  t = t+1
  time.sleep(sleepIntervalSeconds)

# COMMAND ----------

# DBTITLE 1,Count of Transactions per User
df = spark.read.format("json").load(destination_path)
usercounts = df.groupBy("CustomerID").count()
display(usercounts.orderBy("CustomerID"))


# COMMAND ----------

# DBTITLE 1,Display the Data Generated
display(df)

# COMMAND ----------


