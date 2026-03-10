const fs = require("fs");
const path = require("path");

function firstExisting(candidates) {
  for (const candidate of candidates) {
    if (candidate && fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return null;
}

const repoRoot = __dirname;
const repoSlug = path
  .basename(repoRoot)
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, "-")
  .replace(/^-+|-+$/g, "") || "repo";

const pythonBin = process.env.PYTHON_BIN || firstExisting([
  path.join(repoRoot, "venv/bin/python"),
  path.join(repoRoot, "venv314/bin/python"),
  path.join(repoRoot, "venv313/bin/python"),
  path.join(repoRoot, "venv312/bin/python"),
]) || "python3";
const n8nBin = process.env.N8N_BIN || "n8n";
const amazonAgentName = process.env.AMAZON_AGENT_PM2_NAME || `amazon-agent-${repoSlug}`;
const n8nName = process.env.N8N_PM2_NAME || `n8n-server-${repoSlug}`;
const serverPort = process.env.SERVER_PORT || "18080";
const n8nPort = process.env.N8N_PORT || "15678";
const n8nUserFolder = process.env.N8N_USER_FOLDER || path.join(repoRoot, ".n8n");
const pm2Home = process.env.PM2_HOME || path.join(repoRoot, ".pm2");

module.exports = {
  apps: [
    {
      name: amazonAgentName,
      cwd: repoRoot,
      script: pythonBin,
      args: "main.py",
      interpreter: "none",
      autorestart: true,
      max_restarts: 20,
      restart_delay: 3000,
      kill_timeout: 5000,
      listen_timeout: 10000,
      watch: false,
      env: {
        SERVER_PORT: serverPort,
        TZ: "America/Los_Angeles",
        PM2_HOME: pm2Home,
      },
      out_file: path.join(repoRoot, "logs", `pm2-${amazonAgentName}.out.log`),
      error_file: path.join(repoRoot, "logs", `pm2-${amazonAgentName}.err.log`),
      merge_logs: true,
      time: true,
    },
    {
      name: n8nName,
      cwd: repoRoot,
      script: n8nBin,
      args: `start --port ${n8nPort}`,
      interpreter: "none",
      autorestart: true,
      max_restarts: 20,
      restart_delay: 3000,
      kill_timeout: 5000,
      listen_timeout: 15000,
      watch: false,
      env: {
        TZ: "America/Los_Angeles",
        GENERIC_TIMEZONE: "America/Los_Angeles",
        N8N_DEFAULT_TIMEZONE: "America/Los_Angeles",
        N8N_USER_FOLDER: n8nUserFolder,
        QUEUE_HEALTH_CHECK_ACTIVE: "true",
        PM2_HOME: pm2Home,
      },
      out_file: path.join(repoRoot, "logs", `pm2-${n8nName}.out.log`),
      error_file: path.join(repoRoot, "logs", `pm2-${n8nName}.err.log`),
      merge_logs: true,
      time: true,
    },
  ],
};
