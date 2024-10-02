import json
import os
import boto3
import logging

# Configurar el logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Crear un cliente de AWS SQS
sqs = boto3.client('sqs')

QUEUE_URL = os.environ.get('QUEUE_URL')

def handler(event, context):
    for record in event['Records']:
        try:
            # Extraer el mensaje
            mensaje = record['body']
            print(f"Procesando mensaje: {mensaje}")
            
            # Aquí puedes agregar la lógica para procesar el mensaje
            # Por ejemplo, parsear JSON, interactuar con otros servicios, etc.
            
            # Simular procesamiento exitoso
            # Si ocurre un error, lanzar una excepción para que el mensaje sea reenviado a la DLQ
            # raise Exception("Simulación de error de procesamiento")
            
        except Exception as e:
            print(f"Error procesando el mensaje: {e}")
            # Opcional: Implementar lógica adicional de manejo de errores
            raise e  # Re-lanzar la excepción para que SQS lo maneje (reenviar a DLQ)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Mensajes procesados correctamente')
    }
