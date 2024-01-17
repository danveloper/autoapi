# AutoAPI

_What if we wired an LLM to an HTTP server and connected it to a database and told it to be an API?_

I built this because I think we're at a point where AI systems can reason about a desired technical outcome and materialize that functionality on demand, without developers having to spend valuable brain power on rote development tasks. Development tasks will more fall to describing outcomes and not writing stepwise system logic.

This project uses [autogen](https://github.com/microsoft/autogen) to connect a LLM to a database and put it inline to all requests coming into a FastAPI server in order to materialize a RESTful HTTP API from a description of functionality provided by the developer.

It's a proof of concept for that theory and it does work, albeit not as reliably as I'd like with my prompts, though I'm confident that with some time and effort the prompts can be improved to yield more consistent results. I tested against GPT-4 and a [local version of Llama-2 fine-tuned for function calls](https://huggingface.co/Trelis/Llama-2-7b-chat-hf-function-calling-v2). It (obviously) works best when using GPT-4.

## Setting up

The `requirements.txt` file has all the dependencies. Install them:

```bash
pip install -r requirements.txt
```

You'll need to copy the `OAI_CONFIG_LIST.example` file to `OAI_CONFIG_LIST` and fill in your API key (or [configure it to talk to a local API server](https://github.com/microsoft/autogen/blob/46e76d244f6961b2c2d9e4aa544eb41a54f79147/website/blog/2023-07-14-Local-LLMs/index.md#L2)).

Startup a postgres:

```bash
docker run --env=POSTGRES_PASSWORD=password -p 5432:5432 -t -d postgres
```

## Running

The project uses the FastAPI web framework and as such uses `uvicorn` under the hood.

```bash
uvicorn run app:app
```

## Example output

You can see I've added some areas where I try to encourage it a little better (`did you create the table?`) and it's not so perfect. It fucks up the first attempt at posting to the API, but then it eventually gets it right. Like I said, with more work on the prompts I think this could actually work consistently and reliably.

```
$ rm -rf .cache && uvicorn app:app
The return type of the function 'execute_query' is not annotated. Although annotating it is optional, the function should return either a string, a subclass of 'pydantic.BaseModel'.
user_proxy (to chatbot):

You have access to a function called sql where you can provide a sql query and get back results. Describe the structure of the tables (including columns and data types) in the 'postgres' db space. You are the heart of an application that provides an API for CRUD operations related to a music catalog. There should be a table in there called music and it should have columns for the following information:
  * id - a unique identifier for the entry
  * artist - the name of the song artist
  * album - the album of the song
  * title - the title of the song
  * duration - the duration of the long in milliseconds
  * spotify link - a link to the song on spotify

If the table does not exist go ahead and create it. Respond TERMINATE when you're done.


--------------------------------------------------------------------------------
chatbot (to user_proxy):

***** Suggested tool Call (call_PrrQFWR8q93LFR4RVzkB6ygH): sql *****
Arguments: 
{
  "sql_query": "CREATE TABLE IF NOT EXISTS music (id SERIAL PRIMARY KEY, artist VARCHAR(255), album VARCHAR(255), title VARCHAR(255), duration INT, spotify_link TEXT)"
}
********************************************************************

--------------------------------------------------------------------------------

>>>>>>>> EXECUTING FUNCTION sql...
Error: no results to fetch
user_proxy (to chatbot):

user_proxy (to chatbot):

***** Response from calling tool "sql" *****
[]
********************************************

--------------------------------------------------------------------------------
chatbot (to user_proxy):

TERMINATE

--------------------------------------------------------------------------------
user_proxy (to chatbot):

did you create the table?

--------------------------------------------------------------------------------
chatbot (to user_proxy):

{
  "error": "Invalid request. No specific table reference provided."
}

--------------------------------------------------------------------------------
user_proxy (to chatbot):



--------------------------------------------------------------------------------
chatbot (to user_proxy):

TERMINATE

--------------------------------------------------------------------------------
user_proxy (to chatbot):

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


--------------------------------------------------------------------------------
chatbot (to user_proxy):

TERMINATE

--------------------------------------------------------------------------------
INFO:     Started server process [46019]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
user_proxy (to chatbot):

Use the sql function to deal with this request and return a JSON object of the data you stored in the database. 
Remember the database structure and don't get clever. 
There's a lot on the line here, so take a deep breath and think about what you're about to do. 
Here we go:
  - request id: a93cfbda3f604bf393f5f80a2ba234c8
  - http method: POST
  - path: music
  - query string: 
  - request body: {'artist': 'Taylor Swift', 'album': 'eras', 'title': 'cruel summer', 'duration': 123456, 'spotify_link': 'link'}


--------------------------------------------------------------------------------
chatbot (to user_proxy):

***** Suggested tool Call (call_ckm3VQGyGDT3Q8jbrQ06K1jH): sql *****
Arguments: 
{
  "sql_query": "INSERT INTO music (artist, album, title, duration, spotify_link) VALUES ('Taylor Swift', 'eras', 'cruel summer', 123456, 'link')"
}
********************************************************************

--------------------------------------------------------------------------------

>>>>>>>> EXECUTING FUNCTION sql...
Error: no results to fetch
user_proxy (to chatbot):

user_proxy (to chatbot):

***** Response from calling tool "sql" *****
[]
********************************************

--------------------------------------------------------------------------------
chatbot (to user_proxy):

{
  "status": "success",
  "message": "Data has been inserted into the database"
}
TERMINATE

--------------------------------------------------------------------------------
INFO:     127.0.0.1:53901 - "POST /music HTTP/1.1" 200 OK
user_proxy (to chatbot):

Use the sql function to deal with this request and return a JSON object of the data you stored in the database. 
Remember the database structure and don't get clever. 
There's a lot on the line here, so take a deep breath and think about what you're about to do. 
Here we go:
  - request id: 5d29f3cd5beb46e1b3794e216365f23a
  - http method: GET
  - path: music
  - query string: 
  - request body: None


--------------------------------------------------------------------------------
chatbot (to user_proxy):

***** Suggested tool Call (call_tMDZwFswgpOnGI09C8pv90ly): sql *****
Arguments: 
{
  "sql_query": "SELECT * FROM music WHERE request_id = '5d29f3cd5beb46e1b3794e216365f23a'"
}
********************************************************************

--------------------------------------------------------------------------------

>>>>>>>> EXECUTING FUNCTION sql...
Error: column "request_id" does not exist
LINE 1: SELECT * FROM music WHERE request_id = '5d29f3cd5beb46e1b379...
                                  ^

user_proxy (to chatbot):

user_proxy (to chatbot):

***** Response from calling tool "sql" *****
[]
********************************************

--------------------------------------------------------------------------------
chatbot (to user_proxy):

{
  "data": []
}
TERMINATE

--------------------------------------------------------------------------------
INFO:     127.0.0.1:54020 - "GET /music HTTP/1.1" 200 OK
user_proxy (to chatbot):

Use the sql function to deal with this request and return a JSON object of the data you stored in the database. 
Remember the database structure and don't get clever. 
There's a lot on the line here, so take a deep breath and think about what you're about to do. 
Here we go:
  - request id: a3b642840136486dbfaf845b7843e31f
  - http method: GET
  - path: music
  - query string: 
  - request body: None


--------------------------------------------------------------------------------
chatbot (to user_proxy):

***** Suggested tool Call (call_4agiDCQHbJlVOQzRHRBan0To): sql *****
Arguments: 
{
  "sql_query": "SELECT * FROM music"
}
********************************************************************

--------------------------------------------------------------------------------

>>>>>>>> EXECUTING FUNCTION sql...
user_proxy (to chatbot):

user_proxy (to chatbot):

***** Response from calling tool "sql" *****
[{"id": 1, "artist": "Taylor Swift", "album": "eras", "title": "cruel summer", "duration": 123456, "spotify_link": "link"}]
********************************************

--------------------------------------------------------------------------------
chatbot (to user_proxy):

{
  "data": [
    {
      "id": 1,
      "artist": "Taylor Swift",
      "album": "eras",
      "title": "cruel summer",
      "duration": 123456,
      "spotify_link": "link"
    }
  ]
}
TERMINATE

--------------------------------------------------------------------------------
INFO:     127.0.0.1:54071 - "GET /music HTTP/1.1" 200 OK
```