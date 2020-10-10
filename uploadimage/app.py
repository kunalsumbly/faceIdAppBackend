import boto3
import os
import logging
import json

BUCKET = os.environ['BUCKETNAME']
COLLECTION_ID = os.environ['REKOGNITIONCOLLECTION']
LOG_LEVEL = logging.INFO

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
region = os.environ['AWS_REGION'] 
counter_table = os.environ['PersonDataCounter']
missing_person_table = os.environ['PersonData']
dynamodb = boto3.client('dynamodb',region)

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# image name :- mugshot_kusu.png
def lambda_handler(event, context):
    try:
        logger.info("Parsing request data.")
        data = json.loads(event['body'])
        image = data['image']
        missing_person_data = data['missingpersondata']
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
        
        # implement auto increment here
        person_record_pk_id=incrementPersonRecordCounter(); 

        # save the attributes in the person missing data
        saveMissingPersonData(person_record_pk_id, missing_person_data,faceId)

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
        logger.error(e)
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

# This method saves the missing person data in Dynamodb
def saveMissingPersonData(person_record_pk_id, missing_person_data, faceId):
    response = dynamodb.put_item (
                    TableName=missing_person_table,
                     Item = {
                                "person_record_id":{"N":person_record_pk_id}, # key id person record pk id
                                "firstname": {"S":missing_person_data['firstname']},
                                "lastname": {"S":missing_person_data['lastname']},
                                "dateofbirth": {"S":missing_person_data['dateofbirth']},
                                "missingfromlocation": {"S":missing_person_data['missingfromlocation']},
                                "age": {"S":str(missing_person_data['age'])},
                                "familycontactphone": {"S":str(missing_person_data['familycontactphone'])},
                                "reportingcentrecontact": {"S":missing_person_data['reportingcentrecontact']},
                                "faceid":{"S":faceId}
                            }
                )

# This method will increment the person record counter
def incrementPersonRecordCounter() :
    logger.info("incrementPersonRecordCounter started")
    response= dynamodb.update_item (
                TableName=counter_table,
                Key={
                        "counterName":{"S":"personRecordCounter"}
                    },
                UpdateExpression="SET #var = #var + :incr",
                ExpressionAttributeNames={ "#var": "currentValue" },
                ExpressionAttributeValues={
                     ":incr": {"N":"1"}
                },
                ReturnValues='UPDATED_NEW'
            )
    logger.info("incrementPersonRecordCounter ended")        
    return response['Attributes']['currentValue']['N']

