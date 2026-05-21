module.exports = {
  apps: [
    {
      name: 'agent-dashboard',
      script: 'agent-server.js',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        USE_SQLITE: 'true',
        LOG_DIR: './logs'
      }
    }
  ]
}
