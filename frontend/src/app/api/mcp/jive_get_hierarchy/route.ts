import { NextRequest, NextResponse } from 'next/server';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:3454';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Extract X-Namespace header from the request
    const namespace = request.headers.get('X-Namespace');
    
    // Prepare headers for MCP server request
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Forward X-Namespace header if present
    if (namespace) {
      headers['X-Namespace'] = namespace;
    }
    
    // Forward the request to the MCP server
    const response = await fetch(`${MCP_SERVER_URL}/tools/execute`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        tool_name: 'jive_get_hierarchy',
        parameters: body
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
        data: data.result
      });
    } else {
      return NextResponse.json({
        success: false,
        error: data.error || 'Unknown error occurred'
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Error in jive_get_hierarchy API route:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error'
    }, { status: 500 });
  }
}