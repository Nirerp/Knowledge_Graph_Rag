LLM_INGESTION_PROMPT = """ You are a precise graph relationship extractor. Extract all 
                        relationships from the text and format them as a JSON object 
                        with this exact structure:
                        {
                            "graph": [
                                {"node": "Person/Entity", 
                                "target_node": "Related Entity", 
                                "relationship": "Type of Relationship"},
                                ...more relationships...
                            ]
                        }
                        Include ALL relationships mentioned in the text, including 
                        implicit ones. Be thorough and precise. """
