import logging
import time
from app.services.kafka_service import KafkaService
from app.services.log_service import MongoHandler , FileHandler

logging.basicConfig(level=logging.INFO)
mongo_handler = MongoHandler()
file_handler = FileHandler('logs')

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
mongo_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(mongo_handler)
logging.getLogger().addHandler(file_handler)

kafka_service = KafkaService()

while True:
    try:
        consumer = kafka_service.kafka_consumer('test_group')
        break
    except:
        logging.error("Kafka consumer failed to connect. Retrying...")
        # Wait for 5 seconds before retrying
        time.sleep(5)
# Continuously listen for messages
logging.info("Starting consumer...")
try:
    for message in consumer:
        logging.info(f"Received message: {message.value.decode('utf-8')}")
except KeyboardInterrupt:
    logging.info("Consumer interrupted. Closing...")
finally:
    consumer.close()