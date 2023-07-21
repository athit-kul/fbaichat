
from flask import Flask, request
from dotenv import load_dotenv
from gpt_index import GPTSimpleVectorIndex
import requests
import os

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
chat_index = None
message_count = 0


def load_index():
    global chat_index
    if(os.path.exists('index.json')):
        chat_index = GPTSimpleVectorIndex.load_from_disk('index.json')
    

def chatbot(input_text):
    global chat_index
    response = chat_index.query(input_text, response_mode="compact")
    return response.response


load_index()

app = Flask(__name__)

# This is page access token that you get from facebook developer console.
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
# This is API key for facebook messenger.
API = "https://graph.facebook.com/v13.0/me/messages?access_token="+PAGE_ACCESS_TOKEN



# การใช้งาน
# เปิด command prompt :
# ngrok http 5000 
# เพื่อให้ได้ Forwording https เอาไปแปะใน webhook

# เข้า https://developers.facebook.com/apps/234184949535623/messenger/settings/
# แก้ Webhooks > callbackurl
# verify_token = Kasamajin


@app.route("/", methods=['GET'])
# This function use for verify token with facebook webhook. So we can verify our flask app and facebook are connected.
def fbverify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.getenv("Facebook_Verify_Token"):
            return "Verification token missmatch", 403
        return request.args['hub.challenge'], 200
    return "Hello world", 200

# This function return response to facebook messenger.


@app.route("/", methods=['POST'])
def fbwebhook():
    global message_count
    data = request.get_json()
    print(data)
    try:
        # Read messages from facebook messanger.
        message = data['entry'][0]['messaging'][0]['message']
        sender_id = data['entry'][0]['messaging'][0]['sender']['id']
        # Here we get message text and check specific text so we can send response specificaly.
        reply_message = chatbot(message['text'])
        request_body = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": reply_message
            }
        }
        response = requests.post(API, json=request_body).json()

        message_count += 1
        print("MessageNum=" + str(message_count) + " Text= " + str(reply_message))

        return response

    except:
        # Here we are store the file to our server who send by user from facebook messanger.
        try:
            mess = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['url']
            print("for url-->", mess)
            json_path = requests.get(mess)
            filename = mess.split('?')[0].split('/')[-1]
            open(filename, 'wb').write(json_path.content)
        except:
            print("Noot Found-->")

    return 'ok'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 33507))
    app.run(host='0.0.0.0', port=port)