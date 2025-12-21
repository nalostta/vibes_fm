const express = require('express');
const cors = require('cors');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const app = express();
const PORT = process.env.DASHBOARD_PORT || 7331;
const COMPOSE_PROJECT = process.env.COMPOSE_PROJECT_NAME || 'vibes_fm';
const WORKSPACE_PATH = process.env.WORKSPACE_PATH || '/workspace';

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

function loadModulesConfig() {
  try {
    const configPath = process.env.MODULES_CONFIG || path.join(__dirname, '../modules.json');
    const data = fs.readFileSync(configPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading modules config:', error.message);
    return { modules: [] };
  }
}

function execDockerCompose(args) {
  try {
    const composeFile = path.join(WORKSPACE_PATH, 'docker-compose.yml');
    const cmd = `docker compose -f ${composeFile} -p ${COMPOSE_PROJECT} ${args}`;
    const result = execSync(cmd, { encoding: 'utf8', timeout: 30000 });
    return { success: true, output: result };
  } catch (error) {
    return { success: false, error: error.message, output: error.stdout || '' };
  }
}

function getContainerStatus(serviceName) {
  try {
    const result = execDockerCompose(`ps --format json ${serviceName}`);
    if (result.success && result.output.trim()) {
      const lines = result.output.trim().split('\n');
      for (const line of lines) {
        try {
          const container = JSON.parse(line);
          if (container.Service === serviceName || container.Name?.includes(serviceName)) {
            const state = container.State || 'unknown';
            const health = container.Health || 'unknown';
            return {
              running: state === 'running',
              state: state,
              health: health,
              name: container.Name,
              ports: container.Ports || ''
            };
          }
        } catch (e) {
          continue;
        }
      }
    }
    return { running: false, state: 'stopped', health: 'unknown', name: '', ports: '' };
  } catch (error) {
    return { running: false, state: 'error', health: 'unknown', error: error.message };
  }
}

async function checkHttpHealth(url, timeout = 5000) {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: urlObj.pathname,
      method: 'GET',
      timeout: timeout
    };

    const req = http.request(options, (res) => {
      resolve({
        healthy: res.statusCode >= 200 && res.statusCode < 400,
        statusCode: res.statusCode,
        lastCheck: new Date().toISOString()
      });
    });

    req.on('error', () => {
      resolve({
        healthy: false,
        statusCode: null,
        lastCheck: new Date().toISOString()
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        healthy: false,
        statusCode: null,
        lastCheck: new Date().toISOString()
      });
    });

    req.end();
  });
}

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/modules', async (req, res) => {
  try {
    const config = loadModulesConfig();
    const modules = await Promise.all(config.modules.map(async (module) => {
      const containerStatus = getContainerStatus(module.service);
      let healthStatus = { healthy: false, statusCode: null, lastCheck: null };
      
      if (module.healthCheck?.enabled && containerStatus.running) {
        healthStatus = await checkHttpHealth(module.healthCheck.url);
      }

      const moduleType = module.type || 'service';
      let status = 'stopped';
      if (moduleType === 'job') {
        status = containerStatus.running ? 'running' : (containerStatus.state === 'exited' ? 'completed' : 'idle');
      } else {
        status = containerStatus.running ? 'running' : 'stopped';
      }

      return {
        name: module.name,
        displayName: module.displayName,
        description: module.description,
        service: module.service,
        type: moduleType,
        category: module.category || 'Uncategorized',
        status: status,
        containerState: containerStatus.state,
        containerHealth: containerStatus.health,
        containerName: containerStatus.name,
        ports: module.ports,
        health: {
          enabled: module.healthCheck?.enabled || false,
          url: module.healthCheck?.url || null,
          ...healthStatus
        }
      };
    }));

    res.json({ modules, timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/modules/:name/status', async (req, res) => {
  try {
    const { name } = req.params;
    const config = loadModulesConfig();
    const module = config.modules.find(m => m.name === name);

    if (!module) {
      return res.status(404).json({ error: `Module '${name}' not found` });
    }

    const containerStatus = getContainerStatus(module.service);
    let healthStatus = { healthy: false, statusCode: null, lastCheck: null };

    if (module.healthCheck?.enabled && containerStatus.running) {
      healthStatus = await checkHttpHealth(module.healthCheck.url);
    }

    const moduleType = module.type || 'service';
    let status = 'stopped';
    if (moduleType === 'job') {
      status = containerStatus.running ? 'running' : (containerStatus.state === 'exited' ? 'completed' : 'idle');
    } else {
      status = containerStatus.running ? 'running' : 'stopped';
    }

    res.json({
      name: module.name,
      displayName: module.displayName,
      description: module.description,
      service: module.service,
      type: moduleType,
      category: module.category || 'Uncategorized',
      status: status,
      containerState: containerStatus.state,
      containerHealth: containerStatus.health,
      containerName: containerStatus.name,
      ports: module.ports,
      health: {
        enabled: module.healthCheck?.enabled || false,
        url: module.healthCheck?.url || null,
        ...healthStatus
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/modules/:name/start', (req, res) => {
  try {
    const { name } = req.params;
    const config = loadModulesConfig();
    const module = config.modules.find(m => m.name === name);

    if (!module) {
      return res.status(404).json({ error: `Module '${name}' not found` });
    }

    if (module.name === 'dashboard') {
      return res.json({ 
        success: true, 
        message: 'Dashboard is already running',
        service: module.service 
      });
    }

    const result = execDockerCompose(`up -d ${module.service}`);
    
    if (result.success) {
      res.json({ 
        success: true, 
        message: `Module '${name}' started`,
        service: module.service,
        output: result.output
      });
    } else {
      res.status(500).json({ 
        success: false, 
        error: result.error,
        output: result.output
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/modules/:name/stop', (req, res) => {
  try {
    const { name } = req.params;
    const config = loadModulesConfig();
    const module = config.modules.find(m => m.name === name);

    if (!module) {
      return res.status(404).json({ error: `Module '${name}' not found` });
    }

    if (module.name === 'dashboard') {
      return res.status(400).json({ 
        success: false, 
        error: 'Cannot stop the dashboard from itself'
      });
    }

    const result = execDockerCompose(`stop ${module.service}`);
    
    if (result.success) {
      res.json({ 
        success: true, 
        message: `Module '${name}' stopped`,
        service: module.service,
        output: result.output
      });
    } else {
      res.status(500).json({ 
        success: false, 
        error: result.error,
        output: result.output
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/modules/:name/restart', (req, res) => {
  try {
    const { name } = req.params;
    const config = loadModulesConfig();
    const module = config.modules.find(m => m.name === name);

    if (!module) {
      return res.status(404).json({ error: `Module '${name}' not found` });
    }

    if (module.name === 'dashboard') {
      return res.status(400).json({ 
        success: false, 
        error: 'Cannot restart the dashboard from itself'
      });
    }

    const result = execDockerCompose(`restart ${module.service}`);
    
    if (result.success) {
      res.json({ 
        success: true, 
        message: `Module '${name}' restarted`,
        service: module.service,
        output: result.output
      });
    } else {
      res.status(500).json({ 
        success: false, 
        error: result.error,
        output: result.output
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/modules/:name/logs', (req, res) => {
  const { name } = req.params;
  const config = loadModulesConfig();
  const module = config.modules.find(m => m.name === name);

  if (!module) {
    return res.status(404).json({ error: `Module '${name}' not found` });
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  res.write(`data: ${JSON.stringify({ type: 'connected', module: name })}\n\n`);

  const composeFile = path.join(WORKSPACE_PATH, 'docker-compose.yml');
  const logProcess = spawn('docker', [
    'compose', '-f', composeFile, '-p', COMPOSE_PROJECT,
    'logs', '-f', '--tail=100', module.service
  ]);

  logProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(line => {
      res.write(`data: ${JSON.stringify({ type: 'log', content: line })}\n\n`);
    });
  });

  logProcess.stderr.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(line => {
      res.write(`data: ${JSON.stringify({ type: 'log', content: line })}\n\n`);
    });
  });

  logProcess.on('error', (error) => {
    res.write(`data: ${JSON.stringify({ type: 'error', content: error.message })}\n\n`);
  });

  logProcess.on('close', (code) => {
    res.write(`data: ${JSON.stringify({ type: 'closed', code: code })}\n\n`);
    res.end();
  });

  req.on('close', () => {
    logProcess.kill('SIGTERM');
  });
});

app.get('/api/tests', (req, res) => {
  const servicesPath = path.join(WORKSPACE_PATH, 'services');
  try {
    const services = fs.readdirSync(servicesPath, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => {
        const testsPath = path.join(servicesPath, dirent.name, 'tests');
        let testFiles = [];
        try {
          testFiles = fs.readdirSync(testsPath)
            .filter(f => f.startsWith('test_') && f.endsWith('.py'));
        } catch (e) {}
        return {
          name: dirent.name,
          displayName: dirent.name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
          testPath: `services/${dirent.name}/tests`,
          testFiles: testFiles,
          testCount: testFiles.length
        };
      });
    res.json({ services, timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/tests/run', (req, res) => {
  const { service } = req.query;
  
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  const testTarget = service ? `services/${service}/tests` : 'services';
  const displayName = service || 'all services';
  
  res.write(`data: ${JSON.stringify({ type: 'started', target: displayName })}\n\n`);

  const testProcess = spawn('docker', [
    'run', '--rm',
    '-v', `${WORKSPACE_PATH}:/app`,
    '-w', '/app',
    'python:3.11-slim',
    'sh', '-c',
    `pip install -q pytest pytest-asyncio sqlalchemy psycopg2-binary pydantic pydantic-settings python-jose passlib httpx redis && python -m pytest ${testTarget} -v --tb=short 2>&1`
  ]);

  testProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(line => {
      let type = 'output';
      if (line.includes('PASSED')) type = 'passed';
      else if (line.includes('FAILED')) type = 'failed';
      else if (line.includes('ERROR')) type = 'error';
      else if (line.includes('SKIPPED')) type = 'skipped';
      res.write(`data: ${JSON.stringify({ type, content: line })}\n\n`);
    });
  });

  testProcess.stderr.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    lines.forEach(line => {
      res.write(`data: ${JSON.stringify({ type: 'output', content: line })}\n\n`);
    });
  });

  testProcess.on('error', (error) => {
    res.write(`data: ${JSON.stringify({ type: 'error', content: error.message })}\n\n`);
  });

  testProcess.on('close', (code) => {
    res.write(`data: ${JSON.stringify({ type: 'completed', code: code, success: code === 0 })}\n\n`);
    res.end();
  });

  req.on('close', () => {
    testProcess.kill('SIGTERM');
  });
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Dashboard server running on http://0.0.0.0:${PORT}`);
  console.log(`Compose project: ${COMPOSE_PROJECT}`);
  console.log(`Workspace path: ${WORKSPACE_PATH}`);
});
