import serial
import time
import csv
import boto3
import os
import codecs
from datetime import datetime
from botocore.exceptions import NoCredentialsError, ClientError




# === Configuration ===
PORT = 'COM7'  # Replace with your actual COM port
BAUDRATE = 115200
S3_BUCKET = 'capwater'
AWS_REGION = 'us-west-2'
CSV_DIR = 'C:/Users/vakla/Documents/Jun9Office/cap_logs'
CREDENTIAL_CSV = 'C:/Users/vakla/Documents/Jun9Office/vakmaster_accessKeys.csv'




# === Ensure output directory exists ===
os.makedirs(CSV_DIR, exist_ok=True)








# === Read AWS credentials from CSV ===
def read_credentials(file_path):
    with codecs.open(file_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        credentials = next(reader)
        return credentials["AccessKeyId"], credentials["SecretAccessKey"]








# === Upload file to S3 using session with explicit credentials ===
def upload_to_aws(local_file, bucket_name, s3_file, access_key, secret_key):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=AWS_REGION,
    )
    s3 = session.client("s3")
    try:
        s3.upload_file(local_file, bucket_name, s3_file)
        print(f"[S3] Upload successful: {s3_file}")
        return True
    except FileNotFoundError:
        print("[S3 ERROR] File not found")
    except NoCredentialsError:
        print("[S3 ERROR] Credentials not available")
    except ClientError as e:
        print(f"[S3 ERROR] Client error: {e}")
    except Exception as e:
        print(f"[S3 ERROR] Unexpected error: {e}")
    return False








# === Generate filename like cap_sensor_20250710_1500.csv ===
def get_csv_filename():
    timestamp = datetime.now().strftime('%Y%m%d_%H00')
    return os.path.join(CSV_DIR, f"cap_sensor_{timestamp}.csv")








# === Prepare initial CSV file ===
csv_file = get_csv_filename()
if not os.path.exists(csv_file):
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'CH0_pF', 'CH1_pF', 'Delta_pF'])




last_upload_hour = datetime.now().hour
last_write_time = time.time()
latest_data = None




# === Load AWS credentials once ===
access_key, secret_key = read_credentials(CREDENTIAL_CSV)




# === Continuous read and logging loop ===
while True:
    try:
        with serial.Serial(PORT, BAUDRATE, timeout=5) as ser:
            print(f"[{datetime.now()}] Connected to {PORT}")
            time.sleep(2)  # Wait for Arduino reboot




            while True:
                try:
                    line = ser.readline().decode(errors='ignore').strip()
                    if not line:
                        continue




                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")




                    # Parse capacitance values
                    if line.startswith("CH0:"):
                        ch_values = line.replace("CH0: ", "").replace(" pF", "").replace("CH1: ", "").split(",")
                    elif line.startswith("ΔC:"):
                        delta = line.replace("ΔC: ", "").strip()
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        latest_data = (timestamp, ch_values[0], ch_values[1], delta)




                    # Write data every 60 seconds
                    current_time = time.time()
                    if latest_data and (current_time - last_write_time) >= 60:
                        with open(csv_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(latest_data)
                            print(f"[LOGGED] {latest_data}")
                        last_write_time = current_time




                        # Upload file if a new hour starts
                        current_hour = datetime.now().hour
                        if current_hour != last_upload_hour:
                            s3_key = os.path.basename(csv_file)
                            print(f"[{datetime.now()}] Uploading {s3_key} to S3...")
                            upload_to_aws(csv_file, S3_BUCKET, s3_key, access_key, secret_key)




                            # Create new file for next hour
                            csv_file = get_csv_filename()
                            with open(csv_file, 'a', newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow(['Timestamp', 'CH0_pF', 'CH1_pF', 'Delta_pF'])
                            last_upload_hour = current_hour




                except Exception as e:
                    print(f"[READ ERROR] {e}")
                    break




    except serial.SerialException as e:
        print(f"[ERROR] Could not open {PORT}: {e}")
        time.sleep(5)















