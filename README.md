# Decentralised Discovery Gateway

Decentralised Discovery Gateway for proxying requests in a decentralised network in a discovery context.

## Features

- **Decentralised**: Operates in a peer-to-peer network, allowing the discovery of data without a central authority.
- **Proxying**: Acts as a proxy for requests, enabling efficient data retrieval and interaction with decentralised services, if the nodes cannot connect directly.
- **Discovery Context**: Designed specifically for data discovery, which handles sensitive data in a secure and private manner, without the burden of centralised servers.

## Installation

The recommended way to install in production is to use the pre-built Docker image.

## Configuration and usage

This software is designed as a proxy system, where it accepts a query or request, distributes it to the appropriate nodes in the decentralised network, and returns the results. It does not process the request on its own, so the usage is primarily as a proxy service.

### Options and configuration

The following options are available for configuring the gateway:

| Option               | Environment Variable      | Description                                                                                                    |
|----------------------|---------------------------|----------------------------------------------------------------------------------------------------------------|
| Application Name     | `DG_APPLICATION_NAME`     | The name of the application. This controls the logger and other backend features.                              |
| Access URL           | `DG_ACCESS_URL`           | The URL where the gateway is accessible publicly.                                                              |
| Service Name         | `DG_SERVICE_NAME`         | The name of the node, as seen by other nodes.                                                                  |
| Service Description  | `DG_SERVICE_DESCRIPTION`  | A brief description of the node.                                                                               |
| Logging Level        | `DG_LOGGING_LEVEL`        | The logging level for the application. Options are: DEBUG, INFO, WARNING, ERROR, CRITICAL.                     |
| EMA Factor           | `DG_EMA_FACTOR`           | The factor for the Exponential Moving Average (EMA) used in the route scoring.                                 |
| Challenge Difficulty | `DG_CHALLENGE_DIFFICULTY` | The difficulty level for the challenge used in the proof of work challenge.                                    |
| Database Driver      | `DG_DATABASE_DRIVER`      | The driver for the database used by the gateway. Options are: memory, mongodb.                                 |
| MongoDB Host         | `DG_MONGODB_HOST`         | The host for the MongoDB database. Used if `DG_DATABASE_DRIVER` is set to `mongodb`.                           |
| MongoDB Port         | `DG_MONGODB_PORT`         | The port for the MongoDB database. Used if `DG_DATABASE_DRIVER` is set to `mongodb`.                           |
| MongoDB DB Name      | `DG_MONGODB_DB_NAME`      | The name of the MongoDB database. Used if `DG_DATABASE_DRIVER` is set to `mongodb`.                            |
| Cache Driver         | `DG_CACHE_DRIVER`         | The driver for the cache used by the gateway. Options are: memory, redis.                                      |
| Redis Host           | `DG_REDIS_HOST`           | The host for the Redis cache. Used if `DG_CACHE_DRIVER` is set to `redis`.                                     |
| Redis Port           | `DG_REDIS_PORT`           | The port for the Redis cache. Used if `DG_CACHE_DRIVER` is set to `redis`.                                     |
| KMS Driver           | `DG_KMS_DRIVER`           | The driver for the Key Management Service (KMS) used by the gateway. Options are: memory, vault.               |
| Vault URL            | `DG_VAULT_URL`            | The URL for the Hashicorp Vault service. Used if `DG_KMS_DRIVER` is set to `vault`.                            |
| Vault Role ID        | `DG_VAULT_ROLE_ID`        | The role ID used to authenticate to Vault with AppRole. Used if `DG_KMS_DRIVER` is set to `vault`.             |
| Vault Secret ID      | `DG_VAULT_SECRET_ID`      | The secret ID used to authenticate to Vault with AppRole. Used if `DG_KMS_DRIVER` is set to `vault`.           |
| Vault KV Engine      | `DG_VAULT_KV_ENGINE`      | The KV engine name used in Vault for storing secrets. Used if `DG_KMS_DRIVER` is set to `vault`.               |
| Vault KV Path        | `DG_VAULT_KV_PATH`        | The root path in the KV engine where secrets are stored. Used if `DG_KMS_DRIVER` is set to `vault`.            |
| Vault Transit Engine | `DG_VAULT_TRANSIT_ENGINE` | The transit engine name used in Vault for cryptographic operations. Used if `DG_KMS_DRIVER` is set to `vault`. |

### Usage

The service exposes management REST API endpoints for configuration and operation, such as:

- Creating and managing networks
- Request to join a network, or invite a node into a network
- Manage access permissions of nodes
- Sending requests to other nodes in the network

It also has dedicated endpoints for another instance of the service to connect to it, achieving a peer-to-peer connection. After all the joining and permission, the nodes will connect to each other with WebSockets, and fall back to SSE if WebSockets are not available.

Lastly, it routes incoming requests to a specified network address, so a separate data discovery service needs to be configured to recognise the request format and process it accordingly.

For the details of the API endpoints, the request and response formats, and other operational details, please refer to the [documentations](https://decentralised-discovery-gateway.readthedocs.io/en/latest/)

## Licence and Disclaimer

All original code developed and authored by the maintainer in this repository is licensed under the **MIT Licence**, as described in the [LICENSE](LICENSE) file.

This software may depend on, incorporate, or statically link to third-party libraries and components. These external dependencies are governed by their respective licences. For the redistributed third-party components, a licence copy is included in the repository or distribution, where applicable. Please refer to those licenses and contact the respective authors or maintainers for any questions regarding upstream components. This software is not endorsed by or affiliated with any of the third-party projects or libraries used.

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

The software contains implementations of cryptographic algorithms and protocols. The use of cryptography may be subject to legal restrictions in some jurisdictions. It is the user's responsibility to ensure compliance with applicable laws and regulations regarding the use of cryptography in their jurisdiction.
