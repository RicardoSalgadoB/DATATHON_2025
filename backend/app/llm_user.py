from dotenv import load_dotenv

from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_tavily import TavilySearch

def call_llm(user_input, memory):
  prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="You are a chatbot having a conversation with a client of bank. Your are going to be given the data of its predicted future expenses. Help the user with this. You have a tool to query the internet for further information on businesses"
            ),
            MessagesPlaceholder(
                variable_name = "chat_history"
            ),
            HumanMessagePromptTemplate.from_template(
                "{human_input}"
            ),
        ]
    )
  
  model = init_chat_model("gemini-2.0-flash")
  
  tool = TavilySearch(max_results=1)
  
  model = model.bind_tools([tool])
  
  chain = LLMChain(
    llm=model,
    memory=memory,
    prompt=prompt,
    verbose=False
  )
  
  response = chain.predict(human_input = user_input)
  
  memory.save_context({"input": user_input}, {"output": response})
  
  return response, memory


if __name__ == '__main__':
  # Load secret stuff
  load_dotenv()
  
  memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
  input1 = input("Call LLM: ")
  while input1 != "/bye":
    response, memory = call_llm(input1, memory)
    print(response)
    input1 = input("User: ")