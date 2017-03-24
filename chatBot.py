from watson_developer_cloud import ConversationV1
import json
import fileinput
import atmLocator
import calculator
import requests

key = 'key-0335ffc6179bb9f65d104cf06eb11aae'
sandbox = 'sandbox102ac7d1115646e1a481e5ef5dce6f0b.mailgun.org'

request_url = 'https://api.mailgun.net/v2/{0}/messages'.format(sandbox)

#Opening Files
with open('config.json') as data_file:
    config = json.load(data_file)

with open('users.json') as data_file:
    users = json.load(data_file)

# Setting up Watson API's
conversation = ConversationV1(
  username=config['conversation']['username'],
  password=config['conversation']['password'],
  version='2017-02-03'
)

# Variables
global context
context = {}
workspace_id = 'fba7b3e5-6881-416c-9cf1-578fce2a9fee'

''' Authenticates/logs-in user '''
def authenticate(acc_no,pincode):
    if(users[acc_no]['pincode'] == pincode):
        return True
    else:
        return False

def getNumber(context):
    if( len(context) > 1):
        return int(context[2]['value'])
    else:
        return int(context[0]['value'])

def getCalculatorNumbers(context):
    listNum = []

    for i in range(len(context)):
        if(context[i]['entity'] == 'sys-number'):
            listNum.append(context[i]['value'])

    print(listNum)
    return listNum


def getDates(context):
    listNum = []

    for i in range(len(context)):
        if(context[i]['entity'] == 'sys-date'):
            listNum.append(context[i]['value'])


    return listNum

'''
Deals With Various responses and Updates Context Variables for directing conversation flow
'''
def dealWith(response):
    more_response = ''
    final_response = {}
    if('sentiment' not in response['context']):
        response['context']['sentiment'] = 0

    final_response['data'] = response['output']['text'][0]

    if('verified' in response['context']):


        if(response['output']['nodes_visited'][0] == 'fund-transfer-account-number'):
            response['context']['transfer-to'] = getNumber(response['entities'])

        if(response['output']['nodes_visited'][0] == 'fund-transfer-balance'):
            amountTransfer = getNumber(response['entities'])
            acc_no = response['context']['acc_no']
            acc_no_to = response['context']['transfer-to']
            if(int(users[acc_no]['balance']) >= amountTransfer):
                users[acc_no]['balance'] = int(users[acc_no]['balance']) - amountTransfer
                users[str(acc_no_to)]['balance'] = int(users[str(acc_no_to)]['balance']) + amountTransfer
                final_response['data'] = final_response['data'] + '\n' + 'Monay.Transfered.'
            else:
                final_response['data'] = final_response['data'] + '\n' + 'Im sorry.You have insufficient funds'


        if(response['output']['nodes_visited'][0] == 'fd-balance'):
            fd_balance = getNumber(response['entities'])
            acc_no = response['context']['acc_no']
            if(int(users[acc_no]['balance']) >= fd_balance):
                users[acc_no]['balance'] = int(users[acc_no]['balance']) - fd_balance
                final_response['data'] = final_response['data'] + '\n' + 'FD.Created.'
            else:
                final_response['data'] = final_response['data'] + '\n' + 'Im sorry.You have insufficient funds'



        if(response['output']['nodes_visited'][0] == 'mobile-number'):
            response['context']['mobile'] = response['entities'][0]['value']
            final_response['data'] = final_response['data'] + users['mobile-deals']

        if(response['output']['nodes_visited'][0] == 'recharge-money'):
            rechargeAmount = getNumber(response['entities'])
            acc_no = response['context']['acc_no']
            if(int(users[acc_no]['balance']) >= rechargeAmount):
                users[acc_no]['balance'] = int(users[acc_no]['balance']) - rechargeAmount
                final_response['data'] = final_response['data'] + '\n' + 'Mobile.Recharged.'
            else:
                final_response['data'] = final_response['data'] + '\n' + 'Im sorry.You have insufficient funds'



        if(response['context']['verified'] == "1" and response['output']['nodes_visited'][0] == 'bank-balance'):
            acc_no = response['context']['acc_no']
            more_response = users[acc_no]['name'] + "'s account balance is " + str(users[acc_no]['balance']) + " " + users[acc_no]['currency']
            final_response['data'] = final_response['data'] + '\n' + more_response + '\n' + 'is that okay ?'

        print(response['output']['nodes_visited'])

        if(response['context']['verified'] == "1" and response['output']['nodes_visited'][-1] == 'getting-dates'):

            acc_no = response['context']['acc_no']
            more_response = "Sending your account statement to " + users[acc_no]['email'] + "." + '\n' + 'did you receive it ?'
            final_response['data'] = final_response['data'] + '\n' + more_response
            dates = getDates(response['entities'])
            request = requests.post(request_url, auth=('api', key), data={
                'from': 'accountstatement@chatagram.com',
                'to': users[acc_no]['email'],
                'subject': 'Account Statement',
                'text': 'this is your account statement from ' + dates[0] + " to " + dates[1]
            })

    if(response['output']['nodes_visited'][0] == 'getting-data-fixed'):

        try:
            print(response['entities'])
            listNum = getCalculatorNumbers(response['entities'])
            principal_amount = int(listNum[0])
            rate_of_interest = int(listNum[1])
            tenure = int(listNum[2])


            final_response['data'] = final_response['data'] + '\n' + calculator.FD(principal_amount,rate_of_interest,tenure)

        except:
            final_response['data'] = final_response['data'] + '\n' + 'You need to type in all the required fields.Please try again !'


    if(response['output']['nodes_visited'][0] == 'getting-data-emi'):
        try:
            listNum = getCalculatorNumbers(response['entities'])
            principal_amount = int(listNum[0])
            rate_of_interest = int(listNum[1])
            tenure = int(listNum[2])

            final_response['data'] = final_response['data'] + '\n' + calculator.EMI(principal_amount,rate_of_interest,tenure)
        except:
            final_response['data'] = final_response['data'] + '\n' + 'You need to type in all the required fields.Please try again !'

    if(response['output']['nodes_visited'][0] == 'getting-data-compound'):
        try:
            listNum = getCalculatorNumbers(response['entities'])
            principal_amount = int(listNum[0])
            rate_of_interest = int(listNum[1])
            tenure = int(listNum[2])

            final_response['data'] = final_response['data'] + '\n' + calculator.CI(principal_amount,rate_of_interest,tenure)
        except:
            final_response['data'] = final_response['data'] + '\n' + 'You need to type in all the required fields.Please try again !'


    if(response['output']['nodes_visited'][0] == 'map'):
        more_response = atmLocator.getAtm()
        final_response['map'] = 1
        final_response['data'] = more_response


    # updating context stuff
    if(response['output']['nodes_visited'][-1] == 'positive'):
        response['context']['sentiment'] = int(response['context']['sentiment']) + 1
        print(response['context']['sentiment'])


    if(response['output']['nodes_visited'][-1] == 'negative'):
        response['context']['sentiment'] = int(response['context']['sentiment']) - 1
        print(response['context']['sentiment'])


    if(response['output']['nodes_visited'][0] == 'account-number'):
        response['context']['acc_no'] = response['entities'][2]['value']
        acc_no = response['context']['acc_no']
        print(response['entities'])
        response['context']['pincode'] = users[acc_no]['pincode']


    if(response['context']['sentiment'] > 5):
        final_response['data'] = final_response['data'] + '\n' + 'If you like this service please check out <awesome-product-here> and <another-awesome-product-here>.FOr more information visit <interesting-links-here>'
        response['context']['sentiment'] = 0

    if(response['context']['sentiment'] < -5):
        final_response['data'] = final_response['data'] + '\n' + 'If you are having trouble with this service, our human operator is more than happy to help. Contact Shilpa <number here>, toll free'
        response['context']['sentiment'] = 0

    return response,final_response


''' Helper functions '''
def printJSON(printThis):
    print(json.dumps(printThis, indent=2))

''' Driver main function '''
def converse(inputline):

    global context
    response = conversation.message(
      workspace_id=workspace_id,
      message_input={'text': inputline},
      context=context
    )

    response,final_response = dealWith(response)
    context = response['context']
    return final_response
