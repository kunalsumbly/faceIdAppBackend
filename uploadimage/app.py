import boto3
import os
import logging
import json

BUCKET = os.environ['BUCKETNAME']
COLLECTION_ID = os.environ['REKOGNITIONCOLLECTION']
LOG_LEVEL = logging.INFO

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# image name :- mugshot_kusu.png
def lambda_handler(event, context):
    try:
        logger.info("Parsing request data.")
        data = json.loads(event['body'])
        image = data['image']
    
        logger.info("Indexing faces.")
        response = rekognition.index_faces(
            Image={
                "S3Object": {
                    "Bucket": BUCKET,
                    "Name": image
                }
            },
            CollectionId=COLLECTION_ID
        )
    
        logger.info("Getting results.")
        if response['ResponseMetadata']['HTTPStatusCode'] != 200 or len(response['FaceRecords']) == 0:
            raise Exception("Fail to register a face to Rekognition.")

        faceId = response['FaceRecords'][0]['Face']['FaceId']
        logger.info("Recorded faceId: {}".format(faceId))

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Success. Face recorded"
            }),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Error: {}".format(e),
            }),
        }
