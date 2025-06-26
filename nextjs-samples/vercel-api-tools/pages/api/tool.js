export default async function handler(req, res) {
  // Example: receive a tool call, trigger backend logic
  if (req.method === 'POST') {
    const { action, payload } = req.body;
    // Simulate action routing
    if (action === 'openai') {
      // Call OpenAI or other backend logic here
      res.status(200).json({ result: `OpenAI handled: ${payload}` });
    } else if (action === 'webhook') {
      // Simulate webhook
      res.status(200).json({ result: `Webhook triggered with: ${payload}` });
    } else {
      res.status(400).json({ error: 'Unknown action' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
} 