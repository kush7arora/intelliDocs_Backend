from datetime import datetime
import pytz

print("System time:", datetime.now())
print("UTC time:", datetime.utcnow())

ist = pytz.timezone('Asia/Kolkata')
print("IST time:", datetime.now(ist))
