import json
import os
import time

import aiohttp
from dotenv import load_dotenv

load_dotenv()
bhashini_api_key = os.environ.get("BHASHINI_API_KEY")

async def translate_json(response):
    if isinstance(response, dict):
        return {k: await translate_json(v) for k, v in response.items()}
    elif isinstance(response, list):
        return [await translate_json(i) for i in response]
    elif isinstance(response, str):
        translated_text = await translate_text_bhashini(response, source='en', target='or')
        return translated_text[0] if translated_text else response  
    else:
        return response


async def translate_text_bhashini(input_text, source="hi", target="en"):
    if input_text == "":
        return "",""
    
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    payload = json.dumps(
        {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source,
                            "targetLanguage": target,
                        },
                        "serviceId": "ai4bharat/indictrans-v2-all-gpu--t4",
                    },
                }
            ],
            "inputData": {"input": [{"source": input_text}]},
        }
    )
    headers = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)",
        "Authorization": bhashini_api_key,
        "Content-Type": "application/json",
    }

    retries = 0
    max_retries = 5
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        while retries < max_retries:
            try:
                async with session.post(url, headers=headers, data=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        translated_output = response_data["pipelineResponse"][0]["output"][0]["target"]
                        end_time = time.time()
                        return translated_output, retries, end_time - start_time
                    else:
                        print(f"Request failed with status code {response.status}. Retrying...")
                        retries += 1
            except Exception as e:
                print(f"An error occurred: {e}. Retrying...")
                retries += 1

    end_time = time.time()
    return "Translation failed after maximum retries.", max_retries, end_time - start_time
