#Python libraries that we need to import for our bot
import random
from flask import Flask, request
from pymessenger.bot import Bot
import requests
import json # For reading json from api
from dateutil import parser # For parsing date

from enum import Enum

app = Flask(__name__)
ACCESS_TOKEN = 'EAAfontqk504BALpGOnCq26CNqO7lrC4qVtAZBN5ei9Hc4zyoKpXmNttjvLcXqoMMOJjcgmdQJKIFN02SZA47JosUmUZB8UMIlQGmEmVS7p5XyvS0ipiAunnU38Lj81kE6ZCw5elMxK4t1MTHY6TilzstHhJU5mtxMHnv1paG8WvW7Tw72pLOYEjCKoHDOjAZD'
VERIFY_TOKEN = 'FACEBOOK_VERIFY_TOKEN_CHICAGO_2019'

bot = Bot(ACCESS_TOKEN)

class NotificationType(Enum):
    regular = "REGULAR"
    silent_push = "SILENT_PUSH"
    no_push = "NO_PUSH"

def send_quick_reply(self, recipient_id, text, option1, option2, pl, notification_type=NotificationType.regular):
        return self.send_recipient(recipient_id, {"message": {"text": text, "quick_replies": [{"content_type": "text", "title": option1, "payload": option1+'|'+pl}, {"content_type": "text", "title": option2, "payload": option2+'|'+pl}]}}
        , notification_type)

def send_recipient(self, recipient_id, payload, notification_type=NotificationType.regular):
    payload['recipient'] = {
        'id': recipient_id
    }
    payload['notification_type'] = notification_type.value
    return self.send_raw(payload)


Bot.send_quick_reply = send_quick_reply
Bot.send_recipient = send_recipient

#curr_payload=''
quickreply_payload = ''

#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       print(json.dumps(output))
       for event in output['entry']: # If using ?ref=, then that will be one of the events.
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                if message['message'].get('text'):
                    has_payload = False
                    if message['message'].get('postback') or message['message'].get('quick_reply'):
                        has_payload=True
                    msg = message['message'].get('text')
                    response_sent_text, type_ = get_message(msg, has_payload)

                    # If we are just sending back a string message
                    if type_=='txt':
                        send_message(recipient_id, response_sent_text)

                    # If we are sending a carousel...
                    elif type_ == 'carousel':
                        send_carousel_message(recipient_id,response_sent_text)

                    # Remain silent but capture the payload
                    elif type_=='silence':
                        print('REMAIN SILENT!')
                        quickreply_payload = message['message']['quick_reply']['payload']
                        #print(curr_payload)
                        #send_message(recipient_id, curr_payload)
                        print(quickreply_payload)
                        send_message(recipient_id, quickreply_payload)
                        #if quickreply_payload == 'Pick who wins':
                        #    send_quick_reply(recipient_id, 'Who will win?', curr_payload.split(' @ ')[0], curr_payload.split(' @ ')[1])


                    # The default
                    else:
                        send_message(recipient_id,'Im Confused!')

                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    response_sent_nontext = get_message()
                    send_message(recipient_id, response_sent_nontext)

            elif message.get('postback'):
                if message['postback']['title'] == 'Play':
                    recipient_id = messaging[0]['sender']['id']
                    curr_payload = message['postback']['payload']
                    send_message(recipient_id, curr_payload)
                    print(curr_payload)


                    send_quick_reply(recipient_id,'What type of betting?','Pick who wins','Over Under',curr_payload)

            # elif message.get('quick_reply'):
            #     send_message(recipient_id,'in_quick-reply')
            #     if ' @ ' in curr_payload:
            #         send_message(recipient_id,'@')
            #         team1 = curr_payload.split(' @ ')[0]
            #         team2 = curr_payload.split(' @ ')[1]

            #         if quickreply_payload == 'Pick who wins':
            #             send_quick_reply(recipient_id, 'Who will win?', team1, team2)




    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


#chooses a random message to send to the user
def get_message(msg, has_payload):
    if msg=='hey':
        return 'wassup', 'txt'
    if msg=='What games are upcoming?':
        TODAY = '20191103' # Change to dynamic today, or can change to different timelines

        # Load in upcoming game info
        r = json.loads(requests.get('http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=9&dates='+TODAY).text)

        # Loop through and get all upcoming games
        list_of_elements = []
        for i in r['events']:
            if 'odds' in i['competitions'][0]:
                e = {}
                e['title'] = i['shortName']
                e['image_url'] = 'https://static.nfl.com/static/content/public/static/img/share/shield.jpg'
                
                gametime = parser.parse(i['date'])
                odds = i['competitions'][0]['odds'][0]['details']
                overunder = i['competitions'][0]['odds'][0]['overUnder']
                e['subtitle'] = 'Game Time: '+str(gametime.month)+'-'+str(gametime.day)+'-'+str(gametime.year)+' '+str(gametime.hour)+':'+str(gametime.minute)+':00 | Spread: '+odds+' | Over Under: '+str(overunder)
                default_action_dict = {}
                default_action_dict['type'] = 'web_url'
                default_action_dict['url'] = 'nfl.com'
                default_action_dict['webview_height_ratio'] = 'tall'
                e['default_action'] = default_action_dict

                #playbutton = {'type':'web_url', 'url':'nfl.com','title':'Play!'}
                playbutton = {'type':'postback','title':'Play','payload':e['title']} # Send the name of the game as a payload
                challengebutton = {'type':'web_url', 'url':'nfl.com','title':'Challenge'}
                infobutton = {'type':'web_url', 'url':'nfl.com','title':'More Info'}
                
                e['buttons'] = [playbutton,challengebutton,infobutton]

                list_of_elements.append(e)

        #tmp = [{"title": "HOU @ JAX", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T14:30Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "WSH @ BUF", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T18:00Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "NYJ @ MIA", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T18:00Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "CHI @ PHI", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T18:00Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "IND @ PIT", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T18:00Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "TEN @ CAR", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T18:00Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "DET @ OAK", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T21:05Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "TB @ SEA", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T21:05Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "CLE @ DEN", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T21:25Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "GB @ LAC", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-03T21:25Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}, {"title": "NE @ BAL", "image_url": "https://static.nfl.com/static/content/public/static/img/share/shield.jpg", "subtitle": "2019-11-04T01:20Z", "default_action": {"type": "web_url", "url": "nfl.com", "webview_height_ratio": "tall"}, "buttons": [{"type": "web_url", "url": "nfl.com", "title": "Play!"}, {"type": "web_url", "url": "nfl.com", "title": "Challenge!"}, {"type": "web_url", "url": "nfl.com", "title": "More Info"}]}]
        #return [list_of_elements[0], list_of_elements[1]], 'carousel'

        return list_of_elements, 'carousel'

    else:
        if has_payload:
            return 'delet this','silence'
        else:
            sample_responses = ["You are stunning!", "We're proud of you.", "Keep on being you!", "We're greatful to know you :)"]
                # return selected item to the user
            return random.choice(sample_responses), 'txt'


#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

# Send the carousel response to "What games are coming up?"
def send_carousel_message(recipient_id, elements):
    bot.send_text_message(recipient_id, 'sending carousel...')
    #bot.send_text_message(recipient_id, json.loads(elements[0]))
    bot.send_generic_message(recipient_id, elements)
    return "success"

def send_quick_reply(recipient_id,text,option1,option2,pl):
    bot.send_quick_reply(recipient_id,text,option1,option2,pl)

if __name__ == "__main__":
    app.run()
