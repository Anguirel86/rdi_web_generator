# Deployment Configuration

This directory contains the Docker configuration files used to deploy the RDI web generator service. It supports both development and production environments.

## Files

- **`Dockerfile`** — Multi-stage build that installs dependencies, copies the application code, and sets up a non-root user for running the web server.
- **`entrypoint.sh`** — Startup script executed when the container launches; it runs the tool scripts to regenerate forms and presets and handles the Django database migration scripts and static file collection.
- **`docker-compose.dev.yml`** — Development compose file: runs the web app in Django's development server on port 8000.
- **`docker-compose.prod.yml`** — Production compose file: uses Gunicorn behind an Nginx proxy with Let's Encrypt integration via the `jrcs/letsencrypt-nginx-proxy-companion` image. Includes volume mounts for static files, certificates, and ACME configuration.
- **`env.dev`** — Development environment variables (DEBUG=1, permissive host settings).
- **`env.prod`** — Production environment variables (DEBUG=0, required `SECRET_KEY`, allowed hosts set to the production domain).
- **`env.prod.letsencrypt`** — Additional production env vars for Let's Encrypt ACME URI and proxy configuration.

## Usage

### Development

```bash
# From the project root directory
docker compose -f deploy/docker-compose.dev.yml up --build
```

The development configuration will spin up a container and run the site using the built-in Django test server. This allows for local testing but should not be used for production.

### Production

1. Set the `SECRET_KEY` variable in `env.prod` and set an email in `env.prod.letsencrypt`. The default host information is set up for `ctrando.com`, so change this if necessary.
2. Run with production compose:
   ```bash
   # From the project root directory
   docker compose -f deploy/docker-compose.prod.yml up --build -d
   ```

The production configuration spins up the full production suite of containers with Gunicorn and an Nginx proxy. The Nginx proxy will handle TLS termination and forward requests to the Gunicorn worker process inside the container.

## Notes

- The `entrypoint.sh` script automatically regenerates the TOML generator form HTML, preset buttons, and prepatches the ROM on startup. This ensures that deployed containers always have up-to-date assets even if the randomizer code changes.
