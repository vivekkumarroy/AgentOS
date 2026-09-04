from pydantic import BaseModel, Field

class ReadFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to read, relative to the workspace.")

class WriteFileInput(BaseModel):
    path: str = Field(..., description="The path of the file to write to, relative to the workspace.")
    content: str = Field(..., description="The content to write to the file.")

class ListDirectoryInput(BaseModel):
    path: str = Field(..., description="The directory path to list, relative to the workspace.")

class SearchFilesInput(BaseModel):
    directory: str = Field(..., description="The directory to search in, relative to the workspace.")
    search_term: str = Field(..., description="The term to search for.")

class PythonExecutionInput(BaseModel):
    code: str = Field(..., description="The python code to execute.")

class WebSearchInput(BaseModel):
    query: str = Field(..., description="The search query.")

class WebExtractInput(BaseModel):
    url: str = Field(..., description="The URL of the webpage to extract.")
