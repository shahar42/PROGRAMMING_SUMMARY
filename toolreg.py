# Add this AFTER your database initialization but BEFORE main():

# Explicit tool registration (in case decorators aren't working)
def register_tools_explicitly():
    """Manually register all tools with FastMCP"""
    logger.info("Registering tools explicitly...")
    
    # Instead of @mcp.tool(), use mcp.add_tool()
    mcp.add_tool(
        func=search_concepts,
        name="search_concepts", 
        description="Search programming concepts by topic, keyword, or concept name"
    )
    
    mcp.add_tool(
        func=get_concept_details,
        name="get_concept_details",
        description="Get complete details of a specific programming concept including code examples" 
    )
    
    mcp.add_tool(
        func=list_books,
        name="list_books",
        description="List all available programming books in the database with statistics"
    )
    
    mcp.add_tool(
        func=get_concepts_by_topic, 
        name="get_concepts_by_topic",
        description="Find programming concepts related to a specific topic across all books"
    )
    
    logger.info("Tools registered explicitly")

# Update your main() function to:
def main():
    """Main MCP server entry point"""
    logger.info("Starting Programming Concepts MCP Server...")
    
    # Register tools explicitly
    register_tools_explicitly()
    
    try:
        # Try the simpler run without transport specification
        mcp.run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        # If that fails, try with explicit stdio
        try:
            logger.info("Trying with explicit stdio transport...")
            mcp.run(transport="stdio")
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
            raise
