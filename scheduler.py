# import necessary libraries
import schedule
import time
import requests

# define function to make HTTP request to your FastAPI route
def call_api():
    url = "http://localhost:80/fetch-all-posts"
    response = requests.get(url)
    with open('sch.log', 'a') as f:
        f.write("abbas: " + str(response) + "\n")

    print("HTTP response: ")


# schedule the job to run every 15 minutes
schedule.every(15).minutes.do(call_api)

# continuously run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
