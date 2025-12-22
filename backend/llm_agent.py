from pydantic import BaseModel, Field
from typing import Optional, Literal

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# -------------------------
# NoteAction Pydantic Model
# -------------------------
class NoteAction(BaseModel):
    """
    Represents a CRUD-style action on the notes table.
    """

    action: Literal["create", "read", "update", "delete", "list", "help"] = Field(
        ...,
        description="The CRUD action the user wants."
    )

    # How we identify WHICH note to operate on
    note_id: Optional[int] = Field(None, description="Note ID to target")
    target_topic: Optional[str] = Field(
        None,
        description="The CURRENT topic of the note to operate on"
    )

    # New values to assign for create/update
    new_topic: Optional[str] = Field(
        None,
        description="New topic/title for the note"
    )
    new_message: Optional[str] = Field(
        None,
        description="New message/content for the note"
    )

    # For reading or filtering notes
    search_query: Optional[str] = Field(
        None,
        description="Search string for filtering notes"
    )


# -------------------------
# LLM (Ollama) Configuration
# -------------------------
model = ChatOllama(
    model="llama3",
    temperature=0.1,
)

system_instructions = """
You convert a user's natural language into a structured JSON NoteAction.

The NoteAction fields are:

- action: "create", "read", "update", "delete", "list", "help"
- note_id: integer or null
- target_topic: the CURRENT topic of the note we're operating on
- new_topic: the NEW topic to set (for create or update)
- new_message: the NEW message to set (for create or update)
- search_query: text to search for

Rules:

### CREATE
If the user wants to create/add/write a new note:
- action = "create"
- new_topic = the topic they mention
- new_message = the message/content they want

### READ
If the user wants to read/get/show/list notes:
- use action = "list" to show many/all notes
- use action = "read" when looking for a specific one
- fill in note_id or target_topic or search_query

### UPDATE
If the user wants to change/modify/update/edit a note:
- action = "update"
- note_id if they mention "note 3"
- otherwise use target_topic to match the existing topic
- set new_topic if they want to rename the topic
- set new_message if they give new content

EXAMPLES (IMPORTANT):
1. "change the topic assignment to assignment completed"
   -> action="update"
      target_topic="assignment"
      new_topic="assignment completed"

2. "change the topic assignment to assignment completed with message I will do it next month"
   -> action="update"
      target_topic="assignment"
      new_topic="assignment completed"
      new_message="I will do it next month"

### DELETE
If the user wants to delete/remove a note:
- action = "delete"
- note_id or target_topic

### HELP
If the user is confused or asking about usage:
- action = "help"

ALWAYS return ONLY a JSON object matching the NoteAction schema.
No extra text.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_instructions),
        ("human", "{user_input}"),
    ]
)

structured_model = model.with_structured_output(NoteAction)
chain = prompt | structured_model


def parse_user_query(user_input: str) -> NoteAction:
    return chain.invoke({"user_input": user_input})
