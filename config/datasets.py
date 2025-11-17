from pydantic import BaseModel, Field

class Single(BaseModel):
    """Represents a single graph relationship between two nodes."""
    node: str = Field(description="The node of the graph relationship.")
    relationship: str = Field(description="The relationship between the node and the target node.")
    target_node: str = Field(description="The target node of the graph relationship.")
    
    

class GraphComponents(BaseModel):
    """Container for a list of graph relationships."""
    graph: list[Single]


if __name__ == "__main__":
    print(GraphComponents.model_json_schema())