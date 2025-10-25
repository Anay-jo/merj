const fs = require('fs');
const path = require('path');
const os = require('os');
const { Octokit } = require('@octokit/rest');

// Path to config file in user's home directory
const CONFIG_FILE = path.join(os.homedir(), '.merjrc');

/**
 * Get stored GitHub token from config file
 */
function getStoredToken() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
      return config.github?.token || null;
    }
  } catch (error) {
    console.error('Error reading config file:', error.message);
  }
  return null;
}

/**
 * Store GitHub token in config file
 */
function storeToken(token) {
  try {
    const config = {
      github: {
        token: token
      }
    };
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
    // Set restrictive permissions (read/write for owner only)
    fs.chmodSync(CONFIG_FILE, 0o600);
    return true;
  } catch (error) {
    console.error('Error storing token:', error.message);
    return false;
  }
}

/**
 * Initialize authenticated GitHub client
 */
function getAuthenticatedClient() {
  const token = getStoredToken();
  
  if (!token) {
    return null;
  }
  
  return new Octokit({
    auth: token
  });
}

/**
 * Test authentication by making a simple API call
 */
async function testAuthentication() {
  const octokit = getAuthenticatedClient();
  
  if (!octokit) {
    return { authenticated: false, error: 'No token found' };
  }
  
  try {
    const { data } = await octokit.rest.users.getAuthenticated();
    return { 
      authenticated: true, 
      username: data.login,
      user: data
    };
  } catch (error) {
    return { 
      authenticated: false, 
      error: error.message 
    };
  }
}

module.exports = {
  getStoredToken,
  storeToken,
  getAuthenticatedClient,
  testAuthentication,
  CONFIG_FILE
};

