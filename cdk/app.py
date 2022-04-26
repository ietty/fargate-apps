#!/usr/bin/env python3
import os

import aws_cdk as cdk

from lib.alb_stack import AlbStack
from lib.sample_stack import NginxStack
from lib.scipy_stack import ScipyStack
from lib.jupyter_stack import JupyterStack
from lib.jupyter_nlp_def import JupyterNlpDefStack
#from lib.jupyter_nlp_stack import JupyterNlpStack

site = os.getenv('CDK_ENV', 'staging')
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')
)

# stack定義
app = cdk.App()

alb = AlbStack(
    app, "Alb",
    site,
    env=env,
)

NginxStack(
    app, "Sample",
    site,
    alb,
    env=env
)

JupyterNlpDefStack(
    app, "NlpDef",
    site,
    env=env
)

JupyterStack(
    app, "jupyter",
    site,
    alb,
    env=env,
)

app.synth()
