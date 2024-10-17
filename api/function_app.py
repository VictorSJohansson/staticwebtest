import azure.functions as func
import logging
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="message")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(
            json.dumps({ "message": f"Hello, {name}. This HTTP triggered function executed successfully." }),
            mimetype="application/json",
            status_code=200
        )
    else:
        return func.HttpResponse(
            json.dumps({ "message": "Name not provided" }),
            mimetype="application/json",
            status_code=200
        )