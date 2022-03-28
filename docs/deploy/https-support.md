<h1> HTTPS Support </h1>

There is a `certbot` container available when deploying `docker-compose` with `docker-compose-pro.yml` configuration file.

The Let's Encrypt service is used to issue the SSL certificate. You need to have a domain name available to set the certificate.

After cloning the Mercury repository please run the following command from Mercury directory:

```
./setup-pro.sh mydomain.com
```

The [`setup-pro.sh`](https://github.com/mljar/mercury/blob/main/setup-pro.sh) is available in the Mercury repository. It issues the SSL certificates for your domain and starts the docker containers.