from typing import TypedDict



class FlagAttributes(TypedDict):

    name : str
    description : str | None

    color : str
    icon : str | None

    createdAt : str
    updatedAt : str

class FlagRelationships(TypedDict):

    user_id : int
    organization_id : int

class Flag(TypedDict):
    
    id : str
    type : str
    attributes : FlagAttributes
    relationships : FlagRelationships


