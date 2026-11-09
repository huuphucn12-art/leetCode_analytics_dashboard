from src.utility.config import *

from src.scripts.setup.init import *
from src.scripts.setup.bronze import *
from src.scripts.setup.silver import *
from src.scripts.setup.gold import *

from src.scripts.pipeline.raw_to_bronze import *
from src.scripts.pipeline.bronze_to_silver import *
from src.scripts.pipeline.silver_to_gold import *

# Step 1
print("---------------------------------------------------------")
print("====== STEP 1: Verify Authentication to Databricks ======")
print("====== STEP 1 completed successfully ======")
print("---------------------------------------------------------\n")

# Step 2
print("---------------------------------------------------------")
print("====== STEP 2: Setup Objects ======\n")
print(" ===== Init Unity Catalog Objects =====")
print("====== STEP 2 completed successfully ======")
print("---------------------------------------------------------\n")


# Step 3
print("---------------------------------------------------------")
print("====== STEP 3: Raw to Bronze ======\n")
print(" ===== Load Question Information Data =====")
print(" ===== Load Question Topic Data =====")
print(" ===== Load Contest Data =====")
print(" ===== Load Daily Question Data =====")
print(" ===== Load Submission Data =====")
print("===== STEP 3 completed successfully =====")
print("---------------------------------------------------------\n")

# Step 4
print("---------------------------------------------------------")
print("====== STEP 4: Bronze to Silver ======\n")
print(" ===== Processing Question Information Data ===== ")
print(" ===== Processing Question Topic Data ===== ")
print(" ===== Processing Contest Information Data ===== ")
print(" ===== Processing Question Daily Data ===== ")
print(" ===== Processing Submission Information Data ===== ")
print("====== STEP 4 completed successfully =====")
print("---------------------------------------------------------\n")

# Step 5
print("---------------------------------------------------------")
print("====== STEP 5: Silver to Gold ======\n")
print(" ===== Processing Question Information Data ===== ")
print(" ===== Processing Question Topic Data ===== ")
print(" ===== Processing Contest Information Data ===== ")
print(" ===== Processing Question Daily Data ===== ")
print(" ===== Processing Submission Information Data ===== ")
print(" ===== Process Mart Submission Difficulty =====")
print(" ===== Process Mart Submission Topic =====")
print(" ===== Process Mart Submission Daily =====")
print(" ===== Process Mart Submission Contest ===== ")
print("---------------------------------------------------------")