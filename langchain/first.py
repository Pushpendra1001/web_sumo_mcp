from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
 
class Joke(BaseModel):
    question: str = Field(description="question to setup the joke")
    answer:str =Field(description="answer to resolve the joke")
 
parser = JsonOutputParser(pydantic_object=Joke)
 
prompt = PromptTemplate(
    template="Answer the user query. \n{query},\n{format_instructions}",
    input_variables=["query"],
    partial_variables={"format_instructions":parser.get_format_instructions()}
)
 
chain = prompt | llm_model | parser
res = chain.invoke({"query":"tell me a joke"})
print(res)