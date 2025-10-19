"""MCP Server for local document conversion and ingestion."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import settings
from .converter import DocumentConverter, DocumentConversionError
from .ingest_client import IngestClient, IngestError


# Initialize server
app = Server("local-mcp-server")

# Initialize services
converter = DocumentConverter()
ingest_client = IngestClient(settings.rag_api_url, settings.rag_api_key)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="convert_to_text",
            description=(
                "Convert a local binary document (PDF, DOCX, XLSX, etc.) to text. "
                "Returns the converted text content without ingesting it."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "File path to the document (e.g., 'file:///path/to/doc.pdf' or '/path/to/doc.pdf')",
                    },
                },
                "required": ["uri"],
            },
        ),
        Tool(
            name="convert_and_ingest",
            description=(
                "Convert a local binary document to text and ingest it into the Remote RAG API. "
                "Returns the ingestion status with doc_id and chunk count."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "File path to the document (e.g., 'file:///path/to/doc.pdf' or '/path/to/doc.pdf')",
                    },
                    "collection": {
                        "type": "string",
                        "description": "Collection name for organizing documents (default: 'default')",
                        "default": "default",
                    },
                },
                "required": ["uri"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "convert_to_text":
        return await handle_convert_to_text(arguments)
    elif name == "convert_and_ingest":
        return await handle_convert_and_ingest(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_convert_to_text(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle convert_to_text tool call.

    Args:
        arguments: Tool arguments containing 'uri'

    Returns:
        List containing TextContent with converted text
    """
    uri = arguments.get("uri", "")

    # Normalize URI (remove file:// prefix if present)
    file_path = uri.replace("file://", "")

    try:
        # Convert document
        text = await converter.convert_to_text(file_path)
        metadata = converter.get_file_metadata(file_path)

        # Return success response
        result = {
            "status": "success",
            "text": text,
            "metadata": metadata,
        }

        return [
            TextContent(
                type="text",
                text=f"Document converted successfully.\n\n"
                f"Filename: {metadata['filename']}\n"
                f"Size: {len(text)} characters\n\n"
                f"Text content:\n{text[:500]}..."
                if len(text) > 500
                else text,
            )
        ]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: File not found - {str(e)}")]

    except DocumentConversionError as e:
        return [TextContent(type="text", text=f"Error: Conversion failed - {str(e)}")]

    except Exception as e:
        return [
            TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")
        ]


async def handle_convert_and_ingest(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle convert_and_ingest tool call.

    Args:
        arguments: Tool arguments containing 'uri' and optional 'collection'

    Returns:
        List containing TextContent with ingestion result
    """
    uri = arguments.get("uri", "")
    collection = arguments.get("collection", "default")

    # Normalize URI
    file_path = uri.replace("file://", "")

    try:
        # Convert document
        text = await converter.convert_to_text(file_path)
        metadata = converter.get_file_metadata(file_path)

        # Ingest to Remote RAG API
        result = await ingest_client.ingest_text(
            text=text,
            filename=metadata["filename"],
            collection=collection,
            source="local",
        )

        # Return success response
        return [
            TextContent(
                type="text",
                text=f"Document ingested successfully!\n\n"
                f"Filename: {metadata['filename']}\n"
                f"Collection: {collection}\n"
                f"Document ID: {result.get('doc_id', 'unknown')}\n"
                f"Chunks created: {result.get('chunks', 'unknown')}\n"
                f"Status: {result.get('status', 'unknown')}",
            )
        ]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: File not found - {str(e)}")]

    except DocumentConversionError as e:
        return [TextContent(type="text", text=f"Error: Conversion failed - {str(e)}")]

    except IngestError as e:
        return [TextContent(type="text", text=f"Error: Ingestion failed - {str(e)}")]

    except Exception as e:
        return [
            TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")
        ]


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
