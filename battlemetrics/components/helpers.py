from datetime import timedelta, datetime
import json
from time import strftime, localtime

import aiohttp
import re
import asyncio

class Helpers:

    def __init__(self, api_key: str) -> None:
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _make_request(self, method: str, url: str, params: dict = None, json_dict:dict= None) -> dict:
        """Queries the API and spits out the response.
        Args:
            method (str): One of: GET, POST, PATCH, DELETE
            url (str): The endpoint/url you wish to query.
            params (dict, optional): Any params you wish to send to enhance your experience?. Defaults to None.
            json (dict, optional): json data you wish to send to enhance your experience?. Defaults to None.
        Raises:
            Exception: Doom and gloom.
        Returns:
            dict: The response from the server.
        """

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(method=method, url=url, json=json_dict, params=params) as r:
            
                content_type = r.headers.get('content-type', '')
                response_status = int(r.status)
                
                if response_status >= 400:
                    if response_status == 429:
                        print("You're being rate limited. Waiting 30 seconds and trying again.")
                        await asyncio.sleep(30)
                        return await self._make_request(method=method, url=url,params=params, json_dict=json_dict)
                    else:
                        try:
                            response = await r.json()
                            if response.get('errors'):
                                print(json.dumps(response, indent=4))
                            return response
                        except Exception as e:
                            print(e)
                            response = await r.text()
                            with open('errors.txt', 'w') as f:
                                f.write(response)
                
                if 'json' in content_type:
                    try:
                        response = await r.json()
                    except Exception as e:
                        print(f"There's an issue with the respon json data.. Going to try and fix!\n<<Exception@Json>>\n{e}\n")
                        try:
                            stream = await r.content.read()
                            if len(stream) < 10:
                                stream = await r.text()
                            try:
                                response = json.loads(stream)
                                return response
                            except Exception as e:
                                print(f"Tried turning a text to dict.. Failed..\n{e}")
                                response = await self._exception_handler(stream)
                        except Exception as e:
                            print(f"Even the exception handler can't handle this nonsene!\n{e}")
                            
                elif 'octet-stream' in content_type:
                    stream = await r.text(encoding='utf-8')
                    pattern = re.compile(r"""
                            ^\s*banid[ ]              # Appears to be a literal, skip this
                            (?P<steamid>\d+)[ ]         # that banID number
                            "(?P<name>.*?)"[ ]        # whodunnit
                            "(?P<reason>.*?)"[ ]      # what they did
                            (?P<duration>-?\d*)\s*$   # the duration of the ban
                        """, re.VERBOSE)
                    data = []
                    for line in stream.splitlines():
                        if line.strip() == "":
                            continue
                        if contents := pattern.match(line):
                            contents = contents.groupdict()
                            if contents['duration'] == "-1":
                                contents['duration'] = "Permanent"
                            else:
                                duration = int(contents['duration'])
                                try:
                                    duration = strftime(
                                        '%Y-%m-%d %H:%M:%S', localtime(duration))
                                    print(duration)
                                except Exception as e:
                                    print(f"Failed to convert duration to time, defaulted to 'The future'\nSteam ID: {contents['steamid']}\nDuration: {duration}\nError: {e}")
                                    duration = "The future"
                                contents['duration'] = duration
                            data.append(contents)
                        else:
                            print(f"Voodoo Failed. VOODOOO FAILED! PANIC!!\n{line}")
                    return data
                
                elif 'text/html' in content_type:
                    response = await r.text()
                    response = response.replace("'", "").replace("b", "")
                else:
                    raise Exception(f"Unsupported Content Type: {content_type}\n Some additional stuff: {r}\nresponse_status: {response_status}")
                await session.close()
        return response

    #This function attempts to find and fix any errors in the JSON response.
    async def _exception_handler(self, response_content) -> dict:
        print("Exception Handler Running...Attempting to fix the response.")
        if type(response_content) == bytes:
            json_string: str = response_content.decode('utf-8')
        else:
            json_string = response_content
        loops = 0
        max_loops = 50000
        while True and loops < max_loops:
            loops += 1
            try:
                response = json.loads(json_string)
                print(f"Fixer ending early \o/ Ran: {loops} times!")
                return response
            except json.JSONDecodeError as e:
                # Get the position of the error
                error_position = e.pos
                
                # Attempt to fix the error based on the type of error
                if e.msg == "Expecting value":
                    # Remove unexpected characters from the beginning of the string
                    if json_string[error_position-1] == ":" and json_string[error_position-2] == "\"" and json_string[error_position-3] == "\"":
                        json_string = json_string[:error_position-4] + json_string[error_position:]
                    elif json_string[error_position-1] == ":":
                        json_string = json_string[:error_position-1] + 'Test' + json_string[error_position-1:]
                    else:
                        json_string = json_string[:error_position-2] + json_string[error_position-2:]
                elif e.msg == "Extra data":
                    # Remove unexpected characters from the end of the string
                    json_string = json_string[:error_position]
                elif e.msg == "Unterminated string":
                    # If the string is unterminated, add a closing quote
                    json_string = json_string[:error_position] + '"' + json_string[error_position:]
                elif e.msg == "Expecting ':'":
                    # If there's a missing colon, add it at the appropriate position
                    json_string = json_string[:error_position] + ':' + json_string[error_position:]
                elif e.msg == "Expecting ',' or ']'":
                    # If there's a missing comma or bracket, add it at the appropriate position
                    json_string = json_string[:error_position] + ',' + json_string[error_position:]
                elif e.msg == "Expecting property name enclosed in double quotes":
                    # If property names are not enclosed in double quotes, add them
                    json_string = json_string[:error_position] + '"' + json_string[error_position:]
                    next_quote_position = json_string.find('"', error_position + 1)
                    if next_quote_position != -1:
                        json_string = json_string[:next_quote_position] + '"' + json_string[next_quote_position:]
                    else:
                        # If there's no closing quote, add one at the end of the string
                        json_string += '"'
                elif "Expecting ':' delimiter" in e.msg:
                    json_string = json_string[:error_position] + ':' + json_string[error_position:]
                else:
                    # If the error is not recognized, return None
                    print(f"EXITED FIXER AFTER RUNNING {loops} times!\n{e}")
                    return None
        print("Loop failed to achieve anything. Just like my life.")
        return
    
    #Keeping here in case we need this in future. Never know.
    async def _parse_octet_stream(self, response:str) -> dict:
        """Takes your banlist file from the API request and processes it into a dictionary
        Args:
            response (octet-stream): The file response from the API
        Returns:
            dict: Returns the converted file in dictionary form.
        """

        cfg_str = response
        ban_dict = {}
        for line in cfg_str.split("\n"):
            if line.startswith("banid"):
                line_parts = line.split(" ")
                steam_id = line_parts[1]
                player_name = line_parts[2].strip('"')
                reason_parts = line_parts[3:-1]
                duration = line_parts[-1]
                if duration == "-1":
                    duration = "Permanent"
                if duration.isdigit():
                    duration = int(duration)
                    try:
                        duration = strftime(
                            '%Y-%m-%d %H:%M:%S', localtime(duration))
                    except:
                        duration = "FOREVER!"
                reason = " ".join(reason_parts).strip('"')
                ban_dict[steam_id] = {
                    "playername": player_name, "reason": reason, "expires": duration}
        return ban_dict

    async def _replace_char_at_position(self, input_string:str, position:int, new_character:str) -> str:
        return input_string[:position] + new_character + input_string[position + 1:]

    async def calculate_future_date(self, input_string:str) -> str:
        # Extract the numeric part and unit from the input string
        number = int(input_string[:-1])
        unit = input_string[-1]

        # Define a dictionary to map units to timedelta objects
        unit_to_timedelta = {
            'd': timedelta(days=number),
            'w': timedelta(weeks=number),
            'm': timedelta(minutes=number),  # Approximate for months
            'h': timedelta(hours=number),
            's': timedelta(seconds=number)# Hours
        }

        # Get the timedelta object based on the unit
        delta = unit_to_timedelta.get(unit)

        if delta:
            # Calculate the future date by adding the timedelta to the current date
            future_date = str(datetime.now() + delta)
            future_date = future_date.replace(" ", "T")
            future_date += "Z"
            return future_date
        else:
            return None
        
        