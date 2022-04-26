import aws_cdk as core
import aws_cdk.assertions as assertions

from fargate_apps.fargate_apps_stack import FargateAppsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in fargate_apps/fargate_apps_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FargateAppsStack(app, "fargate-apps")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
