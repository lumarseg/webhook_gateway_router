
# Webhook Gateway Router Project

This is a project for CDK development with Python.

Webhook Gateway App is a serverless application designed to receive all RESTful
requests from META through a single webhook and route them to the various
webhooks of Amazon API Gateway used in In2clouds’ POCs (Proof of Concepts).

These POCs integrate META’s messaging services with Amazon Connect. In this way,
the application serves as a centralized webhook router.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.
