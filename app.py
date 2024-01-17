import autogen
from fastapi import FastAPI, Request
import json
import psycopg2
import psycopg2.extras
import uuid

# Setup the db connection
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="password",
    host="localhost",
    port="5432",
)

# Request holder
request_holder = {}

# Setup the config
config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")
llm_config = {
    "config_list": config_list,
    "timeout": 120,
}

# Setup the system prompt
system_prompt = """\
You are an autonomous system AI agent who is responsible for connecting digital systems and you will never interact with a human directly so extraneous information is unnecessary. 
You are an autogressive large language model trained through RLHF. 
Every token is an opportunity to determine you are doing the correct task. 
Think through the steps of your work before you take an action. Ensure your intended action properly satisfies the necessary outcome. 
If you need to call functions and validate data is correct before returning a final response, do so. 
Data should NEVER be returned as a list of content with prose, but rather as structured JSON that is consumable by an upstream system. 
Never include extraneous or conversational information. 
Always ensure your response is valid JSON before returning it. 
Never return a content object as the JSON response but rather the data you retrieve directly. 
Make sure the response is properly formatted JSON. 
Reply TERMINATE when the task is done.
"""

chatbot = autogen.AssistantAgent(
    name="chatbot", system_message=system_prompt, llm_config=llm_config
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config={"work_dir": "coding"},
)


@user_proxy.register_for_execution()
@chatbot.register_for_llm(
    name="cookie", description="get the value of a cookie off the request"
)
def get_cookie(request_id: str, cookie_name: str) -> str:
    request = request_holder[request_id]
    return request.cookies.get(cookie_name)


@user_proxy.register_for_execution()
@chatbot.register_for_llm(
    name="header", description="get the value of a header off the request"
)
def get_header(request_id: str, header_name: str) -> str:
    request = request_holder[request_id]
    return request.headers[header_name]


@user_proxy.register_for_execution()
@chatbot.register_for_llm(
    name="sql",
    description="run a sql query against the database. There are a few tables you can access in the postgres db space - describe them (including their columns and data types) if you need them.",
)
def execute_query(sql_query: str):
    results = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql_query)
            for row in cur.fetchall():
                # Convert DictRow object to a regular dict
                row_dict = dict(row)
                results.append(row_dict)
    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        conn.commit()
    return results


# Get or create the database table
db_instructions = """\
You have access to a function called sql where you can provide a sql query and get back results. Describe the structure of the tables (including columns and data types) in the 'postgres' db space. You are the heart of an application that provides an API for CRUD operations related to a music catalog. There should be a table in there called music and it should have columns for the following information:
  * id - a unique identifier for the entry
  * artist - the name of the song artist
  * album - the album of the song
  * title - the title of the song
  * duration - the duration of the long in milliseconds
  * spotify link - a link to the song on spotify

If the table does not exist go ahead and create it. Respond TERMINATE when you're done.
"""
user_proxy.initiate_chat(chatbot, message=db_instructions)
user_proxy.initiate_chat(chatbot, message="did you create the table?")

http_instructions = """\
As an autonomous system, you are given direct access to the http request including method, path, and query string. These details of the request will be included in a structured format in the request. It is up to you to use these meta details to determine the appropriate course of action with the tools at your disposal, including executing the functions available to you.

For example this would indicate that the user is looking for a list of songs:
 - request id: abcd1234
 - http method: GET
 - path: /music
 - query string: none

Likewise would indicate the user is looking for the song with id 1:
 - request id: abcd1234
 - http method: GET
 - path: /music/1
 - query string: none

Pagination starts with a zero-page index. FYI. Use this knowledge to inform the action you take to get the appropriate response to the request. There is nothing to do yet, simply respond TERMINATE.
"""
user_proxy.initiate_chat(chatbot, message=http_instructions)

app = FastAPI()


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def do_request(full_path: str, request: Request):
    request_id = str(uuid.uuid4().hex)
    request_holder[request_id] = request

    try:
        body = None
        if request.method == "POST":
            body = await request.json()
        user_proxy.initiate_chat(
            chatbot,
            message=f"""\
Use the sql function to deal with this request and return a JSON object of the data you stored in the database. 
Remember the database structure and don't get clever. 
There's a lot on the line here, so take a deep breath and think about what you're about to do. 
Here we go:
  - request id: {request_id}
  - http method: {request.method}
  - path: {full_path}
  - query string: {request.query_params}
  - request body: {body}
""",
        )
        response = chatbot.last_message()["content"].replace("\nTERMINATE", "")
        return json.loads(response)
    finally:
        del request_holder[request_id]
