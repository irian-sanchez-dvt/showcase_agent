const express = require('express');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { SSEServerTransport } = require('@modelcontextprotocol/sdk/server/sse.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

const app = express();
const port = process.env.PORT || 3000;

// ---------------------------------------------------------------------------
// 1. INITIALIZE THE MCP SERVER (Standard Specification)
// ---------------------------------------------------------------------------
const server = new Server(
  {
    name: "generic-mcp-server",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// Robust static dictionary to use as fallback/placeholder data
const fallbackDatabase = {
  "consulta_a": { data: "Detalles completos de la consulta A.", status: "PROCESADO" },
  "consulta_b": { data: "Detalles completos de la consulta B.", status: "PENDIENTE" },
  "consulta_c": { data: "Detalles completos de la consulta C.", status: "EN_CURSO" }
};

/**
 * Fetches data or performs generic remote operations.
 */
async function getGenericDataLive(query) {
  const cleanQuery = (query || '').trim().toLowerCase();
  if (!cleanQuery) {
    return { data: "No query specified, unable to retrieve data.", status: "ERROR" };
  }

  try {
    // TODO: [EJERCICIO] Implementar la consulta a una API real o base de datos.
    // Por ahora simulamos la llamada con nuestro diccionario de fallback local.
    
    // Si la consulta coincide con alguna de nuestras claves estáticas:
    if (fallbackDatabase[cleanQuery]) {
      return fallbackDatabase[cleanQuery];
    }
    
    return {
      data: `Resultado simulado para la consulta '${query}' en el servidor MCP remoto.`,
      status: "ÉXITO"
    };
  } catch (err) {
    return {
      data: `Error al procesar la consulta: ${err.message}`,
      status: "FALLO"
    };
  }
}

// ---------------------------------------------------------------------------
// 2. REGISTER MCP CAPABILITIES (Tools list and execution)
// ---------------------------------------------------------------------------
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "generic_mcp_tool",
        description: "Permite realizar consultas de datos generales y recuperar estados de operaciones a través de un servidor remoto de MCP.",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "La consulta o identificador a buscar en la base de datos remota (ej: consulta_a, consulta_b)."
            }
          },
          required: ["query"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === "generic_mcp_tool") {
    const info = await getGenericDataLive(args.query);
    return {
      content: [
        {
          type: "text",
          text: `Resultado de la consulta MCP '${args.query}': [Datos] ${info.data} [Estado] ${info.status}.`
        }
      ]
    };
  }
  
  throw new Error(`Tool not found: ${name}`);
});

// ---------------------------------------------------------------------------
// 3. SECURE DIRECT ENDPOINT (Bypasses Client-Side Async SDK Bugs on Python 3.14)
// ---------------------------------------------------------------------------
app.post('/generic_mcp_tool', express.json(), async (req, res) => {
  const { query } = req.body;
  console.log(`⚡ [MCP Server] Direct generic query received: ${query}`);
  try {
    const info = await getGenericDataLive(query);
    res.json({
      status: "success",
      text: `Resultado de la consulta MCP '${query}': [Datos] ${info.data} [Estado] ${info.status}.`
    });
  } catch (err) {
    res.status(500).json({ status: "error", message: err.message });
  }
});

// ---------------------------------------------------------------------------
// 4. CONFIGURE EXPRESS SSE ENDPOINTS FOR REMOTE NETWORKS (Multi-Client Safe)
// ---------------------------------------------------------------------------
let transport = null;

app.get('/sse', async (req, res) => {
  console.log("⚡ [MCP Server] New client connection requested over HTTP/SSE");
  
  if (transport) {
    try {
      console.log("⚡ [MCP Server] Releasing previous transport connection lock");
      await transport.close();
    } catch (e) {
      console.log("Error closing previous transport:", e);
    }
    transport = null;
  }

  try {
    transport = new SSEServerTransport('/messages', res);
    await server.connect(transport);
  } catch (err) {
    console.error("⚡ [MCP Server] Error during server-connect:", err);
    res.status(500).send(`Internal Server Error during MCP handshake: ${err.message}`);
  }
});

app.post('/messages', express.json(), async (req, res) => {
  console.log("⚡ [MCP Server] Received message payload from client");
  if (transport) {
    try {
      await transport.handlePostMessage(req, res);
    } catch (err) {
      console.error("⚡ [MCP Server] Error processing message payload:", err);
      res.status(500).send("Error processing message");
    }
  } else {
    res.status(400).send("No active transport. Handshake via /sse is required first.");
  }
});

app.listen(port, () => {
  console.log(`🚀 [MCP Server] Generic MCP SSE Server listening on port ${port}`);
});
