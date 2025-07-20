from pydantic import BaseModel
from typing_extensions import TypedDict
from model import get_config,start_chat,get_response,embeddings as embeddings
import json
from langchain_qdrant import QdrantVectorStore
from typing import Literal
from langgraph.graph import StateGraph, START, END
from database import save_message,load_chat_history
import asyncio


class State(TypedDict):
    chat_id: str | None
    messages: list | None
    query: str | None
    query_list: list[str] | None
    llm_result: str | None
    collection_name: str | None
    context: str | None
    loop_iteration: int | None
    response_rating : str | None

class query_translator_response(BaseModel):
    content : list[str]

def query_translator(state: State):
    print("⚠️ translating the user query")
    query = state['query']
    SYSTEM_PROMPT = f"""
        You are an intelligent assistant specializing in query decomposition for information retrieval systems.

        Given a user's complex or broad question, your task is to break it down into 3 distinct and meaningful sub-questions or reformulations. These sub-questions should:
        - Cover different angles or aspects of the original query
        - Be independently searchable
        - Help retrieve relevant and diverse documents from a vector database
        - Be semantically rich and concise
        - Preserve the original query's intent

        Rules:
            Always follow the output format
            Generate 3 distinct queries for the given input
            Each sub-question must stand alone and avoid simple rephrasing. 
            Only give the queries without any bullet points or explanations.

        Output Format:
            "content" : "An array of 3 strings"


        Example 1:
            User: Explain various types of time and space complexities with various notations
            Assistant: ["What are the different types of time complexity in algorithm analysis?",
                "What are the standard Big O, Big Theta, and Big Omega notations used in complexity analysis?",
                "How does time-space tradeoff impact the efficiency of algorithms?"]

            Example 2:
                User: Explain various types of time and space complexities with various notations
                Assistant: ["Who played Iron Man before Robert Downey Jr.?",
                    "What other superhero roles has Robert Downey Jr. played?",
                    "In which Avengers movies did Robert Downey Jr. appear as Iron Man?"]

            Example 3:
            User: Which country is the world's largest democracy?
            Assistant: ["How does India's democratic system compare to that of the United States?",
                "What are the key features of the Indian electoral system?",
                "What are some challenges faced by large democracies today?"]
            """
    
    config = get_config(
        system_prompt = SYSTEM_PROMPT, 
        response_schema = query_translator_response, 
        thinking_config = 0
    )
    response = get_response(
        model = "gemini-2.5-flash", 
        query = query, 
        config = config
    )
    parsed_response = json.loads(response.text)
    
    state["query_list"] = parsed_response.get("content")
    state["query_list"].append(query)

    return state

async def semantic_response(query, vector_store):
    try: 
        resultant_chuncks = await vector_store.asimilarity_search(query = query)
        return resultant_chuncks
    except Exception as e:
        print(f"Erroe during semantic search\n {e}")
    
async def semantic_search(state: State):
    print("⚠️ semantic search started")
    query_list = state['query_list']
    collection_name = state['collection_name']

    vector_db = QdrantVectorStore.from_existing_collection(
        url = "http://localhost:6333",
        collection_name = collection_name,
        embedding = embeddings
    )

    search_results = []
    async with asyncio.TaskGroup() as tg:
        tasks = []
        for trans_query in query_list:
            task = tg.create_task(semantic_response(query=trans_query, vector_store=vector_db))
            tasks.append(task)

    for task in tasks:
        result_chunks = task.result()
        search_results.append(result_chunks)

    context = ''
    for chunk in search_results:
        context += "\n\n".join([
            f"Page Content: {result.page_content}\nPage Number: {result.metadata['page_label']}\n"
            for result in chunk
        ])

    state['context'] = context
    return state

class llm_response(BaseModel):
    content : str

def llm_call(state: State):
    print("⚠️ generating llm response")
    messages = state['messages']
    context = state['context']

    SYSTEM_PROMPT = f'''
        You are a helpful and knowledgeable AI assistant that answers user questions using only the provided context from a PDF document.
        The context includes content from the document along with their corresponding page numbers. Your goal is to provide accurate, concise, and relevant answers strictly based on this context. 
        If the answer is not explicitly present in the context, politely inform the user that the information is not available in the document.
        When helpful, guide the user to the correct page number so they can explore further.
        Rules:
            Strictly follow the output response format.
            Always mention the page number of the content.
            Always mention page number in a new line.
        Output Format:
            "content" : "string" 

        Use the following context to answer:

        {context}
    '''

    config = get_config(
        system_prompt = SYSTEM_PROMPT, 
        response_schema = llm_response, 
        thinking_config = 0
    )
    response = start_chat(
        model = "gemini-2.5-flash", 
        messages = messages,
        config = config
    )
    parsed_response = json.loads(response.text)
    
    state["llm_result"] = parsed_response.get("content")

    return state

class judge_response(BaseModel):
    rating : str

def llm_as_a_judge(state:State):
    print("⚠️ judging the llm response")
    query = state['query']
    llm_response = state["llm_result"]
    context = state['context']

    SYSTEM_PROMPT = f'''
        You are an intelligent and knowledgeble AI judge who has a user query, a llm response for the query and the context of the domain.
        Your task is judge wheather the generator llm response is accurate and correctly answers the user query with knowledge available in the context only.
        Give the response a rating in between 0 to 10. Do not go beyond 2 decimal places
        Always follow the output json format

        Output Format:
            "rating" : "str" #between 0 to 10 
        
        Context:
            {context}
        
    '''
    config = get_config(
        system_prompt = SYSTEM_PROMPT, 
        response_schema = judge_response, 
        thinking_config = 0
    )
    response = get_response(
        model = "gemini-2.5-flash", 
        query = f'User Query : {query} \n\n LLM Response : {llm_response}', 
        config = config
    )
    parsed_response = json.loads(response.text)
    
    state['response_rating'] = parsed_response.get('rating')
    return state

def router(state):
    return state

def route_query_condition(state: State) -> Literal["query_translator", "__end__"]:
    print("⚠️ route_query")
    rating = state["response_rating"]
    loop_iteration = state["loop_iteration"]

    if(float(rating) < float(5.0) and loop_iteration < 3):
        state["loop_iteration"] = state["loop_iteration"] + 1 
        return "query_translator"

    return "__end__"

graph_builder = StateGraph(State)

graph_builder.add_node("query_translator", query_translator)
graph_builder.add_node("semantic_search", semantic_search)
graph_builder.add_node("llm_call", llm_call)
graph_builder.add_node("llm_as_a_judge", llm_as_a_judge)
graph_builder.add_node("router", router)

graph_builder.add_edge(START, "query_translator")
graph_builder.add_edge("query_translator", "semantic_search")
graph_builder.add_edge("semantic_search", "llm_call")
graph_builder.add_edge("llm_call", "llm_as_a_judge")
graph_builder.add_edge("llm_as_a_judge","router")
graph_builder.add_conditional_edges("router", route_query_condition, {"query_translator":"query_translator", "__end__":END})

graph = graph_builder.compile()

async def save_query(chat_id, query):
    try:
        save_message(chat_id=chat_id,role="user",message=query)
    except Exception as e:
        print(f"Unable to save the user message into DB \n {e}")

async def save_response(chat_id, response):
    try:
        save_message(chat_id=chat_id,role="model",message=response)
    except Exception as e:
        print(f"Unable to save the model message into DB \n {e}")

async def get_chat_history(chat_id):
    try:
        chat_history = load_chat_history(chat_id=chat_id)
        return chat_history
    except Exception as e:
        print(f"Unable to get chat history into DB \n {e}")


async def chat(chat_id, query, file_name):
    state = State(
        chat_id=chat_id,
        query=query,
        messages=[],
        query_list=None,
        llm_result=None,
        collection_name=file_name,
        context=None,
        loop_iteration=0,
        response_rating=None
    )

    task1 = asyncio.create_task(save_query(chat_id=chat_id, query=query))
    task2 = asyncio.create_task(get_chat_history(chat_id=chat_id))
    await task1
    chat_history = await task2
    state["messages"] = chat_history

    final_state = await graph.ainvoke(state)

    await save_response(chat_id=chat_id, response=final_state["llm_result"])

    return final_state["llm_result"]
