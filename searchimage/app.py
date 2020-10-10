import boto3
import os
import logging
import json


BUCKET = os.environ['BUCKETNAME']
COLLECTION_ID = os.environ['REKOGNITIONCOLLECTION']
FACE_MATCH_THRESHOLD = int(os.environ['REKOGNITIONFACEMATCHTHRESHOLD'])
LOG_LEVEL = logging.INFO

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)


def lambda_handler(event, context):
    try:
        logger.info("Parsing request data.")
        data = json.loads(event['body'])
        image = data['image']
        
        
        logger.info("Searching faces.")
        response = rekognition.search_faces_by_image(
            Image={
                "S3Object": {
                    "Bucket": BUCKET,
                    "Name": image
                }
            },
            CollectionId=COLLECTION_ID,
            FaceMatchThreshold=FACE_MATCH_THRESHOLD,
            MaxFaces=1
        )
    
        logger.info("Getting results.")
        if response['ResponseMetadata']['HTTPStatusCode'] != 200 or len(response['FaceMatches']) == 0:
            raise Exception("Fail to find similar face")
    
        faceFound = response['FaceMatches'][0]
        faceId = faceFound['Face']['FaceId']
        confidence = faceFound['Similarity']
        logger.info("Found faceId: {}. Confidence level: {}".format(faceId, confidence))

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Succeed to find similar face.",
                "faceId": faceId,
                "confidence": confidence
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