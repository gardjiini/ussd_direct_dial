from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# In-memory session store
sessions = {}

@csrf_exempt
def ussd_view(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON request body
            data = json.loads(request.body.decode('utf-8'))
            print("Incoming Data:", data)  # Debugging line to check the incoming data
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Extract necessary USSD fields from the request
        ussd_id = data.get('USERID', '')
        msisdn = data.get('MSISDN', '')
        user_data = data.get('USERDATA', '')  # For direct dial, this will be the entire string after *920*1803*
        session_id = data.get('SESSIONID', '')

        print("USERDATA:", user_data)  # Debugging line to check the value of USERDATA

        if not session_id:
            return JsonResponse({'error': 'SESSIONID is missing'}, status=400)

        # Retrieve or create session
        if session_id not in sessions:
            sessions[session_id] = {'screen': 1, 'feeling': '', 'reason': ''}

        session = sessions[session_id]

        # Define mappings for feelings and reasons
        feelings = {
            '1': 'Feeling fine',
            '2': 'Feeling frisky',
            '3': 'Not well'
        }
        reasons = {
            '1': 'because of money issues',
            '2': 'because of relationship',
            '3': 'because of a lot'
        }

        # Handle the case where user_data includes the USSD code prefix
        if user_data.startswith('*920*1803*'):
            user_data = user_data.replace('*920*1803*', '')  # Remove the prefix

        print("Processed USERDATA:", user_data)  # Debugging line to check the processed USERDATA

        # Handle the case where user_data is empty (i.e., base dial like *920*1803#)
        if user_data == '*920*1803':
            if session['screen'] == 1:
                msg = f"Welcome to {ussd_id} USSD Application.\nHow are you feeling?\n1. Feeling fine\n2. Feeling frisky\n3. Not well."
                return JsonResponse({
                    "USERID": ussd_id,
                    "MSISDN": msisdn,
                    "USERDATA": user_data,
                    "SESSIONID": session_id,
                    "MSG": msg,
                    "MSGTYPE": True  # Keep the session open
                })

        # Split the input into individual options, removing trailing '#' if present
        input_parts = user_data.strip('#').split('*')

        print("Input Parts:", input_parts)  # Debugging line to check the split input parts

        # Handle the first screen if user_data has only one input part
        if session['screen'] == 1 and len(input_parts) == 1:
            feeling_input = input_parts[0]

            # Validate the feeling input
            if feeling_input not in feelings:
                return JsonResponse({
                    "USERID": ussd_id,
                    "MSISDN": msisdn,
                    "USERDATA": user_data,
                    "SESSIONID": session_id,
                    "MSG": "Invalid feeling input. Please dial again.\nHow are you feeling?\n1. Feeling fine\n2. Feeling frisky\n3. Not well.",
                    "MSGTYPE": True  # Keep the session open
                })

            # Store the user's feeling and move to the next screen
            session['feeling'] = feelings[feeling_input]
            session['screen'] = 2  # Move to the second screen
            msg = f"Why are you {session['feeling']}?\n1. Money issues\n2. Relationship\n3. A lot."
            return JsonResponse({
                "USERID": ussd_id,
                "MSISDN": msisdn,
                "USERDATA": user_data,
                "SESSIONID": session_id,
                "MSG": msg,
                "MSGTYPE": True  # Keep the session open
            })

        # Handle the second screen if user_data has one or two input parts
        if session['screen'] == 2 and len(input_parts) == 1:
            reason_input = input_parts[0]

            # Validate the reason input
            if reason_input not in reasons:
                return JsonResponse({
                    "USERID": ussd_id,
                    "MSISDN": msisdn,
                    "USERDATA": user_data,
                    "SESSIONID": session_id,
                    "MSG": f"Invalid reason input. Please dial again.\nWhy are you {session['feeling']}?\n1. Money issues\n2. Relationship\n3. A lot.",
                    "MSGTYPE": True  # Keep the session open
                })

            # Final message based on the sequential input
            reason = reasons[reason_input]
            msg = f"You are {session['feeling']} {reason}."

            # End the session and return the final message
            return JsonResponse({
                "USERID": ussd_id,
                "MSISDN": msisdn,
                "USERDATA": user_data,
                "SESSIONID": session_id,
                "MSG": msg,
                "MSGTYPE": False  # End the session
            })

        # Handle the long code with both feeling and reason in one go
        if len(input_parts) == 2:
            feeling_input, reason_input = input_parts

            # Validate the feeling and reason inputs
            if feeling_input not in feelings or reason_input not in reasons:
                return JsonResponse({
                    "USERID": ussd_id,
                    "MSISDN": msisdn,
                    "USERDATA": user_data,
                    "SESSIONID": session_id,
                    "MSG": "Invalid input format. Please dial again.",
                    "MSGTYPE": False  # End the session
                })

            # Final message based on the direct dial input
            feeling = feelings[feeling_input]
            reason = reasons[reason_input]
            msg = f"You are {feeling} {reason}."

            # End the session and return the final message
            return JsonResponse({
                "USERID": ussd_id,
                "MSISDN": msisdn,
                "USERDATA": user_data,
                "SESSIONID": session_id,
                "MSG": msg,
                "MSGTYPE": False  # End the session
            })

        # Invalid input format
        return JsonResponse({
            "USERID": ussd_id,
            "MSISDN": msisdn,
            "USERDATA": user_data,
            "SESSIONID": session_id,
            "MSG": "Invalid input format. Please dial again.",
            "MSGTYPE": False  # End the session
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)
