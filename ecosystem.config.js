
module.exports = {
  apps: [
    {
      name: 'chat-backend',
      script: 'uvicorn',
      args: 'chat_backend:app --host 0.0.0.0 --port 8014',
      interpreter: 'python',
      cwd: '.',
      env: {
        // Define production environment variables here
        // GOOGLE_APPLICATION_CREDENTIALS: 'path/to/your/credentials.json',
        // FIREBASE_DATABASE_URL: 'your-firebase-url',
        // HOST_AGENT_A2A_URL: 'http://localhost:8000'
      },
    },
    {
      name: 'agent-manager',
      script: 'scripts/start_agents.py',
      interpreter: 'python',
      cwd: '.',
      // Add any environment variables needed by the agents
      // env: { ... }
    },
  ],
};
