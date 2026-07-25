# RDI Web Generator

A web-based user interface for the Chrono Trigger Randomizer (ctrando) project. This repository provides a Django-powered frontend that allows users to interact with the Rando-Dalton Imperial randomizer through their browser and provides some basic information and resources for players.

- [RDI home page and web generator](https://ctrando.com)
- [CTRando (RDI) repository](https://github.com/pseudoarc/ctrando)
- [RDI Discord](https://discord.gg/VpYtzMSGRa)

## Project Structure

This repository contains several key directories:

- **ctrando** (submodule) - The main Rando-Dalton Imperial randomizer for Chrono Trigger. This is the core randomization logic and backend API that this web interface connects to.
  
- **Flips** (submodule) - A utility tool for generating patch files, used during the randomization workflow.

- **deploy** - Docker configurations and deployment scripts for running the site in a containerized environment.

- **tools** - Additional utilities and helper scripts for generating site pages, form controls, and randomizer assets.

## Running the Site

This project uses Docker for deployment. See the [deploy](../deploy) directory for container configurations and instructions.

## License

This project is licensed under the same terms as the main ctrando repository. See the LICENSE file for details.
