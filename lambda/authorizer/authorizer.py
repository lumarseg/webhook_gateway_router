import json
import os
import boto3
import logging

# Configurar el logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Crear un cliente de Secrets Manager
secrets_client = boto3.client('secretsmanager')

# @logger.inject_lambda_context
def handler(event, context):
    try:

        ## Paso 1: Obtener el token de autorización de los encabezados
#         auth_header = event['headers'].get('Authorization')
        headers = event.get('headers') or {}
        auth_header = headers.get('Authorization')

        if not auth_header:
            logger.error("Authorization header missing")
            raise Exception("Unauthorized")

        # Extraer el token eliminando el prefijo "Bearer "
#         token = auth_header.replace("Bearer ", "")
        token = auth_header.replace("Bearer ", "").strip()
        logger.info(f"Received token: {token}")

        ## Paso 2: Obtener el ARN del secreto desde las variables de entorno
        secret_arn = os.environ.get('SECRET_ARN')
        if not secret_arn:
            logger.error("SECRET_ARN environment variable missing")
            raise Exception("Internal Server Error")
        logger.info(f"Secret ARN: {secret_arn}")

#         secret_arn = os.environ['SECRET_ARN']

        ## Paso 3: Obtener el secreto desde Secrets Manager
        secret = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_dict = json.loads(secret['SecretString'])
        verify_token = secret_dict.get('VERIFY_TOKEN')

        if not verify_token:
            logger.error("VERIFY_TOKEN not found in secret")
            raise Exception("Internal Server Error")
        logger.info(f"Verify token: {verify_token}")

#         secret = secrets_client.get_secret_value(SecretId=secret_arn)
#         secret_dict = json.loads(secret['SecretString'])
#         verify_token = secret_dict.get('VERIFY_TOKEN')


        ## Paso 4. Comparar el secreto con el token recibido

#         if token == verify_token:
#             # Permitir el acceso
#             return {
#                 "isAuthorized": True,
#                 "context": {
#                     "user": "authorized_user"
#                 }
#             }
#         else:
#             logger.error("Invalid token")
#             raise Exception("Unauthorized")
        
        if token == verify_token:
            # Permitir el acceso
            logger.info("Authorization successful")
            return {
                "isAuthorized": True,
                "context": {
                    "user": "authorized_user"
                }
            }
        else:
            logger.error("Invalid token")
            raise Exception("Unauthorized")


    except Exception as e:
#         logger.error(f"Authorization failed: {str(e)}")
#         return {
#             "isAuthorized": False,
#             "context": {}
#         }

        error_message = str(e)
        if error_message == "Unauthorized":
            logger.warning("Unauthorized access attempt")
            return {
                "isAuthorized": False,
                "context": {}
            }
        else:
            # Para errores internos, es mejor denegar el acceso sin exponer detalles
            logger.error(f"Authorization failed: {error_message}")
            return {
                "isAuthorized": False,
                "context": {}
            }
