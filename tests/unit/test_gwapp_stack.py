import aws_cdk as core
import aws_cdk.assertions as assertions

from gwapp.gwapp_stack import GwappStack

# example tests. To run these tests, uncomment this file along with the example
# resource in gwapp/gwapp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GwappStack(app, "gwapp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
