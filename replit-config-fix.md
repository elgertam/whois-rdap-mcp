# Replit Configuration Fix Required

## Issue
The deployment is failing because the .replit file has incorrect port mapping. The application runs on port 5000 but the external port mapping is configured for port 8000.

## Required Fix in .replit file

The current configuration:
```toml
[[ports]]
localPort = 8000
externalPort = 80
```

Should be changed to:
```toml
[[ports]]
localPort = 5000
externalPort = 80
```

## Current Status
- ✅ Application runs correctly on port 5000
- ✅ Root endpoint (/) returns HTTP 200 with HTML content
- ✅ Health check endpoint (/health) returns HTTP 200 with JSON status
- ✅ Web server binds to 0.0.0.0 for external access
- ❌ Port mapping in .replit needs correction

## Verification
```bash
curl http://localhost:5000/          # Returns HTML page (200 OK)
curl http://localhost:5000/health    # Returns JSON health status (200 OK)
```

Both endpoints are working correctly and ready for deployment once the port mapping is fixed.

## Alternative Solution
If .replit cannot be modified, the deployment system needs to:
1. Map external port 80 to internal port 5000 (not 8000)
2. Ensure the run command uses `python start_servers.py`
3. Wait for port 5000 to be ready before considering deployment successful