import { NextRequest, NextResponse } from 'next/server';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:3454';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Extract parameters from the request body
    const parameters = body.parameters || body;
    
    // Forward the request to the MCP server
    const response = await fetch(`${MCP_SERVER_URL}/tools/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tool_name: 'jive_search_content',
        parameters: parameters
      })
    });

    if (!response.ok) {
      throw new Error(`MCP server responded with status: ${response.status}`);
    }

    const data = await response.json();
    
    // Return the result in the expected format
    if (data.success) {
      return NextResponse.json({
        success: true,
        result: data.result
      });
    } else {
      return NextResponse.json({
        success: false,
        error: data.error || 'Unknown error occurred'
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Error in jive_search_content API route:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error'
    }, { status: 500 });
  }
}