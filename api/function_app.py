import azure.functions as func
import logging
import json

import azure.functions as func
import logging
import os
import json
import time
from openai import AzureOpenAI
from openai import OpenAI

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_key = os.getenv("SEARCH_KEY")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

client = AzureOpenAI(
    azure_endpoint = endpoint,
    api_key = subscription_key,
    api_version = "2024-05-01-preview"
)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
def convert_to_hyperlink(url_string):
    # Ersätt `___` med `://` och `__` med `/`
    url_string = url_string.replace('___', '://').replace('_', '/')
    if url_string.endswith('/.json'):
        url_string = url_string[:-6]
    if url_string.endswith('/.txt'):
        url_string = url_string[:-5]
    return url_string

def call_ai(question):
    return({"answer":"Hello from ai!"})
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": question
            }
        ],
        max_tokens=500,
        temperature=0.4,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False,
        extra_body={
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "filter": None,
                        "endpoint": f"{search_endpoint}",
                        "index_name": "vector-1727789463490",
                        "semantic_configuration": "vector-1727789463490-semantic-configuration",
                        "authentication": {
                            "type": "api_key",
                            "key": f"{search_key}"
                        },
                        "embedding_dependency": {
                            "type": "endpoint",
                            "endpoint": (
                                "https://GaiAzureOpenAI.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-03-15-preview"
                            ),
                            "authentication": {
                                "type": "api_key",
                                "key": f"{subscription_key}"
                            }
                        },
                        "query_type": "vector_simple_hybrid", #testa enbart vektorsök också
                        "in_scope": True,
                        "role_information": (
                            "Du är en AI-assistent som vägleder kunder. \n\n"
                            "Du ska endast ge vägledning i frågor om B-körkort för kunder bosatta i Sverige.\n\n"
                            "Du ska svara trevligt, tydligt och med ett förenklat språk. Försök att vara kortfattad i ditt svar.\n\n"
                            "Du ska vara tydlig om kunden ska vända sig till transportstyrelsen eller trafikverket när det är relevant. \n\n"
                            "\"Jag kan tyvärr inte besvara din fråga med informationen jag har just nu. Du kan hitta mer information"
                            "om att ta körkort på Transportstyrelsens eller Trafikverkets hemsidor.\""
                        ),
                        "strictness": 3,
                        "top_n_documents": 10
                    }
                }
            ]
        }
    )

    answer = completion.to_json()
    #return completion
    answer = json.loads(answer)
    return answer
    citations = answer['choices'][0]['message']['context']['citations']
    result = {'answer':answer['choices'][0]['message']['content'], 'sources': []}
    i = 0
    if not citations:
        return result
    for citation in citations:
        result['sources'].append(convert_to_hyperlink(citation['title']))
        #result['sources'].append(citation['content'] + "/n Källa: " + convert_to_hyperlink(citation['title']))
    if not result:
        result = {"answer":"Hitta inget men letade"}  #Fixa till senare
    return result

@app.route(route="message")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    question = req.params.get('question')
    if not question:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            question = req_body.get('question')

    if question:
        answer = call_ai("Hur tar man körkort?")
        #print("Incoming request!")
        #no need to show the source texts, let's just format the source links here instead
        reply = "Vi gick väl igenom med frågan: " + question
        return func.HttpResponse(reply)
        #return func.HttpResponse("Vi gick väl igenom i alla fall") #Denna funkar iaf.
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a question in the query string or in the request body for a an answer.",
             status_code=200
        )