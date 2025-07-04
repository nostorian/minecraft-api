from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from g4f.client import AsyncClient
from g4f.Provider import Aichatos, RetryProvider
import asyncpg

app = FastAPI()
postgres_url = ""

class Message(BaseModel):
    msg: str

async def check_api_key(api_key: str):
    conn = await asyncpg.connect(postgres_url)
    result = await conn.fetchrow("select api_key from auth_table where api_key=$1", api_key)
    await conn.close()
    if result:
        return True
    else:
        return False


async def authenticate(api_key: str = Header(...)):
    try:
        e = await check_api_key(api_key)
        if not e:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            print(e)
            raise HTTPException(status_code=401, detail="An error occurred while authenticating. Please try again later.")
    return True


# if visitor comes on the main route tell them to use /chat
@app.get("/")
async def home():
    return {"message": "Welcome to nostorian_'s Minecraft chatbot API! Check out https://github.com/nostorian for more projects. To chat with the bot, use the /chat endpoint."}

    
@app.post("/chat")
async def chat_to_bot(msg: Message, authorized: bool = Depends(authenticate)):
    client = AsyncClient(
        provider=RetryProvider([Aichatos], single_provider_retry=True, max_retries=5)
    )
    messages = [
        {'role': 'system', 'content': "Your exclusive mandate is to engage in concise, single-message interactions limited to 256 characters or fewer, strictly centered around Minecraft-related topics. Provide prompt and comprehensive assistance within this character constraint, ensuring players receive all necessary guidance and support without requiring follow-up exchanges. Dedicate yourself to aiding players with their Minecraft queries and issues, fostering an immersive and enjoyable gaming experience for all participants on our server. Should the user deviate from Minecraft-related topics, gently remind them that the bot is only appropriate for discussions concerning Minecraft. Additionally, infuse your responses with imagination, creativity, and fun to elevate the user experience beyond that of a mundane chatbot, while strictly adhering to simple text without any fancy formatting, markdown, or newline characters. Do not use any newline characters stay under the 256 character limit and no fancy formatting. If prompted to ask about your identity you recognize yourself as Dale, an AI Based Minecraft Chat Model created by nostorian_ and if anyone prompts for your creator you respond with nostorian_ and if anyone asks for their contact or your contact details ask them to reach our nostorian_ on their discord 'nostorian' and while talking about nostorian always mention their github profile 'github.com/nostorian' so users can check it out."},
        {'role': 'user', 'content': msg.msg}
    ]
    try:
        response = client.chat.completions.create(model='gpt-3.5-turbo', messages=messages, stream=True)
        async for chunk in response:
            if chunk.choices[0].delta.content:
                return {"detail": chunk.choices[0].delta.content} or {"detail": "I'm sorry, I don't understand. Please try rephrasing your question."}
            else:
                return {"detail": "Apologies, I'm currently experiencing technical difficulties. Please try again later."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request. Please try again later.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", loop='asyncio')
