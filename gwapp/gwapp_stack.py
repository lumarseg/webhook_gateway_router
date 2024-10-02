from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Tags,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_lambda_event_sources as _lambda_event_sources,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class GwappStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # 01. TAG Definition to all resources
        TAG = ["accounting_tag", "webhookgateway"]
        Tags.of(self).add(TAG[0], TAG[1]) 


        # 02. Create the Dead Letter Queue
        dlq_queue = sqs.Queue(
            self, 
            "DeadLetterQueue",
            queue_name="WebhookGateway-DLQ",
            retention_period=Duration.days(14)
        )


        # 03. Create the Main Message Queue
        main_queue = sqs.Queue(
            self, 
            "Queue",
            queue_name="WebhookGateway-Queue",
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=dlq_queue
            ),
            retention_period=Duration.days(4)
        )
        ## max_receive_count: Maximum number of attempts before moving to DLQ


        # 04. Create the Secret for the Verify Token
        verify_token_secret = secretsmanager.Secret(
            self,
            "WebhookGatewaySecret",
            secret_name="WebhookGateway-Secret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"VERIFY_TOKEN": ""}',
                generate_string_key="VERIFY_TOKEN",
                exclude_punctuation=True,
                password_length=32
            )
        )


        # 05. Create the Router Lambda Function
        router_lambda = _lambda.Function(
            self,
            "RequestRouter",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="request_router.handler",
            code=_lambda.Code.from_asset("lambda/request_router"),
            timeout=Duration.seconds(8),
            environment={
                'QUEUE_URL': main_queue.queue_url
            }
        )

        ## Give Router Lambda permissions to read from SQS queue
        main_queue.grant_consume_messages(router_lambda)
        
        ## Configure an Event Source for Router Lambda with SQS
        router_lambda.add_event_source(
            _lambda_event_sources.SqsEventSource(
                main_queue,
                batch_size=10,
                max_batching_window=Duration.seconds(30),
                report_batch_item_failures=True,
                max_concurrency=4
            )
        )


        # 06. Create the Authorizer Lambda Function
        authorizer_lambda = _lambda.Function(
            self,
            "Authorizer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="authorizer.handler",
            code=_lambda.Code.from_asset("lambda/authorizer"),
            timeout=Duration.seconds(8),
            environment={
                'SECRET_ARN': verify_token_secret.secret_arn
            }
        )

        ## Allow the Authorizer Lambda to read the secret
        verify_token_secret.grant_read(authorizer_lambda)

########################################################################################
# UNDER DEVELOPMENT FROM HERE
########################################################################################

        # 07. Create the Authorizer Integration
        authorizer_integration = apigw.LambdaIntegration(authorizer_lambda, proxy=True)

        # 08. Create the API Gateway
        api = apigw.RestApi(
            self,
            "WebhookGateway",
            rest_api_name="WebhookGateway-API",
            description="API Gateway of WebhookGateway Stack"
        )

        # 09. Create the API Gateway Resource
        messages = api.root.add_resource("messages")

        # 10. Create the API Gateway Method
        messages.add_method(
            "POST",
            authorizer_integration,
            authorization_type=apigw.AuthorizationType.CUSTOM,
            authorizer=apigw.RequestAuthorizer(
                handler=authorizer_integration,
                identity_source=["method.request.header.X-Auth-Token"],
                result_ttl_in_seconds=0
            )
        )

        # 07. Create an API Gateway
        api = apigw.RestApi(
            self, 
            "WebhookGateway",
            rest_api_name="WebhookGateway-API",
            description="API Gateway of WebhookGateway Stack"
        )


        ## TEST01

        ## Allow API Gateway to send messages directly to SQS
        sqs_integration_role = iam.Role(
            self,
            "ApiGatewaySqsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com")
        )

        ## Give API Gateway permission to interact with the SQS queue
        main_queue.grant_send_messages(sqs_integration_role)

        ## Create an integration with SQS
        sendMessagesIntegration = apigw.AwsIntegration(
            service="sqs",
            path=f"{self.account}/{main_queue.queue_name}",
            options=apigw.IntegrationOptions(
                credentials_role=sqs_integration_role,
                request_parameters={
                    "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
                },
                request_templates={
                    "application/json": "Action=SendMessage&MessageBody=$input.body"
                },
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"done": true}'
                        }
                    ),
                    apigw.IntegrationResponse(
                        status_code="500",
                        response_templates={
                            "application/json": '{"error": "message not sent"}'
                        }
                    ),
                ]
            )
        )

        ## Create a resource and method in API Gateway to send messages to SQS queue without Token
        messages = api.root.add_resource("messages")

        messages.add_method(
            "POST",
            sendMessagesIntegration,
            method_responses=[
                apigw.MethodResponse(status_code="200"),
                apigw.MethodResponse(status_code="500")
            ]
        )

        ## Crear un recurso y método en API Gateway para enviar mensajes a la cola SQS
        sendMessagesIntegration = apigw.LambdaIntegration(router_lambda, proxy=True)



        # ## TEST02 Create a resource and method in API Gateway to send messages to SQS queue without Token
        # messages = api.root.add_resource("messages")
        # webhook_integration = apigw.LambdaIntegration(router_lambda)
        # messages.add_method(
        #     "POST",
        #     webhook_integration,
        #     method_responses=[
        #         apigw.MethodResponse(status_code="200"),
        #         apigw.MethodResponse(status_code="500")
        #     ]
        # )



        # sendMessagesIntegration = apigw.AwsIntegration(
        #     service="sqs",
        #     region=self.region,  # Asegúrate de que la región esté especificada
        #     path=f"{self.account}/{main_queue.queue_name}",
        #     options=apigw.IntegrationOptions(
        #         credentials_role=sqs_integration_role,
        #         request_parameters={
        #             "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
        #         },
        #         request_templates={
        #             "application/json": "Action=SendMessage&MessageBody=$util.urlEncode($input.body)&Version=2012-11-05"
        #         },
        #         integration_responses=[
        #             apigw.IntegrationResponse(
        #                 status_code="200",
        #                 response_templates={
        #                     "application/json": """
        #                     {
        #                         "message": "Message sent successfully",
        #                         "messageId": "$input.path('SendMessageResponse.SendMessageResult.MessageId')"
        #                     }
        #                     """
        #                 }
        #             ),
        #             apigw.IntegrationResponse(
        #                 status_code="400",
        #                 selection_pattern=".*Error.*",
        #                 response_templates={
        #                     "application/json": '{"message": "Bad Request: Message not sent"}'
        #                 }
        #             ),
        #             apigw.IntegrationResponse(
        #                 status_code="500",
        #                 selection_pattern=".*",
        #                 response_templates={
        #                     "application/json": '{"message": "Internal Server Error"}'
        #                 }
        #             ),
        #         ]
        #     )
        # )



        ## Create a resource and method in API Gateway to send messages to SQS queue with Token
        # messages = api.root.add_resource("messages")
        # messages.add_method(
        #     "POST",
        #     sendMessagesIntegration,
        #     method_responses=[
        #         apigw.MethodResponse(status_code="200"),
        #         apigw.MethodResponse(status_code="500")
        #     ],
        #     authorizer=apigw.RequestAuthorizer(
        #         self,
        #         "APIAuthorizer",
        #         handler=authorizer_lambda,
        #         identity_sources=[apigw.IdentitySource.header("Authorization")]
        #     ),
        #     authorization_type=apigw.AuthorizationType.CUSTOM
        # )


        
        # Opcional: Crear un endpoint específico para enviar mensajes
        # messages = api.root.add_resource("messages")
        # messages.add_method("POST", sendMessagesIntegration)  # POST /messages
        
        # 8. (Opcional) Permitir que API Gateway envíe mensajes directamente a SQS
        # Si deseas que API Gateway envíe directamente a SQS sin pasar por Lambda, puedes configurar una integración SQS.
        # Sin embargo, en este ejemplo, usaremos Lambda como intermediario.
        
        # 9. Salidas (Outputs)
        CfnOutput(self, "Queue_Endpoint", value=main_queue.queue_url, description="Main Queue Endpoint")
        CfnOutput(self, "DLQ_Endpoint", value=dlq_queue.queue_url, description="Dead Letter Queue Endpoint")
        CfnOutput(self, "VerifyTokenSecretArn", value=verify_token_secret.secret_arn, description="Verify Token Secret ARN")